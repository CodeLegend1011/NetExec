"""
Test script for run_netexec() API
This demonstrates that the function captures output correctly.
"""

from run_netexec import run_netexec
import json


def test_help():
    """Test help command"""
    print("=" * 60)
    print("TEST 1: Help Command")
    print("=" * 60)
    
    result = run_netexec(['--help'])
    
    print(f"Return Code: {result['returncode']}")
    print(f"Stdout Length: {len(result['stdout'])} chars")
    print(f"Stderr Length: {len(result['stderr'])} chars")
    print("\nCaptured Output:")
    print(result['stdout'][:500])  # Print first 500 chars
    print("\n")


def test_version():
    """Test version command"""
    print("=" * 60)
    print("TEST 2: Version Command")
    print("=" * 60)
    
    result = run_netexec(['--version'])
    
    print(f"Return Code: {result['returncode']}")
    print(f"Output: {result['stdout'].strip()}")
    print("\n")


def test_protocol_help():
    """Test protocol help"""
    print("=" * 60)
    print("TEST 3: SMB Protocol Help")
    print("=" * 60)
    
    result = run_netexec(['smb', '--help'])
    
    print(f"Return Code: {result['returncode']}")
    print(f"Stdout Length: {len(result['stdout'])} chars")
    print(f"First 300 chars:\n{result['stdout'][:300]}")
    print("\n")


def test_invalid_command():
    """Test invalid command handling"""
    print("=" * 60)
    print("TEST 4: Invalid Command")
    print("=" * 60)
    
    result = run_netexec(['invalid_protocol'])
    
    print(f"Return Code: {result['returncode']}")
    print(f"Stderr: {result['stderr'][:200]}")
    print("\n")


def test_json_output():
    """Test that we can serialize the result"""
    print("=" * 60)
    print("TEST 5: JSON Serialization")
    print("=" * 60)
    
    result = run_netexec(['--version'])
    
    try:
        json_str = json.dumps(result, indent=2)
        print("✓ Result is JSON serializable")
        print(f"JSON output:\n{json_str}")
    except Exception as e:
        print(f"✗ JSON serialization failed: {e}")
    
    print("\n")


if __name__ == "__main__":
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "NetExec API Tests" + " " * 25 + "║")
    print("╚" + "═" * 58 + "╝")
    print("\n")
    
    test_help()
    test_version()
    test_protocol_help()
    test_invalid_command()
    test_json_output()
    
    print("=" * 60)
    print("All tests completed!")
    print("=" * 60)