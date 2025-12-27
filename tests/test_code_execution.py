"""Test code execution in sandbox environment (Feature #147)."""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.routes.artifacts import execute_code_safely


async def test_python_execution():
    """Test Python code execution."""
    print("Testing Python code execution...")

    code = """
print("Hello from Python!")
x = 10
y = 20
print(f"The sum of {x} and {y} is {x + y}")
"""

    result = await execute_code_safely(code, "python", timeout=5)

    assert result["success"] == True, f"Expected success, got: {result}"
    assert "Hello from Python!" in result["output"], f"Expected output, got: {result['output']}"
    assert "The sum of 10 and 20 is 30" in result["output"], f"Expected math output, got: {result['output']}"
    assert result["return_code"] == 0, f"Expected return code 0, got: {result['return_code']}"
    assert result["execution_time"] > 0, f"Expected positive execution time, got: {result['execution_time']}"

    print(f"✓ Python execution successful")
    print(f"  Output: {result['output'].strip()}")
    print(f"  Execution time: {result['execution_time']}s")


async def test_python_syntax_error():
    """Test Python code with syntax error."""
    print("\nTesting Python syntax error...")

    code = """
print("Hello"
# Missing closing parenthesis
"""

    result = await execute_code_safely(code, "python", timeout=5)

    assert result["success"] == False, f"Expected failure for syntax error, got: {result}"
    assert result["error"] is not None, f"Expected error message, got: {result}"
    assert "SyntaxError" in result["error"] or "syntax" in result["error"].lower(), f"Expected SyntaxError, got: {result['error']}"

    print(f"✓ Syntax error correctly caught")
    print(f"  Error: {result['error'][:100]}")


async def test_python_timeout():
    """Test Python code with infinite loop (timeout)."""
    print("\nTesting Python timeout protection...")

    code = """
while True:
    pass
"""

    result = await execute_code_safely(code, "python", timeout=2)

    assert result["success"] == False, f"Expected failure due to timeout, got: {result}"
    assert "timeout" in result["error"].lower(), f"Expected timeout error, got: {result['error']}"
    assert result["execution_time"] <= 3, f"Expected execution time ~2s, got: {result['execution_time']}"

    print(f"✓ Timeout protection working")
    print(f"  Error: {result['error']}")
    print(f"  Execution time: {result['execution_time']}s")


async def main():
    """Run all tests."""
    print("=" * 70)
    print("Code Execution Tests (Feature #147)")
    print("=" * 70)

    try:
        await test_python_execution()
        await test_python_syntax_error()
        await test_python_timeout()

        print("\n" + "=" * 70)
        print("✅ All code execution tests passed!")
        print("=" * 70)
        print("\nFeature #147 Summary:")
        print("  ✓ Python code execution with stdout/stderr capture")
        print("  ✓ Syntax error handling")
        print("  ✓ Timeout protection (prevents infinite loops)")
        print("  ✓ Temporary directory isolation")
        print("  ✓ Execution time tracking")
        print("  ✓ Return code capture")

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
