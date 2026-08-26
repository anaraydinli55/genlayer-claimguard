"""
ClaimGuard Contract Tests — unittest
Run: python tests/test_claimguard.py
"""

import unittest
import sys
import os
import json
from unittest.mock import MagicMock
from types import ModuleType

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

genlayer_pkg = ModuleType("genlayer")
genlayer_pkg.__path__ = []
sys.modules["genlayer"] = genlayer_pkg
sys.modules["genlayer.std"] = ModuleType("genlayer.std")

fake_gl = ModuleType("genlayer.gl")
fake_gl.message = MagicMock()
fake_gl.message.sender_address = "0x1234567890abcdef"
fake_gl.block = MagicMock()
fake_gl.block.timestamp = 1690000000
fake_gl.emit = MagicMock()

fake_eq = MagicMock()
fake_eq.json_eq = lambda fn: fn()
fake_eq.strict_eq = lambda fn: fn()
fake_gl.eq_principle = fake_eq

fake_nondet = MagicMock()
fake_web = MagicMock()
fake_web.render = MagicMock(return_value="<html><body>Test content found here</body></html>")
fake_web.get = MagicMock(return_value=MagicMock(body=b"Test content found here"))
fake_nondet.web = fake_web
fake_nondet.exec_prompt = MagicMock(
    return_value='{"verdict":"VERIFIED","confidence":0.85,"reasoning":"Content matches","evidence_summary":"Found"}'
)
fake_gl.nondet = fake_nondet

fake_gl.Contract = object
fake_gl.public = MagicMock()
fake_gl.public.write = lambda fn: fn
fake_gl.public.view = lambda fn: fn

sys.modules["genlayer.gl"] = fake_gl
genlayer_pkg.gl = fake_gl
sys.modules["genlayer.std"] = ModuleType("genlayer.std")
sys.modules["genlayer.std._wasi"] = fake_gl

import importlib.util
spec = importlib.util.spec_from_file_location(
    "ClaimGuard_mocked",
    os.path.join(PROJECT_ROOT, "contracts", "ClaimGuard.py")
)
claimguard_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(claimguard_module)
ClaimGuard = claimguard_module.ClaimGuard

for _name in ["genlayer.std._wasi", "genlayer.std", "genlayer.gl"]:
    _mod = sys.modules.get(_name)
    if _mod is fake_gl:
        del sys.modules[_name]
if sys.modules.get("genlayer") is genlayer_pkg:
    del sys.modules["genlayer"]


