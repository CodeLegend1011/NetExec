"""
NetExec Programmatic API Entrypoint with Path Independence
This module provides a clean API for running NetExec programmatically
and captures output without stdout pollution.

CORRECTED VERSION - Properly handles path independence
"""

import sys
import io
import os
from contextlib import contextmanager
from typing import Dict, List
from pathlib import Path
import traceback


def initialize_path_independence():
    """
    Initialize paths before NetExec loads.
    Ensures NetExec works from any directory.
    """
    try:
        is_frozen = getattr(sys, 'frozen', False)
        
        if is_frozen:
            if hasattr(sys, '_MEIPASS'):
                base_path = Path(sys._MEIPASS)
            else:
                base_path = Path(sys.executable).parent
            
            if str(base_path) not in sys.path:
                sys.path.insert(0, str(base_path))
        else:
            try:
                import nxc
                base_path = Path(nxc.__file__).parent.parent
                
                if str(base_path) not in sys.path:
                    sys.path.insert(0, str(base_path))
                    
            except ImportError:
                script_path = Path(__file__).parent
                
                if (script_path / 'nxc').exists():
                    base_path = script_path
                    if str(base_path) not in sys.path:
                        sys.path.insert(0, str(base_path))
                else:
                    print(f"Warning: Could not locate nxc module. Script at: {script_path}", 
                          file=sys.stderr)
            
    except Exception as e:
        print(f"Warning: Path initialization issue: {e}", file=sys.stderr)
        traceback.print_exc()


# Initialize before any NetExec imports
initialize_path_independence()


@contextmanager
def capture_output():
    """Context manager to capture stdout and stderr"""
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    
    try:
        sys.stdout = stdout_capture
        sys.stderr = stderr_capture
        yield stdout_capture, stderr_capture
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr


def run_netexec(args: List[str]) -> Dict:
    """
    Runs netexec with the given CLI args and returns output in structured form.
    
    Args:
        args: List of command-line arguments (e.g., ['smb', '192.168.1.1', '-u', 'admin'])
    
    Returns:
        dict: {
            "returncode": int,
            "stdout": str,
            "stderr": str,
            "parsed": dict (optional)
        }
    
    Example:
        result = run_netexec(['--help'])
        print(result['stdout'])
    """
    result = {
        "returncode": 0,
        "stdout": "",
        "stderr": "",
        "parsed": {}
    }
    
    # Save original argv
    original_argv = sys.argv.copy()
    
    try:
        # Set up arguments for NetExec
        sys.argv = ['netexec'] + args
        
        # Capture output
        with capture_output() as (stdout_capture, stderr_capture):
            try:
                # Import and run NetExec's main function
                from nxc.netexec import main
                
                # Execute NetExec
                exit_code = main()
                result["returncode"] = exit_code if exit_code is not None else 0
                
            except SystemExit as e:
                # NetExec might call sys.exit()
                result["returncode"] = e.code if isinstance(e.code, int) else (1 if e.code else 0)
            except Exception as e:
                result["returncode"] = 1
                result["stderr"] += f"\nException: {str(e)}\n{traceback.format_exc()}"
        
        # Get captured output
        result["stdout"] = stdout_capture.getvalue()
        result["stderr"] = stderr_capture.getvalue()
        
    except Exception as e:
        result["returncode"] = 1
        result["stderr"] = f"Fatal error: {str(e)}\n{traceback.format_exc()}"
    finally:
        # Restore original argv
        sys.argv = original_argv
    
    return result


def self_test() -> bool:
    """
    Run comprehensive self-test checks for NetExec.
    Returns True if all tests pass, False otherwise.
    """
    try:
        # Use enhanced self-test if available
        from nxc.helpers.self_test import SelfTestRunner
        
        runner = SelfTestRunner(run_netexec)
        return runner.run_all_tests()
        
    except ImportError:
        # Fallback to basic self-test if enhanced version not available
        print("=" * 60)
        print("NetExec Basic Self-Test Mode")
        print("(Enhanced self-test not available)")
        print("=" * 60)
        print()
        
        protocols = ['ftp', 'ldap', 'mssql', 'nfs', 'rdp', 'smb', 'ssh', 'vnc', 'winrm', 'wmi']
        test_results = {}
        
        # Test 1: Version check
        print("[TEST] Version check...")
        result = run_netexec(['--version'])
        version_pass = len(result['stdout']) > 0
        test_results['version'] = version_pass
        print(f"  {'✓ PASS' if version_pass else '✗ FAIL'}: Version check")
        if version_pass:
            print(f"  Version: {result['stdout'].strip()}")
        print()
        
        # Test 2: Help check
        print("[TEST] Help menu...")
        result = run_netexec(['--help'])
        help_pass = result['returncode'] == 0 and 'usage:' in result['stdout'].lower()
        test_results['help'] = help_pass
        print(f"  {'✓ PASS' if help_pass else '✗ FAIL'}: Help menu")
        print()
        
        # Test 3: Protocol help checks
        print("[TEST] Protocol availability...")
        for protocol in protocols:
            result = run_netexec([protocol, '--help'])
            protocol_pass = result['returncode'] in [0, 2] and len(result['stdout']) > 100
            test_results[f'protocol_{protocol}'] = protocol_pass
            status = '✓ PASS' if protocol_pass else '✗ FAIL'
            print(f"  {status}: {protocol.upper()} protocol")
        
        print()
        print("=" * 60)
        print(f"Results: {sum(test_results.values())}/{len(test_results)} tests passed")
        print("=" * 60)
        
        return all(test_results.values())


def main():
    """
    Main entrypoint when the exe is launched directly.
    Runs self-test mode or accepts CLI arguments.
    """
    # If no arguments provided, run self-test
    if len(sys.argv) == 1:
        print("No arguments provided. Running self-test mode...\n")
        success = self_test()
        sys.exit(0 if success else 1)
    else:
        # Run NetExec with provided arguments
        args = sys.argv[1:]
        result = run_netexec(args)
        
        # Print output
        if result['stdout']:
            print(result['stdout'], end='')
        if result['stderr']:
            print(result['stderr'], end='', file=sys.stderr)
        
        sys.exit(result['returncode'])


if __name__ == "__main__":
    main()