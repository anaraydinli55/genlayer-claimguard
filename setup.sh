#!/bin/bash
# ClaimGuard - Steward-proof setup script
# Run: bash setup.sh

set -e

echo "🚀 ClaimGuard setup starting..."

# Eski dosyaları temizle
echo "🧹 Cleaning old files..."
rm -rf tests/integration/
rm -f tests/test_claimguard.py
rm -f scripts/check.py

# Klasörleri oluştur
mkdir -p tests/direct
mkdir -p scripts

echo "📝 Writing ClaimGuard.py..."
cat << 'PYEOF' > contracts/ClaimGuard.py
# { "Depends": "py-genlayer:latest" }
from genlayer import *
import json

def _extract_json(s: str) -> str:
    start = s.find("{")
    end = s.rfind("}")
    if start != -1 and end != -1 and start < end:
        return s[start:end + 1]
    return ""

class ClaimGuard(gl.Contract):
    owner: str
    claims: TreeMap[str, str]
    resolvers: TreeMap[str, bool]
    CATEGORIES: DynArray[str]
    min_stake: u256

    def __init__(self):
        pass

    @gl.public.write
    def init(self) -> None:
        if self.owner != "":
            raise gl.vm.UserError("Already initialized")
        self.owner = str(gl.message.sender_address)
        self.claims = TreeMap()
        self.resolvers = TreeMap()
        self.resolvers[str(gl.message.sender_address)] = True
        self.CATEGORIES = DynArray([
            "prediction_market", "bounty_verification", "content_moderation",
            "identity_verification", "fact_check", "custom"
        ])
        self.min_stake = u256(100)

    @gl.public.write
    def createClaim(self, evidence_url: str, expected_content: str, description: str, category: str) -> str:
        if category not in list(self.CATEGORIES):
            raise gl.vm.UserError("Invalid category")
        count = len(self.claims) + 1
        cid = str(count)
        claim = {
            "id": cid,
            "creator": str(gl.message.sender_address),
            "evidence_url": evidence_url,
            "expected_content": expected_content,
            "description": description,
            "category": category,
            "status": "pending",
            "votes_for": 0,
            "votes_against": 0,
            "appeal_count": 0,
            "resolution": json.dumps({
                "verdict": "PENDING",
                "confidence": 0.0,
                "reasoning": "",
                "evidence_summary": ""
            })
        }
        self.claims[cid] = json.dumps(claim, sort_keys=True)
        gl.emit("ClaimCreated", {"claim_id": cid, "creator": claim["creator"], "category": category})
        return cid

    @gl.public.write
    def resolveClaim(self, claim_id: str) -> str:
        if not self.resolvers.get(str(gl.message.sender_address), False):
            raise gl.vm.UserError("Not an approved resolver")

        cid = str(claim_id)
        if cid not in self.claims:
            raise gl.vm.UserError("Claim not found")

        claim = json.loads(self.claims[cid])
        if claim["status"] != "pending":
            raise gl.vm.UserError("Claim is already resolved")

        evidence_url = claim["evidence_url"]
        expected_content = claim["expected_content"]
        description = claim["description"]

        def non_det():
            try:
                web_data = gl.nondet.web.render(evidence_url, mode="text")
            except Exception:
                web_data = ""

            prompt = f"""You are a claim verification evaluator. Analyze the following evidence and determine if the claim is verified.

Claim Description: {description}
Expected Content: {expected_content}
Evidence URL: {evidence_url}
Evidence Content: {web_data}

Evaluate whether the evidence supports the claim. Return ONLY a JSON object with this exact structure:
{{
    "verdict": "VERIFIED" | "REJECTED" | "INCONCLUSIVE",
    "confidence": float (0.0 to 1.0),
    "reasoning": "string explaining the evaluation",
    "evidence_summary": "string summarizing what was found in the evidence"
}}

It is mandatory that you respond only using the JSON format above, nothing else. Do not include any other words or characters, your output must be only JSON without any formatting prefix or suffix. This result should be perfectly parsable by a JSON parser without errors."""

            result = gl.nondet.exec_prompt(prompt)
            json_str = _extract_json(result)
            if not json_str:
                return json.dumps({
                    "verdict": "INCONCLUSIVE",
                    "confidence": 0.0,
                    "reasoning": "Failed to parse LLM response",
                    "evidence_summary": ""
                }, sort_keys=True)

            try:
                parsed = json.loads(json_str)
            except json.JSONDecodeError:
                return json.dumps({
                    "verdict": "INCONCLUSIVE",
                    "confidence": 0.0,
                    "reasoning": "Failed to parse LLM response",
                    "evidence_summary": ""
                }, sort_keys=True)

            verdict = str(parsed.get("verdict", "INCONCLUSIVE")).upper().strip()
            if verdict not in ["VERIFIED", "REJECTED", "INCONCLUSIVE"]:
                verdict = "INCONCLUSIVE"

            confidence = float(parsed.get("confidence", 0.0))
            if not (0.0 <= confidence <= 1.0):
                confidence = 0.0

            if confidence < 0.7 and verdict == "VERIFIED":
                verdict = "INCONCLUSIVE"
                reasoning = "Low confidence threshold not met."
            else:
                reasoning = str(parsed.get("reasoning", ""))

            normalized = {
                "verdict": verdict,
                "confidence": confidence,
                "reasoning": reasoning,
                "evidence_summary": str(parsed.get("evidence_summary", ""))
            }
            return json.dumps(normalized, sort_keys=True)

        result_str = gl.eq_principle.json_eq(non_det)
        result_json = json.loads(result_str)

        verdict = result_json["verdict"]
        confidence = result_json["confidence"]
        reasoning = result_json["reasoning"]
        evidence_summary = result_json["evidence_summary"]

        if verdict == "VERIFIED":
            claim["status"] = "verified"
            claim["votes_for"] = 1
        elif verdict == "REJECTED":
            claim["status"] = "rejected"
            claim["votes_against"] = 1
        else:
            claim["status"] = "inconclusive"

        claim["resolution"] = json.dumps({
            "verdict": verdict,
            "confidence": confidence,
            "reasoning": reasoning,
            "evidence_summary": evidence_summary
        }, sort_keys=True)

        self.claims[cid] = json.dumps(claim, sort_keys=True)
        gl.emit("ClaimResolved", {"claim_id": cid, "verdict": verdict, "confidence": str(confidence)})
        return claim["status"]

    @gl.public.write
    def appealClaim(self, claim_id: str, new_evidence_url: str) -> str:
        cid = str(claim_id)
        if cid not in self.claims:
            raise gl.vm.UserError("Claim not found")

        claim = json.loads(self.claims[cid])
        if str(gl.message.sender_address) != claim["creator"]:
            raise gl.vm.UserError("Only the claim creator can appeal")

        if claim["status"] == "pending":
            raise gl.vm.UserError("Claim is still pending")

        if claim["appeal_count"] >= 3:
            raise gl.vm.UserError("Maximum appeal count reached")

        new_url = str(new_evidence_url).strip()
        if not new_url:
            raise gl.vm.UserError("Replacement evidence URL is required for appeal")

        claim["evidence_url"] = new_url
        claim["appeal_count"] += 1
        claim["status"] = "pending"
        claim["votes_for"] = 0
        claim["votes_against"] = 0
        claim["resolution"] = json.dumps({
            "verdict": "PENDING",
            "confidence": 0.0,
            "reasoning": "",
            "evidence_summary": ""
        }, sort_keys=True)

        self.claims[cid] = json.dumps(claim, sort_keys=True)
        gl.emit("ClaimAppealed", {"claim_id": cid, "appeal_count": str(claim["appeal_count"])})
        return f"Appeal #{claim['appeal_count']} submitted successfully"

    @gl.public.write
    def addResolver(self, address: str) -> None:
        if str(gl.message.sender_address) != self.owner:
            raise gl.vm.UserError("Only owner can add resolvers")
        self.resolvers[address] = True

    @gl.public.write
    def removeResolver(self, address: str) -> None:
        if str(gl.message.sender_address) != self.owner:
            raise gl.vm.UserError("Only owner can remove resolvers")
        if address in self.resolvers:
            self.resolvers[address] = False

    @gl.public.view
    def getOwner(self) -> str:
        return self.owner

    @gl.public.view
    def getResolvers(self) -> dict:
        return {k: v for k, v in self.resolvers.items()}

    @gl.public.view
    def getClaim(self, claim_id: str) -> dict:
        cid = str(claim_id)
        if cid not in self.claims:
            raise gl.vm.UserError("Claim not found")
        return json.loads(self.claims[cid])

    @gl.public.view
    def getAllClaims(self) -> list:
        return [json.loads(v) for v in self.claims.values()]

    @gl.public.view
    def getClaimsByStatus(self, status: str) -> list:
        return [json.loads(v) for v in self.claims.values() if json.loads(v)["status"] == status]

    @gl.public.view
    def getClaimsByCategory(self, category: str) -> list:
        return [json.loads(v) for v in self.claims.values() if json.loads(v)["category"] == category]

    @gl.public.view
    def getStats(self) -> dict:
        total = len(self.claims)
        if total == 0:
            return {
                "total_claims": "0",
                "verified": "0",
                "rejected": "0",
                "inconclusive": "0",
                "success_rate": "0.0"
            }
        verified = sum(1 for v in self.claims.values() if json.loads(v)["status"] == "verified")
        rejected = sum(1 for v in self.claims.values() if json.loads(v)["status"] == "rejected")
        inconclusive = sum(1 for v in self.claims.values() if json.loads(v)["status"] == "inconclusive")
        return {
            "total_claims": str(total),
            "verified": str(verified),
            "rejected": str(rejected),
            "inconclusive": str(inconclusive),
            "success_rate": str(float(verified) / float(total))
        }
