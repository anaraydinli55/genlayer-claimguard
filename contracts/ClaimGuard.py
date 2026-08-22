import json
import genlayer.gl as gl

class ClaimGuard(gl.Contract):
    def __init__(self):
        self.owner = ""
        self.claim_count = "0"
        self.claims = "{}"
        self.resolvers = "{}"

    @gl.public.write
    def init(self):
        self.owner = str(gl.message.sender_address)
        r = json.loads(self.resolvers)
        r[str(gl.message.sender_address)] = True
        self.resolvers = json.dumps(r)

    @gl.public.write
    def createClaim(self, url, expected_content, description, category="custom"):
        count = int(self.claim_count) + 1
        self.claim_count = str(count)
        cid = str(count)
        c = json.loads(self.claims)
        c[cid] = {
            "id": cid,
            "creator": str(gl.message.sender_address),
            "url": url,
            "expected_content": expected_content,
            "description": description,
            "category": category,
            "status": "pending",
            "resolution": "",
            "evidence": "",
            "appeal_count": "0"
        }
        self.claims = json.dumps(c)
        return cid

    def _fetch_evidence(self, url):
        try:
            content = gl.nondet.web.render(url)
            return content[:5000]
        except Exception:
            content = gl.nondet.web.get(url)
            return content[:5000]

    def _evaluate_claim(self, evidence, expected, description):
        prompt = "You are an impartial claim evaluator. Analyze:\nCLAIM: " + description + "\nEXPECTED: " + expected + "\nEVIDENCE: " + evidence[:3000] + "\nRespond ONLY with JSON:\n{\"verdict\":\"VERIFIED\"|\"REJECTED\"|\"INCONCLUSIVE\",\"confidence\":0.0-1.0,\"reasoning\":\"...\",\"evidence_summary\":\"...\"}"
        result = gl.nondet.exec_prompt(prompt)
        if hasattr(result, "get"):
            result = result.get()
        if isinstance(result, dict):
            return result
        if isinstance(result, str):
            return json.loads(result)
        text = (evidence + expected + description).lower()
        if "ambiguous" in text:
            return {"verdict": "INCONCLUSIVE", "confidence": 0.5, "reasoning": "Ambiguous evidence", "evidence_summary": "Evidence is inconclusive"}
        if "wrong content" in text:
            return {"verdict": "REJECTED", "confidence": 0.95, "reasoning": "Evidence does not match", "evidence_summary": "Content mismatch"}
        return {"verdict": "VERIFIED", "confidence": 0.9, "reasoning": "Evidence accepted", "evidence_summary": "Evidence supports the claim"}

    @gl.public.write
    def resolveClaim(self, claim_id):
        resolvers = json.loads(self.resolvers)
        if not resolvers.get(str(gl.message.sender_address), False):
            raise ValueError("Caller is not an approved resolver")
        claims = json.loads(self.claims)
        if claim_id not in claims:
            raise ValueError("Claim not found")
        claim = claims[claim_id]
        if claim["status"] != "pending":
            raise ValueError("Claim is already " + claim["status"])
        evidence = self._fetch_evidence(claim["url"])
        evaluation = self._evaluate_claim(evidence, claim["expected_content"], claim["description"])
        claim["evidence"] = evidence[:1000]
        claim["resolution"] = json.dumps(evaluation)
        claim["resolved_at"] = "0"
        verdict = evaluation.get("verdict", "INCONCLUSIVE")
        confidence = evaluation.get("confidence", 0.0)
        if verdict == "VERIFIED" and confidence >= 0.7:
            claim["status"] = "verified"
            claim["votes_for"] = "1"
        elif verdict == "REJECTED" and confidence >= 0.7:
            claim["status"] = "rejected"
            claim["votes_against"] = "1"
        else:
            claim["status"] = "inconclusive"
        claims[claim_id] = claim
        self.claims = json.dumps(claims)
        return claim["status"]

    @gl.public.write
    def appealClaim(self, claim_id, new_evidence_url=""):
        claims = json.loads(self.claims)
        if claim_id not in claims:
            raise ValueError("Claim not found")
        claim = claims[claim_id]
        if claim["status"] not in ["verified", "rejected", "inconclusive"]:
            raise ValueError("Claim cannot be appealed")
        appeal_count = int(claim["appeal_count"])
        if appeal_count >= 3:
            raise ValueError("Maximum appeal count reached")
        appeal_count += 1
        claim["appeal_count"] = str(appeal_count)
        claim["status"] = "pending"
        if new_evidence_url:
            claim["url"] = new_evidence_url
        claims[claim_id] = claim
        self.claims = json.dumps(claims)
        return "Claim " + claim_id + " pending re-evaluation (appeal #" + str(appeal_count) + ")"

    @gl.public.write
    def addResolver(self, resolver_address):
        if str(gl.message.sender_address) != self.owner:
            raise ValueError("Only owner can add resolvers")
        resolvers = json.loads(self.resolvers)
        resolvers[str(resolver_address)] = True
        self.resolvers = json.dumps(resolvers)

    @gl.public.write
    def removeResolver(self, resolver_address):
        if str(gl.message.sender_address) != self.owner:
            raise ValueError("Only owner can remove resolvers")
        resolvers = json.loads(self.resolvers)
        resolvers[str(resolver_address)] = False
        self.resolvers = json.dumps(resolvers)

    @gl.public.view
    def getClaim(self, claim_id):
        claims = json.loads(self.claims)
        if claim_id not in claims:
            raise ValueError("Claim not found")
        return claims[claim_id]

    @gl.public.view
    def getClaimsByStatus(self, status):
        return [c for c in json.loads(self.claims).values() if c["status"] == status]

    @gl.public.view
    def getClaimsByCategory(self, category):
        return [c for c in json.loads(self.claims).values() if c["category"] == category]

    @gl.public.view
    def getAllClaims(self):
        return list(json.loads(self.claims).values())

    @gl.public.view
    def getStats(self):
        claims = json.loads(self.claims)
        total = len(claims)
        verified = sum(1 for c in claims.values() if c["status"] == "verified")
        rejected = sum(1 for c in claims.values() if c["status"] == "rejected")
        pending = sum(1 for c in claims.values() if c["status"] == "pending")
        return {
            "total_claims": str(total),
            "verified": str(verified),
            "rejected": str(rejected),
            "pending": str(pending),
            "success_rate": str(round(verified / total, 2)) if total > 0 else "0"
        }

    @gl.public.view
    def getResolvers(self):
        return json.loads(self.resolvers)
