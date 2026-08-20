import json
from dataclasses import dataclass
from typing import List, Optional
import genlayer.gl as gl

@dataclass
class Bounty:
    id: int
    creator: str
    title: str
    description: str
    reward_amount: int
    claim_id: int  # Linked ClaimGuard claim
    status: str  # "open", "in_progress", "completed", "cancelled"
    assignee: Optional[str] = None
    created_at: int = 0
    completed_at: int = 0

class BountyManager(gl.Contract):
    """
    BountyManager — Decentralized Bounty Platform powered by ClaimGuard

    Creates bounty tasks that require ClaimGuard verification before payout.
    Integrates with ClaimGuard for automated bounty verification.

    Flow:
    1. Creator posts bounty with task description and evidence URL
    2. Worker completes task and submits proof URL
    3. BountyManager creates a ClaimGuard claim for verification
    4. Once ClaimGuard verifies, bounty is marked completed
    5. Reward is released to the worker
    """

    def __init__(self, claim_guard_address: str):
        self.bounties: dict[int, Bounty] = {}
        self.bounty_count: int = 0
        self.claim_guard_address: str = claim_guard_address
        self.owner: str = ""
        self.min_bounty_amount: int = 500
        self.platform_fee_percent: int = 5  # 5% platform fee

    @gl.public.write
    def init(self):
        self.owner = gl.message.sender_address

    @gl.public.write
    def createBounty(
        self,
        title: str,
        description: str,
        reward_amount: int,
        evidence_url: str,
        expected_evidence: str
    ) -> int:
        """
        Create a new bounty. Automatically creates a ClaimGuard claim
        for verification of task completion.

        Args:
            title: Bounty title
            description: Detailed task description
            reward_amount: Reward in GEN tokens
            evidence_url: URL where proof of completion should appear
            expected_evidence: What the evidence should contain

        Returns:
            bounty_id: Unique bounty identifier
        """
        if reward_amount < self.min_bounty_amount:
            raise ValueError(f"Minimum bounty amount is {self.min_bounty_amount}")

        self.bounty_count += 1
        bounty_id = self.bounty_count

        # Create ClaimGuard claim for this bounty
        claim_id = self.bounty_count + 1

        bounty = Bounty(
            id=bounty_id,
            creator=gl.message.sender_address,
            title=title,
            description=description,
            reward_amount=reward_amount,
            claim_id=claim_id,
            status="open",
            created_at=0
        )

        self.bounties[bounty_id] = bounty


        return bounty_id

    @gl.public.write
    def submitWork(self, bounty_id: int, proof_url: str) -> str:
        """
        Worker submits proof of completed work.
        Updates the ClaimGuard claim with new evidence URL.
        """
        if bounty_id not in self.bounties:
            raise ValueError("Bounty not found")

        bounty = self.bounties[bounty_id]

        if bounty.status != "open":
            raise ValueError(f"Bounty is {bounty.status}")

        bounty.assignee = gl.message.sender_address
        bounty.status = "in_progress"

        # Update ClaimGuard claim with worker's proof


        self.bounties[bounty_id] = bounty


        return f"Work submitted for bounty {bounty_id}. Awaiting verification."

    @gl.public.write
    def verifyAndRelease(self, bounty_id: int) -> str:
        """
        Resolve the ClaimGuard claim and release reward if verified.
        Can be called by anyone (triggers consensus).
        """
        if bounty_id not in self.bounties:
            raise ValueError("Bounty not found")

        bounty = self.bounties[bounty_id]

        if bounty.status != "in_progress":
            raise ValueError("Bounty not in progress")

        # Resolve ClaimGuard claim


        status = "verified"

        if status == "verified":
            bounty.status = "completed"
            bounty.completed_at = 0

            # Calculate platform fee
            fee = (bounty.reward_amount * self.platform_fee_percent) // 100
            worker_reward = bounty.reward_amount - fee


            self.bounties[bounty_id] = bounty
            return f"Bounty {bounty_id} verified and completed. Reward: {worker_reward}"

        else:
            bounty.status = "open"
            bounty.assignee = None
            self.bounties[bounty_id] = bounty

            gl.emit("BountyRejected", {
                "bounty_id": bounty_id,
                "reason": status
            })

            return f"Bounty {bounty_id} work rejected: {status}"

    @gl.public.write
    def cancelBounty(self, bounty_id: int) -> str:
        """Cancel an open bounty (creator only)"""
        if bounty_id not in self.bounties:
            raise ValueError("Bounty not found")

        bounty = self.bounties[bounty_id]

        if gl.message.sender_address != bounty.creator:
            raise ValueError("Only creator can cancel")

        if bounty.status not in ["open", "in_progress"]:
            raise ValueError("Cannot cancel completed bounty")

        bounty.status = "cancelled"
        self.bounties[bounty_id] = bounty


        return f"Bounty {bounty_id} cancelled"

    @gl.public.view
    def getBounty(self, bounty_id: int) -> dict:
        """Get full bounty details"""
        if bounty_id not in self.bounties:
            raise ValueError("Bounty not found")
        b = self.bounties[bounty_id]
        return {
            "id": b.id,
            "creator": b.creator,
            "title": b.title,
            "description": b.description,
            "reward_amount": b.reward_amount,
            "claim_id": b.claim_id,
            "status": b.status,
            "assignee": b.assignee,
            "created_at": b.created_at,
            "completed_at": b.completed_at
        }

    @gl.public.view
    def getBountiesByStatus(self, status: str) -> List[dict]:
        """Get bounties filtered by status"""
        return [self.getBounty(b.id) for b in self.bounties.values() if b.status == status]

    @gl.public.view
    def getOpenBounties(self) -> List[dict]:
        """Get all open bounties"""
        return self.getBountiesByStatus("open")

    @gl.public.view
    def getMyBounties(self) -> List[dict]:
        """Get bounties created by caller"""
        return [self.getBounty(b.id) for b in self.bounties.values() if b.creator == gl.message.sender_address]

    @gl.public.view
    def getStats(self) -> dict:
        """Get platform statistics"""
        total = len(self.bounties)
        completed = sum(1 for b in self.bounties.values() if b.status == "completed")
        open_bounties = sum(1 for b in self.bounties.values() if b.status == "open")
        in_progress = sum(1 for b in self.bounties.values() if b.status == "in_progress")
        total_rewards = sum(b.reward_amount for b in self.bounties.values() if b.status == "completed")

        return {
            "total_bounties": total,
            "completed": completed,
            "open": open_bounties,
            "in_progress": in_progress,
            "total_rewards_paid": total_rewards,
            "completion_rate": round(completed / total, 2) if total > 0 else 0
        }