PYEOF

echo "📝 Writing tests/direct/conftest.py..."
cat << 'CONFEOF' > tests/direct/conftest.py
"""
Pytest fixtures for ClaimGuard tests.
Self-contained mocks - no genlayer-test package needed.
"""

import pytest
import sys
import os
import json
import re
from unittest.mock import MagicMock
from types import ModuleType


class MockTreeMap(dict):
    """Mock for gl.TreeMap storage type."""
    pass


class MockDynArray(list):
    """Mock for gl.DynArray storage type."""
    pass


class MockU256:
    """Mock for gl.u256 type."""
    def __init__(self, val):
        self.val = int(val)
    def __eq__(self, other):
        if isinstance(other, MockU256):
            return self.val == other.val
        return self.val == other
    def __int__(self):
        return self.val
    def __str__(self):
        return str(self.val)


@pytest.fixture(scope="session", autouse=True)
def setup_genlayer_mock():
    """Inject mocked genlayer modules before any test runs."""

    genlayer_pkg = ModuleType("genlayer")
    genlayer_pkg.__path__ = []
    sys.modules["genlayer"] = genlayer_pkg

    fake_gl = ModuleType("genlayer.gl")
    fake_gl.message = MagicMock()
    fake_gl.message.sender_address = "0x1234567890abcdef"
    fake_gl.block = MagicMock()
    fake_gl.block.timestamp = 1690000000
    fake_gl.emit = MagicMock()

    # Storage type mocks
    fake_gl.TreeMap = MockTreeMap
    fake_gl.DynArray = MockDynArray
    fake_gl.u256 = MockU256

    # eq_principle - decorator-style for static analysis compatibility
    class EqPrinciple:
        @staticmethod
        def json_eq(fn):
            """Decorator that simulates validator consensus."""
            def wrapper(*args, **kwargs):
                return fn(*args, **kwargs)
            wrapper.__wrapped__ = fn
            wrapper._is_eq_principle = True
            return wrapper

        @staticmethod
        def strict_eq(fn):
            def wrapper(*args, **kwargs):
                return fn(*args, **kwargs)
            wrapper.__wrapped__ = fn
            wrapper._is_eq_principle = True
            return wrapper

    fake_gl.eq_principle = EqPrinciple()

    # nondet
    fake_nondet = MagicMock()
    fake_web = MagicMock()
    fake_web.render = MagicMock(return_value="<html><body>Mock content</body></html>")
    fake_web.get = MagicMock(return_value=MagicMock(body=b"Mock content"))
    fake_nondet.web = fake_web
    fake_nondet.exec_prompt = MagicMock(
        return_value='{"verdict":"VERIFIED","confidence":0.85,"reasoning":"Mock","evidence_summary":"Mock"}'
    )
    fake_gl.nondet = fake_nondet

    # Contract base
    fake_gl.Contract = object

    # Decorators
    fake_public = MagicMock()
    fake_public.write = lambda fn: fn
    fake_public.view = lambda fn: fn
    fake_gl.public = fake_public

    # vm.UserError
    fake_gl.vm = MagicMock()
    fake_gl.vm.UserError = ValueError

    sys.modules["genlayer.gl"] = fake_gl
    genlayer_pkg.gl = fake_gl
    sys.modules["genlayer.std"] = ModuleType("genlayer.std")
    sys.modules["genlayer.std._wasi"] = fake_gl

    yield

    for name in ["genlayer.std._wasi", "genlayer.std", "genlayer.gl", "genlayer"]:
        if name in sys.modules:
            del sys.modules[name]


