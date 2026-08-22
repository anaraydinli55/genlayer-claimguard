"""
ClaimGuard Integration Tests
Tests against real GenLayer Studio/Localnet
"""

import pytest
from gltest.contracts import ContractFactory


class TestClaimGuardIntegration:
    """Integration tests with real LLM and web calls"""

    def test_deploy_init_create(self):
        """Deploy, init, and create a claim"""
        factory = ContractFactory.from_file_path("ClaimGuard.py")
        contract = factory.deploy()
        contract.init()

        cid = contract.createClaim(
            "https://example.com",
            "test content",
            "integration test claim",
            "fact_check"
        )
        assert cid == "1"

        claim = contract.getClaim(cid)
        assert claim["status"] == "pending"
        assert claim["category"] == "fact_check"

    def test_resolve_claim(self):
        """Create and resolve a claim with real LLM"""
        factory = ContractFactory.from_file_path("ClaimGuard.py")
        contract = factory.deploy()
        contract.init()

        cid = contract.createClaim(
            "https://bbc.com",
            "BBC",
            "BBC news website",
            "fact_check"
        )

        # Resolve with real web + LLM
        status = contract.resolveClaim(cid)
        assert status in ["verified", "rejected", "inconclusive"]

        claim = contract.getClaim(cid)
        assert claim["status"] == status
        assert claim["status"] != "pending"

    def test_appeal_flow(self):
        """Full lifecycle: create → resolve → appeal → resolve"""
        factory = ContractFactory.from_file_path("ClaimGuard.py")
        contract = factory.deploy()
        contract.init()

        cid = contract.createClaim(
            "https://example.com",
            "test",
            "appeal test",
            "fact_check"
        )

        # First resolve
        status1 = contract.resolveClaim(cid)
        assert status1 in ["verified", "rejected", "inconclusive"]

        # Appeal
        result = contract.appealClaim(cid)
        assert "Appeal" in result

        # Check status reset to pending
        claim = contract.getClaim(cid)
        assert claim["status"] == "pending"
        assert claim["appeal_count"] == 1

    def test_category_filtering(self):
        """Test getClaimsByCategory with real data"""
        factory = ContractFactory.from_file_path("ClaimGuard.py")
        contract = factory.deploy()
        contract.init()

        contract.createClaim("https://a.com", "x", "x", "prediction_market")
        contract.createClaim("https://b.com", "x", "x", "bounty_verification")

        pm = contract.getClaimsByCategory("prediction_market")
        bv = contract.getClaimsByCategory("bounty_verification")

        assert len(pm) == 1
        assert len(bv) == 1

    def test_stats(self):
        """Test getStats after operations"""
        factory = ContractFactory.from_file_path("ClaimGuard.py")
        contract = factory.deploy()
        contract.init()

        stats = contract.getStats()
        assert stats["total_claims"] == "0"

        contract.createClaim("https://x.com", "x", "x", "fact_check")
        stats = contract.getStats()
        assert stats["total_claims"] == "1"
