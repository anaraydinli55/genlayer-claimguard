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
    genlayer_pkg.TreeMap = MockTreeMap
    genlayer_pkg.DynArray = MockDynArray
    genlayer_pkg.u256 = MockU256
    genlayer_pkg.Contract = object
    genlayer_pkg.gl = fake_gl

    # eq_principle - decorator-style for static analysis compatibility
    class EqPrinciple:
        @staticmethod
        def json_eq(fn, *args, **kwargs):
            if callable(fn):
                return fn(*args, **kwargs)
            return fn

        @staticmethod
        def strict_eq(fn, *args, **kwargs):
            if callable(fn):
                return fn(*args, **kwargs)
            return fn

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