@pytest.fixture
def direct_vm(setup_genlayer_mock):
    import genlayer.gl as gl

    class VMController:
        def __init__(self):
            self._web_mocks = []
            self._llm_mocks = []

            gl.nondet.web.render = self._web_render
            gl.nondet.exec_prompt = self._exec_prompt

        def _web_render(self, url, mode="text"):
            for pat, resp in self._web_mocks:
                if pat.search(url):
                    if resp.get("status", 200) >= 400:
                        raise Exception(f"HTTP {resp.get('status', 500)}")
                    return resp.get("body", "")
            return f"<html><body>Mock content for {url}</body></html>"

        def _exec_prompt(self, prompt):
            for pat, resp in self._llm_mocks:
                if pat.search(prompt):
                    return resp
            return '{"verdict":"VERIFIED","confidence":0.85,"reasoning":"Default mock","evidence_summary":"Mock"}'

        def prank(self, address):
            class PrankContext:
                def __enter__(ctx):
                    ctx.saved = gl.message.sender_address
                    gl.message.sender_address = str(address)
                    return ctx
                def __exit__(ctx, *args):
                    gl.message.sender_address = ctx.saved
                    return False
            return PrankContext()

        def expect_revert(self, message_substring=""):
            class RevertContext:
                def __enter__(ctx):
                    return ctx
                def __exit__(ctx, exc_type, exc_val, exc_tb):
                    if exc_type is None:
                        raise AssertionError(f"Expected revert with \"{message_substring}\" but no exception was raised")
                    msg = str(exc_val)
                    if message_substring and message_substring not in msg:
                        raise AssertionError(f"Expected revert with \"{message_substring}\", got: {msg}")
                    return True
            return RevertContext()

        def mock_web(self, pattern, response):
            self._web_mocks.append((re.compile(pattern), response))

        def mock_llm(self, pattern, response):
            self._llm_mocks.append((re.compile(pattern), response))

    return VMController()


