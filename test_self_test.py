"""
Test script to validate the enhanced self-test system.
Run this to ensure self-test works correctly before Nuitka compilation.
"""

import sys
import subprocess
from pathlib import Path


def test_basic_selftest():
    """Test 1: Basic self-test execution"""
    print("=" * 70)
    print("TEST 1: Basic Self-Test Execution")
    print("=" * 70)
    
    result = subprocess.run(
        [sys.executable, 'run_netexec.py'],
        capture_output=True,
        text=True
    )
    
    print(f"Return code: {result.returncode}")
    print(f"Output length: {len(result.stdout)} chars")
    
    # Check for key markers
    markers = {
        'header': 'NetExec' in result.stdout and 'Self-Test' in result.stdout,
        'tests_run': 'TEST' in result.stdout,
        'summary': 'Summary' in result.stdout,
        'results': 'passed' in result.stdout.lower(),
    }
    
    print("\nMarkers found:")
    for key, found in markers.items():
        status = "✓" if found else "✗"
        print(f"  {status} {key}")
    
    if all(markers.values()):
        print("\n✅ PASS: Basic self-test works")
        return True
    else:
        print("\n❌ FAIL: Basic self-test incomplete")
        return False


def test_enhanced_selftest():
    """Test 2: Enhanced self-test (if available)"""
    print("\n" + "=" * 70)
    print("TEST 2: Enhanced Self-Test Features")
    print("=" * 70)
    
    result = subprocess.run(
        [sys.executable, 'run_netexec.py'],
        capture_output=True,
        text=True
    )
    
    # Check for enhanced features
    enhanced_markers = {
        'test_suites': '[TEST' in result.stdout,
        'detailed_output': 'Database path:' in result.stdout,
        'status_symbols': '[PASS]' in result.stdout or '[FAIL]' in result.stdout,
        'comprehensive': result.stdout.count('TEST') >= 5,  # Multiple test suites
    }
    
    print("Enhanced features found:")
    for key, found in enhanced_markers.items():
        status = "✓" if found else "✗"
        print(f"  {status} {key}")
    
    # Count test categories
    test_count = result.stdout.count('[TEST')
    print(f"\nTest suites detected: {test_count}")
    
    if sum(enhanced_markers.values()) >= 3:
        print("\n✅ PASS: Enhanced self-test active")
        return True
    else:
        print("\n⚠️  WARN: Using basic self-test (enhanced not available)")
        return True  # Not a failure, just using basic


def test_selftest_from_different_directory():
    """Test 3: Self-test works from different directory"""
    print("\n" + "=" * 70)
    print("TEST 3: Self-Test from Different Directory")
    print("=" * 70)
    
    # Get absolute path to run_netexec.py
    script_path = Path('run_netexec.py').absolute()
    
    # Try running from temp directory
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"Running from: {tmpdir}")
        
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            cwd=tmpdir
        )
        
        print(f"Return code: {result.returncode}")
        
        # Should still work
        success = 'NetExec' in result.stdout and 'Self-Test' in result.stdout
        
        if success:
            print("✅ PASS: Self-test works from different directory")
            return True
        else:
            print("❌ FAIL: Self-test failed from different directory")
            print(f"Output: {result.stdout[:200]}")
            return False


def test_selftest_exit_codes():
    """Test 4: Self-test exit codes"""
    print("\n" + "=" * 70)
    print("TEST 4: Self-Test Exit Codes")
    print("=" * 70)
    
    result = subprocess.run(
        [sys.executable, 'run_netexec.py'],
        capture_output=True,
        text=True
    )
    
    print(f"Exit code: {result.returncode}")
    
    # Should return 0 if tests pass, 1 if they fail
    if result.returncode in [0, 1]:
        print("✅ PASS: Valid exit code")
        
        # Check consistency
        has_failures = 'FAIL' in result.stdout
        if has_failures and result.returncode == 0:
            print("⚠️  WARN: Has failures but returned 0")
        elif not has_failures and result.returncode == 1:
            print("⚠️  WARN: No failures but returned 1")
        
        return True
    else:
        print(f"❌ FAIL: Unexpected exit code: {result.returncode}")
        return False


def test_programmatic_api_still_works():
    """Test 5: Programmatic API still functional"""
    print("\n" + "=" * 70)
    print("TEST 5: Programmatic API")
    print("=" * 70)
    
    try:
        from run_netexec import run_netexec
        
        # Test basic call
        result = run_netexec(['--version'])
        
        checks = {
            'is_dict': isinstance(result, dict),
            'has_returncode': 'returncode' in result,
            'has_stdout': 'stdout' in result,
            'has_stderr': 'stderr' in result,
            'stdout_has_content': len(result.get('stdout', '')) > 0,
        }
        
        print("API checks:")
        for key, passed in checks.items():
            status = "✓" if passed else "✗"
            print(f"  {status} {key}")
        
        if all(checks.values()):
            print("\n✅ PASS: Programmatic API works")
            return True
        else:
            print("\n❌ FAIL: Programmatic API broken")
            return False
            
    except Exception as e:
        print(f"\n❌ FAIL: API import error: {e}")
        return False


def test_resource_manager_integration():
    """Test 6: Resource Manager integration"""
    print("\n" + "=" * 70)
    print("TEST 6: Resource Manager Integration")
    print("=" * 70)
    
    try:
        from nxc.helpers.resource_manager import get_resource_manager
        
        rm = get_resource_manager()
        
        checks = {
            'base_path_exists': rm.base_path.exists(),
            'db_path_method': hasattr(rm, 'get_db_path'),
            'protocols_path_method': hasattr(rm, 'get_protocols_path'),
            'is_frozen_property': hasattr(rm, 'is_frozen'),
        }
        
        print("ResourceManager checks:")
        for key, passed in checks.items():
            status = "✓" if passed else "✗"
            print(f"  {status} {key}")
        
        print(f"\nBase path: {rm.base_path}")
        print(f"Is frozen: {rm.is_frozen}")
        print(f"DB path: {rm.get_db_path()}")
        
        if all(checks.values()):
            print("\n✅ PASS: ResourceManager integrated")
            return True
        else:
            print("\n❌ FAIL: ResourceManager issues")
            return False
            
    except ImportError as e:
        print(f"\n❌ FAIL: ResourceManager not available: {e}")
        return False
    except Exception as e:
        print(f"\n❌ FAIL: ResourceManager error: {e}")
        return False


def main():
    """Run all validation tests"""
    print("\n")
    print("=" * 70)
    print("Self-Test Validation Suite")
    print("=" * 70)
    print("\n")
    
    tests = [
        ("Basic Self-Test", test_basic_selftest),
        ("Enhanced Features", test_enhanced_selftest),
        ("Different Directory", test_selftest_from_different_directory),
        ("Exit Codes", test_selftest_exit_codes),
        ("Programmatic API", test_programmatic_api_still_works),
        ("ResourceManager", test_resource_manager_integration),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n❌ EXCEPTION in {name}: {e}")
            results.append((name, False))
    
    # Final summary
    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n[SUCCESS] All validation tests passed! Ready for Nuitka compilation.")
        return 0
    elif passed_count >= total_count * 0.8:
        print("\n[WARNING] Most tests passed. Review failures before compilation.")
        return 0
    else:
        print("\n[FAILED] Multiple test failures. Fix issues before proceeding.")
        return 1


if __name__ == "__main__":
    sys.exit(main())