#!/usr/bin/env python3
"""
Simple contract checker — validates Python syntax and basic structure.
No external dependencies needed.
"""

import ast
import sys
import os

def check_file(filepath):
    """Check Python syntax and basic contract structure"""
    print(f"\n🔍 Checking: {filepath}")

    with open(filepath, "r") as f:
        source = f.read()

    # 1. Syntax check
    try:
        tree = ast.parse(source)
        print("  ✅ Syntax OK")
    except SyntaxError as e:
        print(f"  ❌ Syntax Error: {e}")
        return False

    # 2. Check for required decorators
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
        if ok:
            print(f"  ✅ Found {req}")
        else:
            print(f"  ⚠️  Missing {req}")

    # 3. Check for gl.Contract inheritance
    has_contract = "gl.Contract" in source
    if has_contract:
        print("  ✅ Inherits from gl.Contract")
    else:
        print("  ⚠️  Does not inherit from gl.Contract")

    # 4. Check for non-deterministic blocks
    has_nondet = "gl.nondet" in source
    if has_nondet:
        print("  ✅ Uses non-deterministic blocks (gl.nondet)")
    else:
        print("  ⚠️  No non-deterministic blocks found")

    # 5. Check for eq_principle
    has_eq = "gl.eq_principle" in source
    if has_eq:
        print("  ✅ Uses equivalence principle (gl.eq_principle)")
    else:
        print("  ⚠️  No equivalence principle usage")

    # 6. Check for emit
    has_emit = "gl.emit" in source
    if has_emit:
        print("  ✅ Emits events (gl.emit)")
    else:
        print("  ⚠️  No event emissions")

    return True

def main():
    contracts_dir = os.path.join(os.path.dirname(__file__), "..", "contracts")

    if not os.path.exists(contracts_dir):
        print(f"❌ Contracts directory not found: {contracts_dir}")
        sys.exit(1)

    all_ok = True
    for filename in sorted(os.listdir(contracts_dir)):
        if filename.endswith(".py"):
            filepath = os.path.join(contracts_dir, filename)
            if not check_file(filepath):
                all_ok = False

    print("\n" + "="*50)
    if all_ok:
        print("✅ All contracts passed basic checks!")
    else:
        print("❌ Some contracts have issues.")

    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
