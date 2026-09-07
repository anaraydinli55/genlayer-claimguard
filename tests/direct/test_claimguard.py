import pytest
import json

def test_init(direct_deploy, direct_owner, direct_vm):
    cg = direct_deploy("contracts/ClaimGuard.py")
    with direct_vm.prank(direct_owner):
        cg.init()
    assert cg.owner == str(direct_owner)
    resolvers = cg.getResolvers()
    assert resolvers[str(direct_owner)] is True

def test_init_twice_reverts(direct_deploy, direct_owner, direct_vm):
    cg = direct_deploy("contracts/ClaimGuard.py")
    with direct_vm.prank(direct_owner):
        cg.init()
        with direct_vm.expect_revert("Already initialized"):
            cg.init()

def test_create_claim(direct_deploy, direct_owner, direct_vm):
    cg = direct_deploy("contracts/ClaimGuard.py")
    with direct_vm.prank(direct_owner):
        cg.init()
        cid = cg.createClaim("https://example.com", "Test content", "Verify this", "fact_check")
    assert cid == "1"
    claim = cg.getClaim("1")
    assert claim["status"] == "pending"
    assert claim["category"] == "fact_check"
    assert claim["evidence_url"] == "https://example.com"
    assert claim["id"] == "1"
    assert "resolution" in claim

def test_create_claim_invalid_category(direct_deploy, direct_owner, direct_vm):
    cg = direct_deploy("contracts/ClaimGuard.py")
    with direct_vm.prank(direct_owner):
        cg.init()
        with direct_vm.expect_revert("Invalid category"):
            cg.createClaim("https://x.com", "x", "x", "nonexistent")

def test_resolve_claim_verified(direct_deploy, direct_owner, direct_vm):
    cg = direct_deploy("contracts/ClaimGuard.py")
    with direct_vm.prank(direct_owner):
        cg.init()
        cid = cg.createClaim("https://example.com", "Test", "Verify", "fact_check")

    direct_vm.mock_web(r".*", {"status": 200, "body": "Test content found here"})
    direct_vm.mock_llm(r".*", '{"verdict":"VERIFIED","confidence":0.85,"reasoning":"Content matches","evidence_summary":"Found"}')

    with direct_vm.prank(direct_owner):
        status = cg.resolveClaim(cid)
    assert status == "verified"
    claim = cg.getClaim(cid)
    assert claim["status"] == "verified"
    assert claim["votes_for"] == 1
    resolution = json.loads(claim["resolution"])
    assert resolution["verdict"] == "VERIFIED"
    assert resolution["confidence"] >= 0.7

def test_resolve_claim_rejected(direct_deploy, direct_owner, direct_vm):
    cg = direct_deploy("contracts/ClaimGuard.py")
    with direct_vm.prank(direct_owner):
        cg.init()
        cid = cg.createClaim("https://example.com", "Wrong", "Verify", "fact_check")

    direct_vm.mock_web(r".*", {"status": 200, "body": "Different content here"})
    direct_vm.mock_llm(r".*", '{"verdict":"REJECTED","confidence":0.95,"reasoning":"No match","evidence_summary":"Different"}')

    with direct_vm.prank(direct_owner):
        status = cg.resolveClaim(cid)
    assert status == "rejected"
    claim = cg.getClaim(cid)
    assert claim["votes_against"] == 1
    resolution = json.loads(claim["resolution"])
    assert resolution["verdict"] == "REJECTED"

def test_resolve_claim_inconclusive_low_confidence(direct_deploy, direct_owner, direct_vm):
    cg = direct_deploy("contracts/ClaimGuard.py")
    with direct_vm.prank(direct_owner):
        cg.init()
        cid = cg.createClaim("https://example.com", "x", "x", "fact_check")

    direct_vm.mock_web(r".*", {"status": 200, "body": "Maybe content"})
    direct_vm.mock_llm(r".*", '{"verdict":"VERIFIED","confidence":0.5,"reasoning":"Maybe","evidence_summary":"Unclear"}')

    with direct_vm.prank(direct_owner):
        status = cg.resolveClaim(cid)
    assert status == "inconclusive"
    claim = cg.getClaim(cid)
    resolution = json.loads(claim["resolution"])
    assert resolution["verdict"] == "INCONCLUSIVE"