class TestClaimGuard(unittest.TestCase):

    def setUp(self):
        fake_gl.emit.reset_mock()
        fake_gl.message.sender_address = "0x1234567890abcdef"
        fake_nondet.exec_prompt = MagicMock(
            return_value='{"verdict":"VERIFIED","confidence":0.85,"reasoning":"ok","evidence_summary":"ok"}'
        )

    def test_init(self):
        c = ClaimGuard()
        c.init()
        self.assertEqual(c.owner, "0x1234567890abcdef")
        resolvers = c.getResolvers()
        self.assertTrue(resolvers["0x1234567890abcdef"])

    def test_create_claim(self):
        c = ClaimGuard()
        c.init()
        cid = c.createClaim("https://example.com", "Test content", "Verify this", "fact_check")
        self.assertEqual(cid, "1")
        self.assertEqual(c.claim_count, 1)
        claim = c.getClaim("1")
        self.assertEqual(claim["status"], "pending")
        self.assertEqual(claim["category"], "fact_check")
        self.assertEqual(claim["evidence_url"], "https://example.com")
        self.assertEqual(claim["id"], "1")
        self.assertIn("resolution", claim)
        self.assertIn("created_at", claim)

    def test_create_claim_invalid_category(self):
        c = ClaimGuard()
        c.init()
        with self.assertRaises(ValueError) as ctx:
            c.createClaim("https://x.com", "x", "x", "nonexistent")
        self.assertIn("Invalid category", str(ctx.exception))

    def test_resolve_claim_verified(self):
        c = ClaimGuard()
        c.init()
        cid = c.createClaim("https://example.com", "Test", "Verify", "fact_check")
        status = c.resolveClaim(cid)
        self.assertEqual(status, "verified")
        claim = c.getClaim(cid)
        self.assertEqual(claim["status"], "verified")
        self.assertEqual(claim["votes_for"], 1)
        resolution = json.loads(claim["resolution"])
        self.assertEqual(resolution["verdict"], "VERIFIED")
        self.assertGreaterEqual(resolution["confidence"], 0.7)

    def test_resolve_claim_rejected(self):
        c = ClaimGuard()
        c.init()
        fake_nondet.exec_prompt = MagicMock(
            return_value='{"verdict":"REJECTED","confidence":0.95,"reasoning":"No match","evidence_summary":"Different"}'
        )
        cid = c.createClaim("https://example.com", "Wrong", "Verify", "fact_check")
        status = c.resolveClaim(cid)
        self.assertEqual(status, "rejected")
        claim = c.getClaim(cid)
        self.assertEqual(claim["votes_against"], 1)
        resolution = json.loads(claim["resolution"])
        self.assertEqual(resolution["verdict"], "REJECTED")

    def test_resolve_claim_inconclusive_low_confidence(self):
        c = ClaimGuard()
        c.init()
        fake_nondet.exec_prompt = MagicMock(
            return_value='{"verdict":"VERIFIED","confidence":0.5,"reasoning":"Maybe","evidence_summary":"Unclear"}'
        )
        cid = c.createClaim("https://example.com", "x", "x", "fact_check")
        status = c.resolveClaim(cid)
        self.assertEqual(status, "inconclusive")
        claim = c.getClaim(cid)
        resolution = json.loads(claim["resolution"])
        self.assertEqual(resolution["verdict"], "INCONCLUSIVE")

    def test_resolve_claim_invalid_verdict_becomes_inconclusive(self):
        c = ClaimGuard()
        c.init()
        fake_nondet.exec_prompt = MagicMock(
            return_value='{"verdict":"MAYBE","confidence":0.9,"reasoning":"?","evidence_summary":"?"}'
        )
        cid = c.createClaim("https://example.com", "x", "x", "fact_check")
        status = c.resolveClaim(cid)
        self.assertEqual(status, "inconclusive")
        claim = c.getClaim(cid)
        resolution = json.loads(claim["resolution"])
        self.assertEqual(resolution["verdict"], "INCONCLUSIVE")

    def test_unauthorized_resolver(self):
        c = ClaimGuard()
        c.init()
        cid = c.createClaim("https://x.com", "x", "x", "fact_check")
        fake_gl.message.sender_address = "0xunauthorized"
        with self.assertRaises(ValueError) as ctx:
            c.resolveClaim(cid)
        self.assertIn("Not an approved resolver", str(ctx.exception))

    def test_appeal_claim(self):
        c = ClaimGuard()
        c.init()
        cid = c.createClaim("https://x.com", "x", "x", "fact_check")
        c.resolveClaim(cid)
        result = c.appealClaim(cid, "https://new-evidence.com")
        claim = c.getClaim(cid)
        self.assertEqual(claim["status"], "pending")
        self.assertEqual(claim["appeal_count"], 1)
        self.assertEqual(claim["evidence_url"], "https://new-evidence.com")
        self.assertIn("Appeal #1", result)

    def test_appeal_without_new_url(self):
        c = ClaimGuard()
        c.init()
        cid = c.createClaim("https://x.com", "x", "x", "fact_check")
        c.resolveClaim(cid)
        c.appealClaim(cid, "")
        claim = c.getClaim(cid)
        self.assertEqual(claim["evidence_url"], "https://x.com")

    def test_appeal_unauthorized(self):
        c = ClaimGuard()
        c.init()
        cid = c.createClaim("https://x.com", "x", "x", "fact_check")
        c.resolveClaim(cid)
        fake_gl.message.sender_address = "0xattacker"
        with self.assertRaises(ValueError) as ctx:
            c.appealClaim(cid, "https://evil.com")
        self.assertIn("Only the claim creator can appeal", str(ctx.exception))

    def test_max_appeals(self):
        c = ClaimGuard()
        c.init()
        cid = c.createClaim("https://x.com", "x", "x", "fact_check")
        for _ in range(3):
            c.resolveClaim(cid)
            c.appealClaim(cid)
        c.resolveClaim(cid)
        with self.assertRaises(ValueError) as ctx:
            c.appealClaim(cid)
        self.assertIn("Maximum appeal count reached", str(ctx.exception))

    def test_resolver_management(self):
        c = ClaimGuard()
        c.init()
        c.addResolver("0xnewresolver")
        resolvers = c.getResolvers()
        self.assertTrue(resolvers["0xnewresolver"])
        c.removeResolver("0xnewresolver")
        resolvers = c.getResolvers()
        self.assertFalse(resolvers["0xnewresolver"])

    def test_unauthorized_resolver_management(self):
        c = ClaimGuard()
        c.init()
        fake_gl.message.sender_address = "0xnotowner"
        with self.assertRaises(ValueError) as ctx:
            c.addResolver("0xnewresolver")
        self.assertIn("Only owner", str(ctx.exception))

    def test_get_claim(self):
        c = ClaimGuard()
        c.init()
        cid = c.createClaim("https://example.com", "content", "desc", "fact_check")
        claim = c.getClaim(cid)
        self.assertEqual(claim["id"], "1")
        self.assertEqual(claim["evidence_url"], "https://example.com")
        self.assertEqual(claim["status"], "pending")

    def test_get_nonexistent_claim(self):
        c = ClaimGuard()
        c.init()
        with self.assertRaises(ValueError) as ctx:
            c.getClaim("999")
        self.assertIn("Claim not found", str(ctx.exception))

    def test_get_all_claims(self):
        c = ClaimGuard()
        c.init()
        c.createClaim("https://a.com", "x", "x", "fact_check")
        c.createClaim("https://b.com", "x", "x", "custom")
        all_claims = c.getAllClaims()
        self.assertEqual(len(all_claims), 2)

    def test_get_claims_by_status(self):
        c = ClaimGuard()
        c.init()
        c.createClaim("https://a.com", "x", "x", "fact_check")
        c.createClaim("https://b.com", "x", "x", "fact_check")
        c.resolveClaim("1")
        pending = c.getClaimsByStatus("pending")
        verified = c.getClaimsByStatus("verified")
        self.assertEqual(len(pending), 1)
        self.assertEqual(len(verified), 1)

    def test_get_stats_empty(self):
        c = ClaimGuard()
        c.init()
        stats = c.getStats()
        self.assertEqual(stats["total_claims"], "0")
        self.assertEqual(stats["success_rate"], "0.0")

    def test_get_stats_with_claims(self):
        c = ClaimGuard()
        c.init()
        for i in range(3):
            c.createClaim(f"https://site{i}.com", "x", "x", "fact_check")
        for i in range(1, 4):
            c.resolveClaim(str(i))
        stats = c.getStats()
        self.assertEqual(stats["total_claims"], "3")
        self.assertEqual(stats["verified"], "3")
        self.assertEqual(stats["success_rate"], "1.0")

    def test_categories_list(self):
        c = ClaimGuard()
        self.assertEqual(len(c.CATEGORIES), 6)
        self.assertIn("prediction_market", c.CATEGORIES)
        self.assertIn("bounty_verification", c.CATEGORIES)

    def test_claims_by_category(self):
        c = ClaimGuard()
        c.init()
        c.createClaim("https://a.com", "x", "x", "prediction_market")
        c.createClaim("https://b.com", "x", "x", "fact_check")
        c.createClaim("https://c.com", "x", "x", "prediction_market")
        pm = c.getClaimsByCategory("prediction_market")
        self.assertEqual(len(pm), 2)

    def test_min_stake(self):
        c = ClaimGuard()
        c.init()
        self.assertEqual(c.min_stake, 100)

    def test_claim_id_increment(self):
        c = ClaimGuard()
        c.init()
        id1 = c.createClaim("https://a.com", "x", "x", "custom")
        id2 = c.createClaim("https://b.com", "x", "x", "custom")
        self.assertEqual(id1, "1")
        self.assertEqual(id2, "2")


if __name__ == "__main__":
    unittest.main()
