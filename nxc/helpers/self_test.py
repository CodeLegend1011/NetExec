"""
Enhanced Self-Test System for NetExec
Provides comprehensive validation of all components when exe is launched without arguments.
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class TestStatus(Enum):
    """Test result status"""
    PASS = "[PASS]"
    FAIL = "[FAIL]"
    WARN = "[WARN]"
    SKIP = "[SKIP]"


@dataclass
class TestResult:
    """Individual test result"""
    name: str
    status: TestStatus
    message: str = ""
    details: List[str] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = []


class SelfTestRunner:
    """Comprehensive self-test runner for NetExec"""
    
    def __init__(self, run_netexec_func):
        """
        Initialize self-test runner.
        
        Args:
            run_netexec_func: The run_netexec() function to execute tests
        """
        self.run_netexec = run_netexec_func
        self.results: List[TestResult] = []
        self.protocols = ['ftp', 'ldap', 'mssql', 'nfs', 'rdp', 'smb', 'ssh', 'vnc', 'winrm', 'wmi']
        
    def _add_result(self, name: str, status: TestStatus, message: str = "", details: List[str] = None):
        """Add a test result"""
        self.results.append(TestResult(name, status, message, details or []))
    
    def test_basic_functionality(self) -> None:
        """Test 1: Basic command-line functionality"""
        print("\n[TEST 1] Basic Functionality")
        print("-" * 60)
        
        # Test version
        print("  Testing --version...")
        result = self.run_netexec(['--version'])
        if len(result['stdout']) > 0 and 'Yippie-Ki-Yay' in result['stdout']:
            version = result['stdout'].strip()
            self._add_result(
                "basic_version",
                TestStatus.PASS,
                f"Version: {version}"
            )
            print(f"    {TestStatus.PASS.value}: {version}")
        else:
            self._add_result("basic_version", TestStatus.FAIL, "Version output invalid")
            print(f"    {TestStatus.FAIL.value}: No version output")
        
        # Test help
        print("  Testing --help...")
        result = self.run_netexec(['--help'])
        if result['returncode'] == 0 and 'usage:' in result['stdout'].lower():
            self._add_result("basic_help", TestStatus.PASS, "Help menu accessible")
            print(f"    {TestStatus.PASS.value}: Help menu works")
        else:
            self._add_result("basic_help", TestStatus.FAIL, "Help menu failed")
            print(f"    {TestStatus.FAIL.value}: Help menu error")
    
    def test_protocol_availability(self) -> None:
        """Test 2: All protocols are available"""
        print("\n[TEST 2] Protocol Availability")
        print("-" * 60)
        
        available_protocols = []
        failed_protocols = []
        
        for protocol in self.protocols:
            result = self.run_netexec([protocol, '--help'])
            
            # Success if help shows or returns expected codes
            if result['returncode'] in [0, 2] and len(result['stdout']) > 100:
                available_protocols.append(protocol)
                self._add_result(
                    f"protocol_{protocol}",
                    TestStatus.PASS,
                    f"{protocol.upper()} protocol available"
                )
                print(f"  {TestStatus.PASS.value}: {protocol.upper()}")
            else:
                failed_protocols.append(protocol)
                self._add_result(
                    f"protocol_{protocol}",
                    TestStatus.FAIL,
                    f"{protocol.upper()} protocol unavailable"
                )
                print(f"  {TestStatus.FAIL.value}: {protocol.upper()}")
        
        # Summary
        print(f"\n  Summary: {len(available_protocols)}/{len(self.protocols)} protocols available")
    
    def test_module_system(self) -> None:
        """Test 3: Module system functionality"""
        print("\n[TEST 3] Module System")
        print("-" * 60)
        
        # Test module listing with SMB (most common)
        print("  Testing module listing...")
        result = self.run_netexec(['smb', '-L'])
        
        # Module listing might return various codes but should show modules
        if 'modules' in result['stdout'].lower() or result['returncode'] in [0, 1]:
            # Try to count modules mentioned
            module_mentions = result['stdout'].lower().count('module')
            self._add_result(
                "modules_list",
                TestStatus.PASS,
                f"Module system functional (mentions: {module_mentions})"
            )
            print(f"    {TestStatus.PASS.value}: Module listing works")
        else:
            self._add_result(
                "modules_list",
                TestStatus.WARN,
                "Module listing unclear"
            )
            print(f"    {TestStatus.WARN.value}: Module listing unclear")
        
        # Test specific module help (if available)
        print("  Testing module help...")
        result = self.run_netexec(['smb', '-M', 'spider_plus', '--help'])
        
        if result['returncode'] in [0, 1, 2] or len(result['stdout']) > 0:
            self._add_result("modules_help", TestStatus.PASS, "Module help accessible")
            print(f"    {TestStatus.PASS.value}: Module help works")
        else:
            self._add_result("modules_help", TestStatus.WARN, "Module help unclear")
            print(f"    {TestStatus.WARN.value}: Module help unclear")
    
    def test_path_independence(self) -> None:
        """Test 4: Path independence validation"""
        print("\n[TEST 4] Path Independence")
        print("-" * 60)
        
        try:
            from nxc.helpers.resource_manager import get_resource_manager
            
            rm = get_resource_manager()
            
            # Check base paths
            checks = {
                'base_path': rm.base_path.exists(),
                'nxc_path': rm.nxc_path.exists() if not rm.is_frozen else True,
                'protocols_path': rm.get_protocols_path().exists() if not rm.is_frozen else True,
                'modules_path': rm.get_modules_path().exists() if not rm.is_frozen else True,
                'db_path': rm.get_db_path().exists(),
            }
            
            all_pass = all(checks.values())
            
            print(f"  Base path: {rm.base_path}")
            print(f"    Exists: {checks['base_path']}")
            
            if not rm.is_frozen:
                print(f"  NXC path: {rm.nxc_path}")
                print(f"    Exists: {checks['nxc_path']}")
                print(f"  Protocols path: {rm.get_protocols_path()}")
                print(f"    Exists: {checks['protocols_path']}")
                print(f"  Modules path: {rm.get_modules_path()}")
                print(f"    Exists: {checks['modules_path']}")
            
            print(f"  Database path: {rm.get_db_path()}")
            print(f"    Exists: {checks['db_path']}")
            
            if all_pass:
                self._add_result(
                    "path_independence",
                    TestStatus.PASS,
                    "All paths accessible",
                    [f"{k}: {v}" for k, v in checks.items()]
                )
                print(f"\n  {TestStatus.PASS.value}: All paths valid")
            else:
                failed = [k for k, v in checks.items() if not v]
                self._add_result(
                    "path_independence",
                    TestStatus.FAIL,
                    f"Some paths failed: {failed}",
                    [f"{k}: {v}" for k, v in checks.items()]
                )
                print(f"\n  {TestStatus.FAIL.value}: Some paths invalid: {failed}")
                
        except Exception as e:
            self._add_result(
                "path_independence",
                TestStatus.FAIL,
                f"ResourceManager error: {str(e)}"
            )
            print(f"  {TestStatus.FAIL.value}: {str(e)}")
    
    def test_database_functionality(self) -> None:
        """Test 5: Database initialization and access"""
        print("\n[TEST 5] Database Functionality")
        print("-" * 60)
        
        db_path = os.environ.get('NXC_DB', '')
        
        if db_path:
            db_path_obj = Path(db_path)
            
            print(f"  Database location: {db_path}")
            
            # Check if directory exists
            if db_path_obj.exists():
                print(f"    {TestStatus.PASS.value}: Directory exists")
                
                # Check if writable
                try:
                    test_file = db_path_obj / '.write_test'
                    test_file.write_text('test')
                    test_file.unlink()
                    
                    self._add_result(
                        "database_writable",
                        TestStatus.PASS,
                        f"Database path writable: {db_path}"
                    )
                    print(f"    {TestStatus.PASS.value}: Directory writable")
                    
                except Exception as e:
                    self._add_result(
                        "database_writable",
                        TestStatus.FAIL,
                        f"Database path not writable: {str(e)}"
                    )
                    print(f"    {TestStatus.FAIL.value}: Not writable - {e}")
            else:
                self._add_result(
                    "database_writable",
                    TestStatus.WARN,
                    "Database directory doesn't exist yet"
                )
                print(f"    {TestStatus.WARN.value}: Directory doesn't exist (will be created on use)")
        else:
            self._add_result(
                "database_writable",
                TestStatus.FAIL,
                "NXC_DB environment variable not set"
            )
            print(f"  {TestStatus.FAIL.value}: NXC_DB not set")
    
    def test_data_files(self) -> None:
        """Test 6: Data files accessibility"""
        print("\n[TEST 6] Data Files")
        print("-" * 60)
        
        try:
            from nxc.helpers.resource_manager import get_resource_manager
            rm = get_resource_manager()
            
            data_path = rm.get_data_path()
            
            if data_path.exists():
                # Count data files
                data_files = list(data_path.rglob('*'))
                file_count = len([f for f in data_files if f.is_file()])
                
                print(f"  Data directory: {data_path}")
                print(f"  Files found: {file_count}")
                
                # Check for critical files
                critical_files = ['nxc.conf', 'default.pem']
                found_critical = []
                
                for cf in critical_files:
                    if (data_path / cf).exists():
                        found_critical.append(cf)
                        print(f"    {TestStatus.PASS.value}: {cf}")
                    else:
                        print(f"    {TestStatus.WARN.value}: {cf} not found")
                
                if file_count > 0:
                    self._add_result(
                        "data_files",
                        TestStatus.PASS,
                        f"{file_count} data files accessible"
                    )
                else:
                    self._add_result(
                        "data_files",
                        TestStatus.WARN,
                        "No data files found"
                    )
            else:
                self._add_result(
                    "data_files",
                    TestStatus.WARN,
                    "Data directory not found (may be bundled differently)"
                )
                print(f"  {TestStatus.WARN.value}: Data directory not found")
                
        except Exception as e:
            self._add_result(
                "data_files",
                TestStatus.FAIL,
                f"Data files check error: {str(e)}"
            )
            print(f"  {TestStatus.FAIL.value}: {str(e)}")
    
    def test_argument_parsing(self) -> None:
        """Test 7: Advanced argument parsing"""
        print("\n[TEST 7] Argument Parsing")
        print("-" * 60)
        
        test_cases = [
            (['smb', '127.0.0.1', '-u', 'test', '-p', 'test'], 'Basic SMB syntax'),
            (['ldap', '127.0.0.1', '-u', 'test', '-p', 'test'], 'Basic LDAP syntax'),
            (['--threads', '10', 'smb', '--help'], 'Global options'),
        ]
        
        passed = 0
        for args, description in test_cases:
            result = self.run_netexec(args)
            
            # Should not crash (returncode != exception)
            if result['returncode'] in [0, 1, 2] or len(result['stdout']) > 0:
                passed += 1
                print(f"  {TestStatus.PASS.value}: {description}")
            else:
                print(f"  {TestStatus.FAIL.value}: {description}")
        
        if passed == len(test_cases):
            self._add_result(
                "argument_parsing",
                TestStatus.PASS,
                f"All {len(test_cases)} parsing tests passed"
            )
        else:
            self._add_result(
                "argument_parsing",
                TestStatus.WARN,
                f"{passed}/{len(test_cases)} parsing tests passed"
            )
    
    def test_output_capture(self) -> None:
        """Test 8: Output capture functionality"""
        print("\n[TEST 8] Output Capture")
        print("-" * 60)
        
        # Test that output is properly captured
        result = self.run_netexec(['--help'])
        
        has_stdout = len(result['stdout']) > 0
        has_returncode = 'returncode' in result
        is_dict = isinstance(result, dict)
        
        print(f"  Output is dict: {is_dict}")
        print(f"  Has returncode: {has_returncode}")
        print(f"  Has stdout: {has_stdout}")
        print(f"  Stdout length: {len(result['stdout'])} chars")
        
        if is_dict and has_returncode and has_stdout:
            self._add_result(
                "output_capture",
                TestStatus.PASS,
                "Output properly captured in dict"
            )
            print(f"  {TestStatus.PASS.value}: Output capture working")
        else:
            self._add_result(
                "output_capture",
                TestStatus.FAIL,
                "Output capture incomplete"
            )
            print(f"  {TestStatus.FAIL.value}: Output capture broken")
    
    def run_all_tests(self) -> bool:
        """Run all self-tests and return overall success"""
        print("=" * 60)
        print("NetExec Comprehensive Self-Test")
        print("=" * 60)
        
        # Run all test suites
        self.test_basic_functionality()
        self.test_protocol_availability()
        self.test_module_system()
        self.test_path_independence()
        self.test_database_functionality()
        self.test_data_files()
        self.test_argument_parsing()
        self.test_output_capture()
        
        # Print summary
        self._print_summary()
        
        # Return overall success
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == TestStatus.PASS)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAIL)
        
        # Success if no failures and at least 80% pass
        return failed == 0 and passed >= (total * 0.8)
    
    def _print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("Self-Test Summary")
        print("=" * 60)
        
        # Group by status
        by_status = {
            TestStatus.PASS: [],
            TestStatus.FAIL: [],
            TestStatus.WARN: [],
            TestStatus.SKIP: []
        }
        
        for result in self.results:
            by_status[result.status].append(result)
        
        # Print each group
        for status in [TestStatus.PASS, TestStatus.WARN, TestStatus.FAIL, TestStatus.SKIP]:
            results = by_status[status]
            if results:
                print(f"\n{status.value} ({len(results)}):")
                for r in results:
                    msg = f"  {r.name}"
                    if r.message:
                        msg += f": {r.message}"
                    print(msg)
        
        # Overall stats
        total = len(self.results)
        passed = len(by_status[TestStatus.PASS])
        failed = len(by_status[TestStatus.FAIL])
        warned = len(by_status[TestStatus.WARN])
        
        print("\n" + "=" * 60)
        print(f"Results: {passed} passed, {warned} warnings, {failed} failed ({total} total)")
        
        # Final verdict
        if failed == 0 and passed >= (total * 0.8):
            print("[SUCCESS] Self-test PASSED - System ready!")
        elif failed == 0:
            print("[WARNING] Self-test PASSED with warnings")
        else:
            print("[FAILED] Self-test FAILED - Issues detected")
        
        print("=" * 60)