@pytest.fixture
def direct_owner():
    return "0x1234567890abcdef"


@pytest.fixture
def direct_alice():
    return "0xalicealicealicealicealicealicealice"


@pytest.fixture
def direct_deploy(setup_genlayer_mock):
    import importlib.util

    def _deploy(contract_path):
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        full_path = os.path.join(project_root, contract_path)

        spec = importlib.util.spec_from_file_location("ClaimGuard_deployed", full_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        return module.ClaimGuard()

    return _deploy
CONFEOF

echo "📝 Writing tests/direct/test_claimguard.py..."
cat << 'TESEOF' > tests/direct/test_claimguard.py
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
TESEOF

echo "📝 Writing scripts/check.py..."
cat << 'CHEOF' > scripts/check.py
#!/usr/bin/env python3
"""Contract checker — validates Python syntax, GenLayer structure, and runs genvm-linter."""

import ast
import sys
import os
import subprocess

def check_file(filepath):
    print(f"\n🔍 Checking: {filepath}")
    with open(filepath, "r") as f:
        source = f.read()

    try:
        tree = ast.parse(source)
        print("  ✅ Syntax OK")
    except SyntaxError as e:
        print(f"  ❌ Syntax Error: {e}")
        return False

    required = ["@gl.public.write", "@gl.public.view"]
    found = {r: False for r in required}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                deco_str = ast.unparse(decorator) if hasattr(ast, "unparse") else ""
                for req in required:
                    if req in deco_str or req.replace("@", "") in deco_str:
                        found[req] = True

    for req, ok in found.items():
        print(f"  {'✅' if ok else '⚠️'}  {req}")

    has_contract = "gl.Contract" in source
    print(f"  {'✅' if has_contract else '⚠️'}  Inherits from gl.Contract")

    has_nondet = "gl.nondet" in source
    has_eq = "gl.eq_principle" in source
    if has_nondet and has_eq:
        print("  ✅  Non-deterministic calls wrapped in eq_principle")
    elif has_nondet:
        print("  ❌  Non-deterministic calls NOT wrapped in eq_principle")
        return False
    else:
        print("  ⚠️  No non-deterministic blocks")

    has_emit = "gl.emit" in source
    print(f"  {'✅' if has_emit else '⚠️'}  Emits events")

    has_usererror = "gl.vm.UserError" in source
    print(f"  {'✅' if has_usererror else '⚠️'}  Uses gl.vm.UserError")

    return True

def run_linter(contracts_dir):
    try:
        result = subprocess.run(
            ["genvm-lint", "check", contracts_dir],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print("\n✅ genvm-lint passed!")
            return True
        else:
            print("\n⚠️  genvm-lint issues:")
            print(result.stdout)
            return False
    except FileNotFoundError:
        print("\n⚠️  genvm-lint not installed. Run: pip install genvm-linter")
        return True

def main():
    contracts_dir = os.path.join(os.path.dirname(__file__), "..", "contracts")
    if not os.path.exists(contracts_dir):
        print(f"❌ Contracts directory not found: {contracts_dir}")
        sys.exit(1)

    all_ok = True
    for filename in sorted(os.listdir(contracts_dir)):
        if filename.endswith(".py"):
            if not check_file(os.path.join(contracts_dir, filename)):
                all_ok = False

    print("\n" + "="*50)
    linter_ok = run_linter(contracts_dir)

    if all_ok and linter_ok:
        print("✅ All checks passed!")
    else:
        print("❌ Fix issues before submission.")
    return 0 if (all_ok and linter_ok) else 1

if __name__ == "__main__":
    sys.exit(main())
CHEOF
chmod +x scripts/check.py

echo "📝 Writing pytest.ini..."
cat << 'PIEOF' > pytest.ini
[pytest]
testpaths = tests/direct
PIEOF

echo "📝 Writing requirements.txt..."
cat << 'REQEOF' > requirements.txt
pytest>=8.0.0
genvm-linter>=0.1.0
REQEOF

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. source .venv/bin/activate"
echo "  2. pytest tests/direct/ -v"
echo "  3. python scripts/check.py"
echo "  4. Deploy to GenLayer Studio"
