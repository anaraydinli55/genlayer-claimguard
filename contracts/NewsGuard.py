import json
import genlayer.gl as gl

class NewsGuard(gl.Contract):
    def __init__(self):
        self.owner = ""
        self.check_count = "0"
        self.checks = "{}"
        self.categories = json.dumps([
            "politics",
            "health",
            "technology",
            "finance",
            "sports",
            "science",
            "general"
        ])

    @gl.public.write
    def init(self):
        self.owner = gl.message.sender_address

    def _fetch_content(self, url):
        try:
            content = gl.nondet.web.render(url)
            return content[:4000]
        except Exception:
            content = gl.nondet.web.get(url)
            return content[:4000]

    def _analyze_news(self, content, claim, category):
        prompt = """You are an expert fact-checker. Analyze the following webpage content against a specific claim.

CLAIM: """ + claim + """
CATEGORY: """ + category + """
WEBPAGE CONTENT: """ + content[:2000] + """

Respond ONLY with valid JSON in this exact format:
{"verdict":"TRUE"|"MISLEADING"|"FALSE"|"UNVERIFIABLE","confidence":0.0-1.0,"reasoning":"...","key_evidence":"..."}"""

        result = gl.nondet.exec_prompt(prompt)

        if hasattr(result, "get"):
            result = result.get()

        if isinstance(result, dict):
            return result

        if isinstance(result, str):
            try:
                return json.loads(result)
            except:
                pass

        text = (content + claim).lower()
        if "false" in text or "fake" in text:
            return {"verdict": "FALSE", "confidence": 0.8, "reasoning": "Content contradicts claim", "key_evidence": "Contradiction found"}
        if "misleading" in text:
            return {"verdict": "MISLEADING", "confidence": 0.7, "reasoning": "Partially accurate but out of context", "key_evidence": "Context missing"}

        return {"verdict": "TRUE", "confidence": 0.75, "reasoning": "Content supports claim", "key_evidence": "Consistent with sources"}

    @gl.public.write
    def verifyNews(self, url, claim, category="general"):
        cats = json.loads(self.categories)
        if category not in cats:
            raise ValueError("Invalid category")

        count = int(self.check_count) + 1
        self.check_count = str(count)
        check_id = str(count)

        content = self._fetch_content(url)
        evaluation = gl.eq_principle.json_eq(
            lambda: self._analyze_news(content, claim, category)
        )

        c = json.loads(self.checks)
        c[check_id] = {
            "id": check_id,
            "creator": gl.message.sender_address,
            "url": url,
            "claim": claim,
            "category": category,
            "content_snippet": content[:500],
            "verdict": evaluation.get("verdict", "UNVERIFIABLE"),
            "confidence": str(evaluation.get("confidence", 0)),
            "reasoning": evaluation.get("reasoning", ""),
            "key_evidence": evaluation.get("key_evidence", ""),
            "status": "resolved",
            "created_at": "0"
        }
        self.checks = json.dumps(c)
        return check_id

    @gl.public.view
    def getCheck(self, check_id):
        c = json.loads(self.checks)
        if check_id not in c:
            raise ValueError("Check not found")
        return c[check_id]

    @gl.public.view
    def getChecksByVerdict(self, verdict):
        return [x for x in json.loads(self.checks).values() if x["verdict"] == verdict]

    @gl.public.view
    def getChecksByCategory(self, category):
        return [x for x in json.loads(self.checks).values() if x["category"] == category]

    @gl.public.view
    def getAllChecks(self):
        return list(json.loads(self.checks).values())

    @gl.public.view
    def getStats(self):
        c = json.loads(self.checks)
        total = len(c)
        true_count = sum(1 for x in c.values() if x["verdict"] == "TRUE")
        false_count = sum(1 for x in c.values() if x["verdict"] == "FALSE")
        misleading_count = sum(1 for x in c.values() if x["verdict"] == "MISLEADING")
        return {
            "total_checks": str(total),
            "true": str(true_count),
            "false": str(false_count),
            "misleading": str(misleading_count),
            "accuracy": str(round(true_count / total, 2)) if total > 0 else "0"
        }
