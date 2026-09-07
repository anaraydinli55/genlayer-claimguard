# { "Depends": "py-genlayer:latest" }
from genlayer import *
import json

class NewsGuard(gl.Contract):
    owner: str
    check_count: str
    checks: str

    def __init__(self):
        self.owner = ""
        self.check_count = "0"
        self.checks = "{}"

    @gl.public.write
    def init(self) -> None:
        self.owner = str(gl.message.sender_address)

    @gl.public.view
    def getOwner(self) -> str:
        return self.owner

    @gl.public.write
    def verifyNews(self, url: str, claim: str, category: str = "general") -> str:
        cats = ["politics", "health", "technology", "finance", "sports", "science", "general"]
        if category not in cats:
            raise gl.vm.UserError("Invalid category")

        def evaluate_consensus():
            try:
                web_data = gl.nondet.web.render(url, mode="text")
            except Exception:
                web_data = ""

            prompt = f"Analyze: {claim}\nURL: {url}\nContent: {web_data}\nRespond with raw JSON: {{\"verdict\":\"TRUE\",\"confidence\":0.9,\"reasoning\":\"verified\",\"key_evidence\":\"summary\"}}"
            result = gl.nondet.exec_prompt(prompt)
            
            try:
                s = result.find("{")
                e = result.rfind("}")
                parsed = json.loads(result[s:e+1]) if (s != -1 and e != -1) else {}
            except Exception:
                parsed = {}

            verdict = str(parsed.get("verdict", "UNVERIFIABLE")).upper().strip()
            confidence = float(parsed.get("confidence", 0.0))
            return json.dumps({
                "verdict": verdict,
                "confidence": confidence,
                "reasoning": str(parsed.get("reasoning", "")),
                "key_evidence": str(parsed.get("key_evidence", ""))
            }, sort_keys=True)

        res_str = gl.eq_principle.strict_eq(evaluate_consensus)
        res = json.loads(res_str)

        count = int(self.check_count) + 1
        self.check_count = str(count)
        cid = str(count)

        c = json.loads(self.checks) if self.checks else {}
        c[cid] = {
            "id": cid,
            "creator": str(gl.message.sender_address),
            "url": url,
            "claim": claim,
            "category": category,
            "verdict": res["verdict"],
            "confidence": str(res["confidence"]),
            "reasoning": res["reasoning"],
            "key_evidence": res["key_evidence"],
            "status": "resolved"
        }
        self.checks = json.dumps(c, sort_keys=True)
        gl.emit("NewsVerified", {"check_id": cid, "verdict": res["verdict"]})
        return cid

    @gl.public.view
    def getCheck(self, check_id: str) -> dict:
        c = json.loads(self.checks) if self.checks else {}
        if str(check_id) not in c:
            raise gl.vm.UserError("Check not found")
        return c[str(check_id)]

    @gl.public.view
    def getAllChecks(self) -> list:
        return list(json.loads(self.checks).values()) if self.checks else []

    @gl.public.view
    def getStats(self) -> dict:
        c = json.loads(self.checks) if self.checks else {}
        total = len(c)
        return {"total_checks": str(total)}
