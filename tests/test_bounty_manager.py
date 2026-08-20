"""
BountyManager Direct Mode Tests
"""

import pytest

class TestBountyManagerDirect:
    def test_create_bounty(self, direct_vm, direct_deploy):
        """Test bounty creation with ClaimGuard integration"""
        # Deploy ClaimGuard first
        claim_guard = direct_deploy("contracts/ClaimGuard.py")
        import genlayer.gl.genvm_contracts as _gvm
        _gvm.__known_contract__ = None
        claim_guard.init()

        # Deploy BountyManager with ClaimGuard address
        bounty_mgr = direct_deploy("contracts/BountyManager.py", claim_guard.address)
        bounty_mgr.init()

        # Mock ClaimGuard createClaim response

        bid = bounty_mgr.createBounty(
            "Build a website",
            "Create a landing page",
            1000,
            "https://github.com/user/repo",
            "Landing page deployed"
        )

        assert bid == 1
        bounty = bounty_mgr.getBounty(bid)
        assert bounty["title"] == "Build a website"
        assert bounty["status"] == "open"
        assert bounty["reward_amount"] == 1000

    def test_submit_work(self, direct_vm, direct_deploy, direct_alice):
        """Test work submission flow"""
        claim_guard = direct_deploy("contracts/ClaimGuard.py")
        import genlayer.gl.genvm_contracts as _gvm
        _gvm.__known_contract__ = None
        claim_guard.init()

        bounty_mgr = direct_deploy("contracts/BountyManager.py", claim_guard.address)
        bounty_mgr.init()

        bid = bounty_mgr.createBounty("Task", "Desc", 500, "https://a.com", "evidence")

        # Worker submits proof
        with direct_vm.prank(direct_alice):
            result = bounty_mgr.submitWork(bid, "https://proof.com")
            assert "Awaiting verification" in result

        bounty = bounty_mgr.getBounty(bid)
        assert bounty["status"] == "in_progress"
        assert str(bounty["assignee"]).lower() == "0x" + direct_alice.hex().lower()

    def test_verify_and_release(self, direct_vm, direct_deploy, direct_alice):
        """Test verification and reward release"""
        claim_guard = direct_deploy("contracts/ClaimGuard.py")
        import genlayer.gl.genvm_contracts as _gvm
        _gvm.__known_contract__ = None
        claim_guard.init()

        bounty_mgr = direct_deploy("contracts/BountyManager.py", claim_guard.address)
        bounty_mgr.init()

        bid = bounty_mgr.createBounty("Task", "Desc", 1000, "https://a.com", "evidence")

        with direct_vm.prank(direct_alice):
            bounty_mgr.submitWork(bid, "https://proof.com")

        # Mock ClaimGuard resolve as verified
    
        result = bounty_mgr.verifyAndRelease(bid)
        assert "verified and completed" in result

        bounty = bounty_mgr.getBounty(bid)
        assert bounty["status"] == "completed"

    def test_cancel_bounty(self, direct_vm, direct_deploy):
        """Test bounty cancellation by creator"""
        claim_guard = direct_deploy("contracts/ClaimGuard.py")
        import genlayer.gl.genvm_contracts as _gvm
        _gvm.__known_contract__ = None
        claim_guard.init()

        bounty_mgr = direct_deploy("contracts/BountyManager.py", claim_guard.address)
        bounty_mgr.init()

        bid = bounty_mgr.createBounty("Task", "Desc", 500, "https://a.com", "evidence")

        result = bounty_mgr.cancelBounty(bid)
        assert "cancelled" in result
        assert bounty_mgr.getBounty(bid)["status"] == "cancelled"

    def test_platform_stats(self, direct_vm, direct_deploy):
        """Test platform statistics"""
        claim_guard = direct_deploy("contracts/ClaimGuard.py")
        import genlayer.gl.genvm_contracts as _gvm
        _gvm.__known_contract__ = None
        claim_guard.init()

        bounty_mgr = direct_deploy("contracts/BountyManager.py", claim_guard.address)
        bounty_mgr.init()


        for i in range(3):
            bounty_mgr.createBounty(f"Task {i}", "Desc", 500, f"https://site{i}.com", "evidence")

        stats = bounty_mgr.getStats()
        assert stats["total_bounties"] == 3
        assert stats["open"] == 3
