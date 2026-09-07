# { "Depends": "py-genlayer:latest" }
import json
import genlayer.gl as gl

class BountyManager(gl.Contract):
    def __init__(self, claim_guard_address: str = ""):
        self.claim_guard_address = claim_guard_address
        self.bounty_count = "0"
        self.bounties = "{}"
        self.owner = ""
        self.min_bounty_amount = "500"

    @gl.public.write
    def init(self) -> None:
        self.owner = str(gl.message.sender_address)

    @gl.public.write
    def createBounty(self, title: str, description: str, reward_amount: str, evidence_url: str, expected_evidence: str) -> str:
        if int(reward_amount) < int(self.min_bounty_amount):
            raise gl.vm.UserError("Minimum bounty amount is " + self.min_bounty_amount)

        count = int(self.bounty_count) + 1
        self.bounty_count = str(count)
        bid = str(count)

        b = json.loads(self.bounties) if self.bounties else {}
        b[bid] = {
            "id": bid,
            "creator": str(gl.message.sender_address),
            "title": title,
            "description": description,
            "reward_amount": reward_amount,
            "evidence_url": evidence_url,
            "expected_evidence": expected_evidence,
            "status": "open",
            "hunter": "",
            "submission_url": ""
        }
        self.bounties = json.dumps(b, sort_keys=True)
        gl.emit("BountyCreated", {"bounty_id": bid, "creator": str(gl.message.sender_address), "reward": reward_amount})
        return bid

    @gl.public.view
    def getBounty(self, bounty_id: str) -> dict:
        b = json.loads(self.bounties) if self.bounties else {}
        if str(bounty_id) not in b:
            raise gl.vm.UserError("Bounty not found")
        return b[str(bounty_id)]

    @gl.public.view
    def getBountiesByStatus(self, status: str) -> list:
        b = json.loads(self.bounties) if self.bounties else {}
        return [x for x in b.values() if x["status"] == status]

    @gl.public.view
    def getOpenBounties(self) -> list:
        return self.getBountiesByStatus("open")

    @gl.public.view
    def getStats(self) -> dict:
        b = json.loads(self.bounties) if self.bounties else {}
        total = len(b)
        open_b = sum(1 for x in b.values() if x["status"] == "open")
        return {"total_bounties": str(total), "open_bounties": str(open_b)}