def test_resolve_claim_invalid_verdict_becomes_inconclusive(direct_deploy, direct_owner, direct_vm):
    cg = direct_deploy("contracts/ClaimGuard.py")
    with direct_vm.prank(direct_owner):
        cg.init()
        cid = cg.createClaim("https://example.com", "x", "x", "fact_check")

    direct_vm.mock_web(r".*", {"status": 200, "body": "Something"})
    direct_vm.mock_llm(r".*", '{"verdict":"MAYBE","confidence":0.9,"reasoning":"?","evidence_summary":"?"}')

    with direct_vm.prank(direct_owner):
        status = cg.resolveClaim(cid)
    assert status == "inconclusive"
    claim = cg.getClaim(cid)
    resolution = json.loads(claim["resolution"])
    assert resolution["verdict"] == "INCONCLUSIVE"

def test_resolve_claim_llm_returns_garbage(direct_deploy, direct_owner, direct_vm):
    cg = direct_deploy("contracts/ClaimGuard.py")
    with direct_vm.prank(direct_owner):
        cg.init()
        cid = cg.createClaim("https://example.com", "x", "x", "fact_check")

    direct_vm.mock_web(r".*", {"status": 200, "body": "x"})
    direct_vm.mock_llm(r".*", "This is not JSON at all!!!")

    with direct_vm.prank(direct_owner):
        status = cg.resolveClaim(cid)
    assert status == "inconclusive"
    claim = cg.getClaim(cid)
    resolution = json.loads(claim["resolution"])
    assert resolution["verdict"] == "INCONCLUSIVE"
    assert "Failed to parse" in resolution["reasoning"]

def test_resolve_claim_web_fetch_fails(direct_deploy, direct_owner, direct_vm):
    cg = direct_deploy("contracts/ClaimGuard.py")
    with direct_vm.prank(direct_owner):
        cg.init()
        cid = cg.createClaim("https://dead-site.com", "x", "x", "fact_check")

    direct_vm.mock_web(r".*", {"status": 500, "body": ""})
    direct_vm.mock_llm(r".*", '{"verdict":"INCONCLUSIVE","confidence":0.0,"reasoning":"No evidence","evidence_summary":""}')

    with direct_vm.prank(direct_owner):
        status = cg.resolveClaim(cid)
    assert status == "inconclusive"

def test_unauthorized_resolver(direct_deploy, direct_owner, direct_alice, direct_vm):
    cg = direct_deploy("contracts/ClaimGuard.py")
    with direct_vm.prank(direct_owner):
        cg.init()
        cid = cg.createClaim("https://x.com", "x", "x", "fact_check")

    with direct_vm.prank(direct_alice):
        with direct_vm.expect_revert("Not an approved resolver"):
            cg.resolveClaim(cid)

def test_appeal_claim(direct_deploy, direct_owner, direct_vm):
    cg = direct_deploy("contracts/ClaimGuard.py")
    with direct_vm.prank(direct_owner):
        cg.init()
        cid = cg.createClaim("https://x.com", "x", "x", "fact_check")

    direct_vm.mock_web(r".*", {"status": 200, "body": "x"})
    direct_vm.mock_llm(r".*", '{"verdict":"REJECTED","confidence":0.9,"reasoning":"No","evidence_summary":"No"}')

    with direct_vm.prank(direct_owner):
        cg.resolveClaim(cid)
        result = cg.appealClaim(cid, "https://new-evidence.com")

    claim = cg.getClaim(cid)
    assert claim["status"] == "pending"
    assert claim["appeal_count"] == 1
    assert claim["evidence_url"] == "https://new-evidence.com"
    assert "Appeal #1" in result

