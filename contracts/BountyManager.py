import json
import genlayer.gl as gl

class BountyManager(gl.Contract):
    def __init__(self, claim_guard_address):
        self.claim_guard_address = claim_guard_address
        self.bounty_count = "0"
        self.bounties = "{}"
        self.owner = ""
        self.min_bounty_amount = "500"

    @gl.public.write
    def init(self):
        self.owner = gl.message.sender_address

    @gl.public.write
    def createBounty(self, title, description, reward_amount, evidence_url, expected_evidence):
        if int(reward_amount) < int(self.min_bounty_amount):
            raise ValueError("Minimum bounty amount is " + self.min_bounty_amount)

        count = int(self.bounty_count) + 1
        self.bounty_count = str(count)
        bid = str(count)

        b = json.loads(self.bounties)
        b[bid] = {
            "id": bid,
            "creator": gl.message.sender_address,
            "title": title,
            "description": description,
            "reward_amount": reward_amount,
            "claim_id": bid,
            "status": "open",
            "assignee": "",
            "created_at": "0",
            "completed_at": "0"
        }
        self.bounties = json.dumps(b)
        return bid

    @gl.public.write
    def submitWork(self, bounty_id, proof_url):
        b = json.loads(self.bounties)
        if bounty_id not in b:
            raise ValueError("Bounty not found")
        bounty = b[bounty_id]
        if bounty["status"] != "open":
            raise ValueError("Bounty is " + bounty["status"])
        bounty["assignee"] = gl.message.sender_address
        bounty["status"] = "in_progress"
        b[bounty_id] = bounty
        self.bounties = json.dumps(b)
        return "Work submitted for bounty " + bounty_id

    @gl.public.write
    def verifyAndRelease(self, bounty_id):
        b = json.loads(self.bounties)
        if bounty_id not in b:
            raise ValueError("Bounty not found")
        bounty = b[bounty_id]
        if bounty["status"] != "in_progress":
            raise ValueError("Bounty not in progress")
        bounty["status"] = "completed"
        bounty["completed_at"] = "0"
        b[bounty_id] = bounty
        self.bounties = json.dumps(b)
        return "Bounty " + bounty_id + " verified and completed"

    @gl.public.write
    def cancelBounty(self, bounty_id):
        b = json.loads(self.bounties)
        if bounty_id not in b:
            raise ValueError("Bounty not found")
        bounty = b[bounty_id]
        if gl.message.sender_address != bounty["creator"]:
            raise ValueError("Only creator can cancel")
        if bounty["status"] not in ["open", "in_progress"]:
            raise ValueError("Cannot cancel completed bounty")
        bounty["status"] = "cancelled"
        b[bounty_id] = bounty
        self.bounties = json.dumps(b)
        return "Bounty " + bounty_id + " cancelled"

    @gl.public.view
    def getBounty(self, bounty_id):
        b = json.loads(self.bounties)
        if bounty_id not in b:
            raise ValueError("Bounty not found")
        return b[bounty_id]

    @gl.public.view
    def getBountiesByStatus(self, status):
        return [x for x in json.loads(self.bounties).values() if x["status"] == status]

    @gl.public.view
    def getOpenBounties(self):
        return self.getBountiesByStatus("open")

    @gl.public.view
    def getStats(self):
        b = json.loads(self.bounties)
        total = len(b)
        completed = sum(1 for x in b.values() if x["status"] == "completed")
        open_b = sum(1 for x in b.values() if x["status"] == "open")
        return {
            "total_bounties": str(total),
            "completed": str(completed),
            "open": str(open_b)
        }
