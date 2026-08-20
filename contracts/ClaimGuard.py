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
        self.owner = gl.message.sender_address
        r = json.loads(self.resolvers)
        r[gl.message.sender_address] = True
        self.resolvers = json.dumps(r)

    @gl.public.write
    def createClaim(self, url, expected_content, description, category="custom"):
        count = int(self.claim_count) + 1
        self.claim_count = str(count)
        cid = str(count)
        c = json.loads(self.claims)
        c[cid] = {
            "id": cid, "creator": gl.message.sender_address,
            "url": url, "expected_content": expected_content,
            "description": description, "category": category,
            "status": "pending", "resolution": "",
            "evidence": "", "appeal_count": "0"
        }
        self.claims = json.dumps(c)
        return cid

    @gl.public.view
    def getClaim(self, claim_id):
        c = json.loads(self.claims)
        if claim_id not in c:
            raise ValueError("Claim not found")
        return c[claim_id]

    @gl.public.view
    def getAllClaims(self):
        return list(json.loads(self.claims).values())

    @gl.public.view
    def getStats(self):
        c = json.loads(self.claims)
        total = len(c)
        verified = sum(1 for x in c.values() if x["status"] == "verified")
        return {"total": str(total), "verified": str(verified)}
