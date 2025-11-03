"""Complete test suite for metadata extraction service."""

import asyncio
import subprocess
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_test_file(test_file: str) -> bool:
    """Run a test file and return success status."""
    print(f"\n{'='*60}")
    print(f"Running {test_file}")
    print("=" * 60)

    try:
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=False,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )

        if result.returncode == 0:
            print(f"✅ {test_file} passed")
            return True
        else:
            print(f"❌ {test_file} failed with exit code {result.returncode}")
            return False

    except Exception as e:
        print(f"❌ {test_file} failed with exception: {e}")
        return False


async def run_complete_test_suite():
    """Run the complete metadata test suite."""
    print("🚀 Starting Complete Metadata Service Test Suite")
    print("=" * 80)

    test_files = [
        "test_metadata_basic.py",
        "test_metadata_repo_basic.py",
        "test_metadata_integration.py",
    ]

    results = []

    for test_file in test_files:
        success = run_test_file(test_file)
        results.append((test_file, success))

    # Summary
    print(f"\n{'='*80}")
    print("TEST SUITE SUMMARY")
    print("=" * 80)

    passed = 0
    failed = 0

    for test_file, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_file:<40} {status}")
        if success:
            passed += 1
        else:
            failed += 1

    print(f"\nTotal: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Metadata extraction service is ready.")
        return True
    else:
        print(f"\n💥 {failed} test(s) failed. Please review and fix issues.")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_complete_test_suite())
    sys.exit(0 if success else 1)
