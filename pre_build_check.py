"""
Pre-Build Environment Checker
Validates that everything is ready for Nuitka compilation.
"""

import sys
import subprocess
import os
from pathlib import Path


def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def check_python():
    """Check Python version"""
    print("\n[CHECK 1] Python Version")
    version = sys.version_info
    
    print(f"  Python: {version.major}.{version.minor}.{version.micro}")
    print(f"  Path: {sys.executable}")
    
    if version >= (3, 7):
        print("  Status: OK (3.7+ required)")
        return True
    else:
        print("  Status: FAIL (need Python 3.7+)")
        return False


def check_nuitka():
    """Check Nuitka installation"""
    print("\n[CHECK 2] Nuitka")
    
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'nuitka', '--version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            version = result.stdout.strip().split('\n')[0]
            print(f"  Installed: {version}")
            print("  Status: OK")
            return True
        else:
            print("  Installed: No")
            print("  Status: FAIL")
            print("  Fix: pip install nuitka")
            return False
            
    except FileNotFoundError:
        print("  Installed: No")
        print("  Status: FAIL")
        print("  Fix: pip install nuitka")
        return False
    except Exception as e:
        print(f"  Error: {e}")
        print("  Status: FAIL")
        return False


def check_msvc():
    """Check MSVC compiler"""
    print("\n[CHECK 3] MSVC Compiler")
    
    # Check for cl.exe
    try:
        result = subprocess.run(
            ['where', 'cl.exe'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            path = result.stdout.strip().split('\n')[0]
            print(f"  Found: {path}")
            print("  Status: OK")
            return True
        else:
            print("  Found: No")
            print("  Status: FAIL")
            print_msvc_help()
            return False
            
    except Exception as e:
        print(f"  Error: {e}")
        print("  Status: WARN (could not verify)")
        print_msvc_help()
        return False


def print_msvc_help():
    """Print help for installing MSVC"""
    print("\n  How to fix:")
    print("  1. Install Visual Studio Build Tools 2022")
    print("     https://visualstudio.microsoft.com/downloads/")
    print("  2. Select 'Desktop development with C++'")
    print("  3. Run from 'x64 Native Tools Command Prompt'")
    print("     OR")
    print("  4. Run vcvarsall.bat before building:")
    print('     "C:\\Program Files\\...\\vcvarsall.bat" x64')


def check_repo_structure():
    """Check repository structure"""
    print("\n[CHECK 4] Repository Structure")
    
    cwd = Path.cwd()
    print(f"  Current directory: {cwd}")
    
    required_files = {
        'run_netexec.py': 'Entry point',
        'nxc': 'NetExec package',
        'nxc/protocols': 'Protocol modules',
        'nxc/modules': 'Extension modules',
        'nxc/helpers/self_test.py': 'Self-test module',
        'nxc/helpers/resource_manager.py': 'Path manager',
    }
    
    all_ok = True
    
    for path, description in required_files.items():
        path_obj = cwd / path
        exists = path_obj.exists()
        
        status = "OK" if exists else "MISSING"
        print(f"  [{status:7}] {path:40} ({description})")
        
        if not exists:
            all_ok = False
    
    if all_ok:
        print("  Status: OK")
    else:
        print("  Status: FAIL (missing required files)")
    
    return all_ok


def check_dependencies():
    """Check Python dependencies"""
    print("\n[CHECK 5] Python Dependencies")
    
    # Try importing critical modules
    imports = {
        'nxc': 'NetExec package',
        'nxc.netexec': 'NetExec main',
        'nxc.helpers.resource_manager': 'Resource manager',
        'nxc.helpers.self_test': 'Self-test system',
    }
    
    all_ok = True
    
    for module, description in imports.items():
        try:
            __import__(module)
            print(f"  [OK     ] {module:30} ({description})")
        except ImportError as e:
            print(f"  [FAIL   ] {module:30} ({description})")
            print(f"            Error: {e}")
            all_ok = False
    
    if all_ok:
        print("  Status: OK")
    else:
        print("  Status: FAIL")
        print("  Fix: pip install -e .")
    
    return all_ok


def check_disk_space():
    """Check available disk space"""
    print("\n[CHECK 6] Disk Space")
    
    cwd = Path.cwd()
    
    try:
        import shutil
        total, used, free = shutil.disk_usage(cwd)
        
        free_gb = free / (1024**3)
        print(f"  Free space: {free_gb:.1f} GB")
        
        if free_gb >= 2:
            print("  Status: OK (2+ GB recommended)")
            return True
        else:
            print("  Status: WARN (less than 2 GB free)")
            return True  # Warning, not failure
            
    except Exception as e:
        print(f"  Error: {e}")
        print("  Status: WARN (could not check)")
        return True


def check_previous_builds():
    """Check for previous build artifacts"""
    print("\n[CHECK 7] Previous Builds")
    
    cwd = Path.cwd()
    dist_dir = cwd / 'dist'
    build_dir = cwd / 'build'
    
    if dist_dir.exists():
        files = list(dist_dir.iterdir())
        print(f"  dist/ exists with {len(files)} files")
        print("  Note: Will be cleaned before build")
    else:
        print("  dist/ does not exist (clean)")
    
    if build_dir.exists():
        print("  build/ exists")
        print("  Note: Will be cleaned before build")
    else:
        print("  build/ does not exist (clean)")
    
    print("  Status: OK")
    return True


def test_import_run_netexec():
    """Test if run_netexec.py can be imported"""
    print("\n[CHECK 8] run_netexec.py Import Test")
    
    try:
        # Add current directory to path
        cwd = Path.cwd()
        if str(cwd) not in sys.path:
            sys.path.insert(0, str(cwd))
        
        # Try importing
        from run_netexec import run_netexec, self_test
        
        print("  Import: OK")
        
        # Try a quick test
        result = run_netexec(['--version'])
        
        if isinstance(result, dict) and 'returncode' in result:
            print("  API function: OK")
            print(f"  Version output: {result['stdout'].strip()[:50]}...")
            return True
        else:
            print("  API function: FAIL (unexpected return type)")
            return False
            
    except Exception as e:
        print(f"  Error: {e}")
        print("  Status: FAIL")
        import traceback
        traceback.print_exc()
        return False


def print_summary(results):
    """Print summary of all checks"""
    print_section("Pre-Build Check Summary")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    for check, result in results.items():
        status = "[OK]  " if result else "[FAIL]"
        print(f"  {status} {check}")
    
    print(f"\n  Total: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n  Status: READY TO BUILD")
        print("  Next: python build_nuitka.py")
        return True
    else:
        print(f"\n  Status: NOT READY ({failed} issues)")
        print("  Fix the failed checks above before building")
        return False


def main():
    """Run all checks"""
    print("\n")
    print("=" * 70)
    print(" " * 20 + "NetExec Pre-Build Checker")
    print("=" * 70)
    
    results = {
        'Python Version': check_python(),
        'Nuitka Installation': check_nuitka(),
        'MSVC Compiler': check_msvc(),
        'Repository Structure': check_repo_structure(),
        'Python Dependencies': check_dependencies(),
        'Disk Space': check_disk_space(),
        'Previous Builds': check_previous_builds(),
        'Import Test': test_import_run_netexec(),
    }
    
    ready = print_summary(results)
    
    if ready:
        print("\n" + "=" * 70)
        print("Ready to build! Run:")
        print("  python build_nuitka.py")
        print("=" * 70)
        return 0
    else:
        print("\n" + "=" * 70)
        print("Fix the issues above, then run this check again")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())