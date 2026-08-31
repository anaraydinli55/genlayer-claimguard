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
            "confidence": "0",
            "verdict": "PENDING",
        }
        self.claims = json.dumps(c, sort_keys=True)

        return cid

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
    def getStats(self):
        c = json.loads(self.claims) if self.claims else {}
        total = len(c)
        verified = sum(1 for x in c.values() if x.get("status") == "verified")
        rejected = sum(1 for x in c.values() if x.get("status") == "rejected")
        return {
            "total_claims": str(total),
            "verified": str(verified),
            "rejected": str(rejected),
        }