def test_appeal_without_new_url_reverts(direct_deploy, direct_owner, direct_vm):
    cg = direct_deploy("contracts/ClaimGuard.py")
    with direct_vm.prank(direct_owner):
        cg.init()
        cid = cg.createClaim("https://x.com", "x", "x", "fact_check")

    direct_vm.mock_web(r".*", {"status": 200, "body": "x"})
    direct_vm.mock_llm(r".*", '{"verdict":"REJECTED","confidence":0.9,"reasoning":"No","evidence_summary":"No"}')

    with direct_vm.prank(direct_owner):
        cg.resolveClaim(cid)
        with direct_vm.expect_revert("Replacement evidence URL is required for appeal"):
            cg.appealClaim(cid, "")

def test_appeal_unauthorized(direct_deploy, direct_owner, direct_alice, direct_vm):
    cg = direct_deploy("contracts/ClaimGuard.py")
    with direct_vm.prank(direct_owner):
        cg.init()
        cid = cg.createClaim("https://x.com", "x", "x", "fact_check")

    direct_vm.mock_web(r".*", {"status": 200, "body": "x"})
    direct_vm.mock_llm(r".*", '{"verdict":"REJECTED","confidence":0.9,"reasoning":"No","evidence_summary":"No"}')

    with direct_vm.prank(direct_owner):
        cg.resolveClaim(cid)

    with direct_vm.prank(direct_alice):
        with direct_vm.expect_revert("Only the claim creator can appeal"):
            cg.appealClaim(cid, "https://evil.com")

def test_max_appeals(direct_deploy, direct_owner, direct_vm):
    cg = direct_deploy("contracts/ClaimGuard.py")
    with direct_vm.prank(direct_owner):
        cg.init()
        cid = cg.createClaim("https://x.com", "x", "x", "fact_check")

    direct_vm.mock_web(r".*", {"status": 200, "body": "x"})
    direct_vm.mock_llm(r".*", '{"verdict":"REJECTED","confidence":0.9,"reasoning":"No","evidence_summary":"No"}')

    with direct_vm.prank(direct_owner):
        for _ in range(3):
            cg.resolveClaim(cid)
            cg.appealClaim(cid, "https://new-evidence.com")
        cg.resolveClaim(cid)

        with direct_vm.expect_revert("Maximum appeal count reached"):
            cg.appealClaim(cid, "https://new-evidence.com")

def test_resolver_management(direct_deploy, direct_owner, direct_alice, direct_vm):
    cg = direct_deploy("contracts/ClaimGuard.py")
    with direct_vm.prank(direct_owner):
        cg.init()
        cg.addResolver(str(direct_alice))
        resolvers = cg.getResolvers()
        assert resolvers[str(direct_alice)] is True
        cg.removeResolver(str(direct_alice))
        resolvers = cg.getResolvers()
        assert resolvers[str(direct_alice)] is False

def test_unauthorized_resolver_management(direct_deploy, direct_owner, direct_alice, direct_vm):
    cg = direct_deploy("contracts/ClaimGuard.py")
    with direct_vm.prank(direct_owner):
        cg.init()

    with direct_vm.prank(direct_alice):
        with direct_vm.expect_revert("Only owner can add resolvers"):
            cg.addResolver(str(direct_alice))

def test_get_claim(direct_deploy, direct_owner, direct_vm):
    cg = direct_deploy("contracts/ClaimGuard.py")
    with direct_vm.prank(direct_owner):
        cg.init()
        cid = cg.createClaim("https://example.com", "content", "desc", "fact_check")

    claim = cg.getClaim(cid)
    assert claim["id"] == "1"
    assert claim["evidence_url"] == "https://example.com"
    assert claim["status"] == "pending"

def test_get_nonexistent_claim(direct_deploy, direct_owner, direct_vm):
    cg = direct_deploy("contracts/ClaimGuard.py")
    with direct_vm.prank(direct_owner):
        cg.init()
        with direct_vm.expect_revert("Claim not found"):
            cg.getClaim("999")

