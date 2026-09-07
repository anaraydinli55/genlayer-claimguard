# { "Depends": "py-genlayer:latest" }
from genlayer import *
import json

def _extract_json(s: str) -> str:
    start = s.find("{")
    end = s.rfind("}")
    if start != -1 and end != -1 and start < end:
        return s[start:end + 1]
    return ""

class ClaimGuard(gl.Contract):
    owner: str
    claims: TreeMap[str, str]
    resolvers: TreeMap[str, bool]
    CATEGORIES: DynArray[str]
    min_stake: u256

    def __init__(self):
        self.owner = ""
        self.claims = TreeMap()
        self.resolvers = TreeMap()
        self.CATEGORIES = DynArray([
            "prediction_market", "bounty_verification", "content_moderation",
            "identity_verification", "fact_check", "custom"
        ])
        self.min_stake = u256(100)

    @gl.public.write
    def init(self) -> None:
        if self.owner != "":
            raise gl.vm.UserError("Already initialized")
        self.owner = str(gl.message.sender_address)
        self.resolvers[str(gl.message.sender_address)] = True

    @gl.public.write
    def createClaim(self, evidence_url: str, expected_content: str, description: str, category: str) -> str:
        if category not in list(self.CATEGORIES):
            raise gl.vm.UserError("Invalid category")
        count = len(self.claims) + 1
        cid = str(count)
        claim = {
            "id": cid,
            "creator": str(gl.message.sender_address),
            "evidence_url": evidence_url,
            "expected_content": expected_content,
            "description": description,
            "category": category,
            "status": "pending",
            "votes_for": 0,
            "votes_against": 0,
            "appeal_count": 0,
            "resolution": json.dumps({
                "verdict": "PENDING",
                "confidence": 0.0,
                "reasoning": "",
                "evidence_summary": ""
            })
        }
        self.claims[cid] = json.dumps(claim, sort_keys=True)
        gl.emit("ClaimCreated", {"claim_id": cid, "creator": claim["creator"], "category": category})
        return cid

    @gl.public.write
    def resolveClaim(self, claim_id: str) -> str:
        if not self.resolvers.get(str(gl.message.sender_address), False):
            raise gl.vm.UserError("Not an approved resolver")

        cid = str(claim_id)
        if cid not in self.claims:
            raise gl.vm.UserError("Claim not found")

        claim = json.loads(self.claims[cid])
        if claim["status"] != "pending":
            raise gl.vm.UserError("Claim is already resolved")

        evidence_url = claim["evidence_url"]
        expected_content = claim["expected_content"]
        description = claim["description"]

        def non_det():
            try:
                web_data = gl.nondet.web.render(evidence_url, mode="text")
            except Exception:
                web_data = ""

            prompt = f"""You are a claim verification evaluator. Analyze the following evidence and determine if the claim is verified.

Claim Description: {description}
Expected Content: {expected_content}
Evidence URL: {evidence_url}
Evidence Content: {web_data}

Evaluate whether the evidence supports the claim. Return ONLY a JSON object with this exact structure:
{{
    "verdict": "VERIFIED" | "REJECTED" | "INCONCLUSIVE",
    "confidence": float (0.0 to 1.0),
    "reasoning": "string explaining the evaluation",
    "evidence_summary": "string summarizing what was found in the evidence"
}}

It is mandatory that you respond only using the JSON format above, nothing else. Do not include any other words or characters, your output must be only JSON without any formatting prefix or suffix. This result should be perfectly parsable by a JSON parser without errors."""

            result = gl.nondet.exec_prompt(prompt)
            json_str = _extract_json(result)
            if not json_str:
                return json.dumps({
                    "verdict": "INCONCLUSIVE",
                    "confidence": 0.0,
                    "reasoning": "Failed to parse LLM response",
                    "evidence_summary": ""
                }, sort_keys=True)

            try:
                parsed = json.loads(json_str)
            except json.JSONDecodeError:
                return json.dumps({
                    "verdict": "INCONCLUSIVE",
                    "confidence": 0.0,
                    "reasoning": "Failed to parse LLM response",
                    "evidence_summary": ""
                }, sort_keys=True)

            verdict = str(parsed.get("verdict", "INCONCLUSIVE")).upper().strip()
            if verdict not in ["VERIFIED", "REJECTED", "INCONCLUSIVE"]:
                verdict = "INCONCLUSIVE"

            confidence = float(parsed.get("confidence", 0.0))
            if not (0.0 <= confidence <= 1.0):
                confidence = 0.0

            if confidence < 0.7 and verdict == "VERIFIED":
                verdict = "INCONCLUSIVE"
                reasoning = "Low confidence threshold not met."
            else:
                reasoning = str(parsed.get("reasoning", ""))

            normalized = {
                "verdict": verdict,
                "confidence": confidence,
                "reasoning": reasoning,
                "evidence_summary": str(parsed.get("evidence_summary", ""))
            }
            return json.dumps(normalized, sort_keys=True)

        result_str = gl.eq_principle.strict_eq(non_det)
        result_json = json.loads(result_str)

        verdict = result_json["verdict"]
        confidence = result_json["confidence"]
        reasoning = result_json["reasoning"]
        evidence_summary = result_json["evidence_summary"]

        if verdict == "VERIFIED":
            claim["status"] = "verified"
            claim["votes_for"] = 1
        elif verdict == "REJECTED":
            claim["status"] = "rejected"
            claim["votes_against"] = 1
        else:
            claim["status"] = "inconclusive"

        claim["resolution"] = json.dumps({
            "verdict": verdict,
            "confidence": confidence,
            "reasoning": reasoning,
            "evidence_summary": evidence_summary
        }, sort_keys=True)

        self.claims[cid] = json.dumps(claim, sort_keys=True)
        gl.emit("ClaimResolved", {"claim_id": cid, "verdict": verdict, "confidence": str(confidence)})
        return claim["status"]

    @gl.public.write
    def appealClaim(self, claim_id: str, new_evidence_url: str) -> str:
        cid = str(claim_id)
        if cid not in self.claims:
            raise gl.vm.UserError("Claim not found")

        claim = json.loads(self.claims[cid])
        if str(gl.message.sender_address) != claim["creator"]:
            raise gl.vm.UserError("Only the claim creator can appeal")

        if claim["status"] == "pending":
            raise gl.vm.UserError("Claim is still pending")

        if claim["appeal_count"] >= 3:
            raise gl.vm.UserError("Maximum appeal count reached")

        new_url = str(new_evidence_url).strip()
        if not new_url:
            raise gl.vm.UserError("Replacement evidence URL is required for appeal")

        claim["evidence_url"] = new_url
        claim["appeal_count"] += 1
        claim["status"] = "pending"
        claim["votes_for"] = 0
        claim["votes_against"] = 0
        claim["resolution"] = json.dumps({
            "verdict": "PENDING",
            "confidence": 0.0,
            "reasoning": "",
            "evidence_summary": ""
        }, sort_keys=True)

        self.claims[cid] = json.dumps(claim, sort_keys=True)
        gl.emit("ClaimAppealed", {"claim_id": cid, "appeal_count": str(claim["appeal_count"])})
        return f"Appeal #{claim['appeal_count']} submitted successfully"

    @gl.public.write
    def addResolver(self, address: str) -> None:
        if str(gl.message.sender_address) != self.owner:
            raise gl.vm.UserError("Only owner can add resolvers")
        self.resolvers[address] = True

    @gl.public.write
    def removeResolver(self, address: str) -> None:
        if str(gl.message.sender_address) != self.owner:
            raise gl.vm.UserError("Only owner can remove resolvers")
        if address in self.resolvers:
            self.resolvers[address] = False

    @gl.public.view
    def getOwner(self) -> str:
        return self.owner

    @gl.public.view
    def getResolvers(self) -> dict:
        return {k: v for k, v in self.resolvers.items()}

    @gl.public.view
    def getClaim(self, claim_id: str) -> dict:
        cid = str(claim_id)
        if cid not in self.claims:
            raise gl.vm.UserError("Claim not found")
        return json.loads(self.claims[cid])

    @gl.public.view
    def getAllClaims(self) -> list:
        return [json.loads(v) for v in self.claims.values()]

    @gl.public.view
    def getClaimsByStatus(self, status: str) -> list:
        return [json.loads(v) for v in self.claims.values() if json.loads(v)["status"] == status]

    @gl.public.view
    def getClaimsByCategory(self, category: str) -> list:
        return [json.loads(v) for v in self.claims.values() if json.loads(v)["category"] == category]

    @gl.public.view
    def getStats(self) -> dict:
        total = len(self.claims)
        if total == 0:
            return {
                "total_claims": "0",
                "verified": "0",
                "rejected": "0",
                "inconclusive": "0",
                "success_rate": "0.0"
            }
        verified = sum(1 for v in self.claims.values() if json.loads(v)["status"] == "verified")
        rejected = sum(1 for v in self.claims.values() if json.loads(v)["status"] == "rejected")
        inconclusive = sum(1 for v in self.claims.values() if json.loads(v)["status"] == "inconclusive")
        return {
            "total_claims": str(total),
            "verified": str(verified),
            "rejected": str(rejected),
            "inconclusive": str(inconclusive),
            "success_rate": str(float(verified) / float(total))
        }
