# { "Depends": "py-genlayer:15qfivjvy80800rh998pcxmd2m8va1wq2qzqhz850n8ggcr4i9q0" }
from genlayer import *
import json

class ClaimGuard(gl.Contract):
    owner: str = ""
    claim_count: str = "0"
    claims: str = "{}"

    def __init__(self):
        self.owner = str(gl.message.sender_address)
        self.claim_count = "0"
        self.claims = "{}"

    @gl.public.view
    def getOwner(self):
        return self.owner

    @gl.public.write
    def createClaim(self, evidence_url, expected_content, description, category):
        valid_cats = ["prediction_market", "bounty_verification", "content_moderation", "identity_verification", "fact_check", "custom"]
        if category not in valid_cats:
            raise ValueError("Invalid category")
        count = int(self.claim_count) + 1
        self.claim_count = str(count)
        cid = str(count)
        c = json.loads(self.claims) if self.claims else {}
        c[cid] = {
            "id": cid,
            "creator": str(gl.message.sender_address),
            "evidence_url": evidence_url,
            "expected_content": expected_content,
            "description": description,
            "category": category,
            "status": "pending",
            "votes_for": "0",
            "votes_against": "0",
            "appeal_count": "0",
            "reasoning": "",
            "confidence": "0",
            "verdict": "PENDING",
            "evidence_summary": ""
        }
        self.claims = json.dumps(c, sort_keys=True)
        return cid

    @gl.public.write
    def resolveClaim(self, claim_id, verdict, confidence_pct, reasoning, evidence_summary):
        if str(gl.message.sender_address) != self.owner:
            raise ValueError("Only owner can resolve")
        v = str(verdict).upper().strip()
        if v not in ["VERIFIED", "REJECTED", "INCONCLUSIVE"]:
            raise ValueError("Invalid verdict")
        c = json.loads(self.claims) if self.claims else {}
        cid = str(claim_id)
        if cid not in c:
            raise ValueError("Claim not found")
        claim = c[cid]
        if claim["status"] != "pending":
            raise ValueError("Claim is already resolved")
        conf_pct = int(confidence_pct)
        if not (0 <= conf_pct <= 100):
            raise ValueError("Invalid confidence percentage (0-100)")
        conf = conf_pct / 100.0
        if conf < 0.7:
            v = "INCONCLUSIVE"
            if not reasoning:
                reasoning = "Low confidence threshold not met."
        if v == "VERIFIED":
            claim["status"] = "verified"
            claim["votes_for"] = "1"
        elif v == "REJECTED":
            claim["status"] = "rejected"
            claim["votes_against"] = "1"
        else:
            claim["status"] = "inconclusive"
        claim["reasoning"] = str(reasoning)
        claim["confidence"] = str(conf)
        claim["verdict"] = v
        claim["evidence_summary"] = str(evidence_summary)
        c[cid] = claim
        self.claims = json.dumps(c, sort_keys=True)
        return claim["status"]

    @gl.public.write
    def appealClaim(self, claim_id, new_evidence_url):
        new_url = str(new_evidence_url).strip()
        if not new_url:
            raise ValueError("Replacement evidence URL is required for appeal")
        c = json.loads(self.claims) if self.claims else {}
        cid = str(claim_id)
        if cid not in c:
            raise ValueError("Claim not found")
        claim = c[cid]
        if str(gl.message.sender_address) != claim["creator"]:
            raise ValueError("Only the claim creator can appeal")
        if claim["status"] == "pending":
            raise ValueError("Claim is still pending")
        appeal_count = int(claim["appeal_count"])
        if appeal_count >= 3:
            raise ValueError("Maximum appeal count reached")
        appeal_count += 1
        claim["appeal_count"] = str(appeal_count)
        claim["evidence_url"] = new_url
        claim["status"] = "pending"
        claim["confidence"] = "0"
        claim["verdict"] = "PENDING"
        claim["reasoning"] = ""
        claim["evidence_summary"] = ""
        claim["votes_for"] = "0"
        claim["votes_against"] = "0"
        c[cid] = claim
        self.claims = json.dumps(c, sort_keys=True)
        return "Appeal #" + str(appeal_count) + " submitted successfully"

    @gl.public.view
    def getClaim(self, claim_id):
        c = json.loads(self.claims) if self.claims else {}
        cid = str(claim_id)
        if cid not in c:
            raise ValueError("Claim not found")
        return c[cid]

    @gl.public.view
    def getAllClaims(self):
        return list(json.loads(self.claims).values()) if self.claims else []

    @gl.public.view
    def getClaimsByStatus(self, status):
        c = json.loads(self.claims) if self.claims else {}
        return [x for x in c.values() if x["status"] == status]

    @gl.public.view
    def getClaimsByCategory(self, category):
        c = json.loads(self.claims) if self.claims else {}
        return [x for x in c.values() if x["category"] == category]

    @gl.public.view
    def getStats(self):
        c = json.loads(self.claims) if self.claims else {}
        total = len(c)
        verified = sum(1 for x in c.values() if x["status"] == "verified")
        rejected = sum(1 for x in c.values() if x["status"] == "rejected")
        inconclusive = sum(1 for x in c.values() if x["status"] == "inconclusive")
        return {
            "total_claims": str(total),
            "verified": str(verified),
            "rejected": str(rejected),
            "inconclusive": str(inconclusive),
            "success_rate": str(float(verified / total)) if total > 0 else "0"
        }