def test_get_all_claims(direct_deploy, direct_owner, direct_vm):
    cg = direct_deploy("contracts/ClaimGuard.py")
    with direct_vm.prank(direct_owner):
        cg.init()
        cg.createClaim("https://a.com", "x", "x", "fact_check")
        cg.createClaim("https://b.com", "x", "x", "custom")

    all_claims = cg.getAllClaims()
    assert len(all_claims) == 2

def test_get_claims_by_status(direct_deploy, direct_owner, direct_vm):
    cg = direct_deploy("contracts/ClaimGuard.py")
    with direct_vm.prank(direct_owner):
        cg.init()
        cg.createClaim("https://a.com", "x", "x", "fact_check")
        cg.createClaim("https://b.com", "x", "x", "fact_check")

    direct_vm.mock_web(r".*", {"status": 200, "body": "x"})
    direct_vm.mock_llm(r".*", '{"verdict":"VERIFIED","confidence":0.9,"reasoning":"Yes","evidence_summary":"Yes"}')

    with direct_vm.prank(direct_owner):
        cg.resolveClaim("1")

    pending = cg.getClaimsByStatus("pending")
    verified = cg.getClaimsByStatus("verified")
    assert len(pending) == 1
    assert len(verified) == 1

def test_get_stats_empty(direct_deploy, direct_owner, direct_vm):
    cg = direct_deploy("contracts/ClaimGuard.py")
    with direct_vm.prank(direct_owner):
        cg.init()

    stats = cg.getStats()
    assert stats["total_claims"] == "0"
    assert stats["success_rate"] == "0.0"

def test_get_stats_with_claims(direct_deploy, direct_owner, direct_vm):
    cg = direct_deploy("contracts/ClaimGuard.py")
    with direct_vm.prank(direct_owner):
        cg.init()
        for i in range(3):
            cg.createClaim(f"https://site{i}.com", "x", "x", "fact_check")

    direct_vm.mock_web(r".*", {"status": 200, "body": "x"})
    direct_vm.mock_llm(r".*", '{"verdict":"VERIFIED","confidence":0.9,"reasoning":"Yes","evidence_summary":"Yes"}')

    with direct_vm.prank(direct_owner):
        for i in range(1, 4):
            cg.resolveClaim(str(i))

    stats = cg.getStats()
    assert stats["total_claims"] == "3"
    assert stats["verified"] == "3"
    assert stats["success_rate"] == "1.0"

def test_categories_list(direct_deploy, direct_owner, direct_vm):
    cg = direct_deploy("contracts/ClaimGuard.py")
    with direct_vm.prank(direct_owner):
        cg.init()

    assert len(cg.CATEGORIES) == 6
    assert "prediction_market" in list(cg.CATEGORIES)
    assert "bounty_verification" in list(cg.CATEGORIES)

def test_claims_by_category(direct_deploy, direct_owner, direct_vm):
    cg = direct_deploy("contracts/ClaimGuard.py")
    with direct_vm.prank(direct_owner):
        cg.init()
        cg.createClaim("https://a.com", "x", "x", "prediction_market")
        cg.createClaim("https://b.com", "x", "x", "fact_check")
        cg.createClaim("https://c.com", "x", "x", "prediction_market")

    pm = cg.getClaimsByCategory("prediction_market")
    assert len(pm) == 2

def test_min_stake(direct_deploy, direct_owner, direct_vm):
    cg = direct_deploy("contracts/ClaimGuard.py")
    with direct_vm.prank(direct_owner):
        cg.init()

    assert cg.min_stake == 100

def test_claim_id_increment(direct_deploy, direct_owner, direct_vm):
    cg = direct_deploy("contracts/ClaimGuard.py")
    with direct_vm.prank(direct_owner):
        cg.init()
        id1 = cg.createClaim("https://a.com", "x", "x", "custom")
        id2 = cg.createClaim("https://b.com", "x", "x", "custom")

    assert id1 == "1"
    assert id2 == "2"
