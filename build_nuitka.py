"""
Nuitka Build Script for NetExec
Compiles NetExec into a single-file Windows executable.
"""

import subprocess
import sys
import os
from pathlib import Path
import shutil


class NuitkaBuilder:
    """Handles the Nuitka compilation process"""
    
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.nxc_path = repo_root / 'nxc'
        self.output_dir = repo_root / 'dist'
        self.build_dir = repo_root / 'build'
        
    def check_prerequisites(self):
        """Check if all prerequisites are met"""
        print("=" * 70)
        print("Checking Build Prerequisites")
        print("=" * 70)
        
        checks = {}
        
        # Check Python version
        print("\n[1/6] Python Version...")
        python_version = sys.version_info
        if python_version >= (3, 7):
            print(f"  ✓ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
            checks['python'] = True
        else:
            print(f"  ✗ Python {python_version.major}.{python_version.minor} (need 3.7+)")
            checks['python'] = False
        
        # Check Nuitka
        print("\n[2/6] Nuitka Installation...")
        try:
            result = subprocess.run([sys.executable, '-m', 'nuitka', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.strip().split('\n')[0]  # Get first line
                print(f"  ✓ Nuitka installed: {version}")
                checks['nuitka'] = True
            else:
                print(f"  ✗ Nuitka not working (return code: {result.returncode})")
                if result.stderr:
                    print(f"    Error: {result.stderr.strip()}")
                checks['nuitka'] = False
        except Exception as e:
            print(f"  ✗ Nuitka not installed: {e}")
            print(f"  Install with: pip install nuitka")
            checks['nuitka'] = False
        
        # Check MSVC (required for Nuitka on Windows)
        print("\n[3/6] MSVC Compiler...")
        try:
            # Try to find cl.exe
            result = subprocess.run(['where', 'cl.exe'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"  ✓ MSVC found: {result.stdout.strip()}")
                checks['msvc'] = True
            else:
                print(f"  ⚠ MSVC not in PATH")
                print(f"  Run this from 'x64 Native Tools Command Prompt for VS'")
                print(f"  Or install Visual Studio Build Tools")
                checks['msvc'] = False
        except Exception as e:
            print(f"  ⚠ Could not check MSVC: {e}")
            checks['msvc'] = False
        
        # Check run_netexec.py
        print("\n[4/6] run_netexec.py...")
        if (self.repo_root / 'run_netexec.py').exists():
            print(f"  ✓ Found run_netexec.py")
            checks['entrypoint'] = True
        else:
            print(f"  ✗ run_netexec.py not found")
            checks['entrypoint'] = False
        
        # Check nxc directory
        print("\n[5/6] NetExec Package...")
        if self.nxc_path.exists():
            protocol_count = len(list((self.nxc_path / 'protocols').glob('*.py'))) if (self.nxc_path / 'protocols').exists() else 0
            module_count = len(list((self.nxc_path / 'modules').glob('*.py'))) if (self.nxc_path / 'modules').exists() else 0
            print(f"  ✓ nxc package found")
            print(f"    Protocols: {protocol_count}")
            print(f"    Modules: {module_count}")
            checks['nxc'] = True
        else:
            print(f"  ✗ nxc directory not found")
            checks['nxc'] = False
        
        # Check data files
        print("\n[6/6] Data Files...")
        data_path = self.nxc_path / 'data'
        if data_path.exists():
            data_files = list(data_path.rglob('*.*'))
            print(f"  ✓ Data directory found: {len(data_files)} files")
            checks['data'] = True
        else:
            print(f"  ⚠ Data directory not found (may not be critical)")
            checks['data'] = True  # Not critical
        
        # Summary
        print("\n" + "=" * 70)
        passed = sum(1 for v in checks.values() if v)
        total = len(checks)
        
        if passed == total:
            print(f"✓ All prerequisites met ({passed}/{total})")
            return True
        else:
            print(f"✗ Missing prerequisites ({passed}/{total})")
            failed = [k for k, v in checks.items() if not v]
            print(f"  Failed: {', '.join(failed)}")
            return False
    
    def get_nuitka_command(self):
        """Build the Nuitka compilation command"""
        
        cmd = [
            sys.executable, '-m', 'nuitka',
            
            # Main options
            '--standalone',              # Create standalone distribution
            '--onefile',                 # Pack everything into single exe
            '--assume-yes-for-downloads', # Auto-download dependencies
            
            # Windows specific
            '--windows-console-mode=force',  # Keep console window
            
            # Performance
            '--lto=no',                 # Link-time optimization disabled
            
            # Include packages
            '--include-package=nxc',     # Include entire nxc package
            
            # Include data directories
            f'--include-data-dir={self.nxc_path / "protocols"}=nxc/protocols',
            f'--include-data-dir={self.nxc_path / "modules"}=nxc/modules',
        ]
        
        # Include data directory if it exists
        data_dir = self.nxc_path / 'data'
        if data_dir.exists():
            cmd.append(f'--include-data-dir={data_dir}=nxc/data')
        
        # Additional data directories (if they exist)
        for subdir in ['loaders', 'helpers']:
            subdir_path = self.nxc_path / subdir
            if subdir_path.exists():
                cmd.append(f'--include-package=nxc.{subdir}')
        
        # Output configuration
        cmd.extend([
            '--output-dir=dist',
            '--output-filename=netexec.exe',
            
            # The entry point
            'run_netexec.py'
        ])
        
        return cmd
    
    def clean_build_artifacts(self):
        """Clean previous build artifacts"""
        print("\n" + "=" * 70)
        print("Cleaning Build Artifacts")
        print("=" * 70)
        
        dirs_to_clean = [self.build_dir, self.output_dir]
        
        for dir_path in dirs_to_clean:
            if dir_path.exists():
                print(f"  Removing {dir_path}...")
                try:
                    shutil.rmtree(dir_path)
                    print(f"  ✓ Cleaned {dir_path}")
                except Exception as e:
                    print(f"  ✗ Failed to clean {dir_path}: {e}")
        
        print()
    
    def build(self, clean=True):
        """Run the Nuitka build"""
        
        if clean:
            self.clean_build_artifacts()
        
        print("=" * 70)
        print("Starting Nuitka Compilation")
        print("=" * 70)
        print("\nThis will take 5-15 minutes depending on your system...")
        print("You'll see a lot of output - this is normal!")
        print()
        
        cmd = self.get_nuitka_command()
        
        # Print the command
        print("Build Command:")
        print("-" * 70)
        for i, part in enumerate(cmd):
            if i == 0:
                print(f"{part} \\")
            elif i < len(cmd) - 1:
                print(f"  {part} \\")
            else:
                print(f"  {part}")
        print("-" * 70)
        print()
        
        # Run Nuitka
        try:
            result = subprocess.run(cmd, cwd=self.repo_root)
            
            if result.returncode == 0:
                print("\n" + "=" * 70)
                print("✓ Build Successful!")
                print("=" * 70)
                
                # Check output file
                exe_path = self.output_dir / 'netexec.exe'
                if exe_path.exists():
                    size_mb = exe_path.stat().st_size / (1024 * 1024)
                    print(f"\nExecutable created: {exe_path}")
                    print(f"Size: {size_mb:.1f} MB")
                    return True
                else:
                    print("\n⚠ Build succeeded but exe not found at expected location")
                    print(f"Expected: {exe_path}")
                    return False
            else:
                print("\n" + "=" * 70)
                print("✗ Build Failed!")
                print("=" * 70)
                print(f"Exit code: {result.returncode}")
                return False
                
        except KeyboardInterrupt:
            print("\n\nBuild interrupted by user")
            return False
        except Exception as e:
            print(f"\n✗ Build error: {e}")
            return False
    
    def test_exe(self):
        """Test the compiled executable"""
        exe_path = self.output_dir / 'netexec.exe'
        
        if not exe_path.exists():
            print(f"✗ Executable not found: {exe_path}")
            return False
        
        print("\n" + "=" * 70)
        print("Testing Compiled Executable")
        print("=" * 70)
        
        tests = [
            (['--version'], 'Version check'),
            (['--help'], 'Help menu'),
            ([], 'Self-test mode'),
        ]
        
        for args, description in tests:
            print(f"\nTest: {description}")
            print(f"Command: netexec.exe {' '.join(args)}")
            
            try:
                result = subprocess.run(
                    [str(exe_path)] + args,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if args == []:  # Self-test
                    # Check for comprehensive test
                    if 'Comprehensive Self-Test' in result.stdout:
                        print(f"  ✓ Self-test runs")
                        if 'Self-test PASSED' in result.stdout or result.returncode == 0:
                            print(f"  ✓ Self-test PASSED")
                        else:
                            print(f"  ⚠ Self-test completed with warnings")
                    else:
                        print(f"  ⚠ Self-test output unclear")
                elif result.returncode in [0, 1]:  # Version returns 1, help returns 0
                    print(f"  ✓ {description} works")
                    if args == ['--version']:
                        print(f"    Output: {result.stdout.strip()}")
                else:
                    print(f"  ✗ {description} failed")
                    print(f"    Return code: {result.returncode}")
                    
            except subprocess.TimeoutExpired:
                print(f"  ✗ {description} timed out")
            except Exception as e:
                print(f"  ✗ {description} error: {e}")
        
        print()
        return True


def main():
    """Main build function"""
    print("\n")
    print("=" * 70)
    print(" " * 20 + "NetExec Nuitka Builder" + " " * 26)
    print("=" * 70)
    print("\n")
    
    # Find repo root
    repo_root = Path.cwd()
    if not (repo_root / 'nxc').exists():
        print("Error: Not in NetExec repository root")
        print("Please run this from E:\\BugBase\\NetExec")
        return 1
    
    builder = NuitkaBuilder(repo_root)
    
    # Check prerequisites
    if not builder.check_prerequisites():
        print("\n⚠ Prerequisites not met. Please fix the issues above.")
        print("\nCommon fixes:")
        print("  - Install Nuitka: pip install nuitka")
        print("  - Install MSVC: Download Visual Studio Build Tools")
        print("  - Run from 'x64 Native Tools Command Prompt for VS'")
        return 1
    
    # Build
    print("\nReady to build. Press Ctrl+C to cancel...")
    import time
    time.sleep(2)
    
    success = builder.build(clean=True)
    
    if success:
        # Test the exe
        builder.test_exe()
        
        print("\n" + "=" * 70)
        print("BUILD COMPLETE!")
        print("=" * 70)
        print(f"\nYour executable is ready:")
        print(f"  {builder.output_dir / 'netexec.exe'}")
        print(f"\nNext steps:")
        print(f"  1. Test on a clean Windows VM")
        print(f"  2. Copy to different locations and test")
        print(f"  3. Create your demo video")
        print("=" * 70)
        return 0
    else:
        print("\nBuild failed. Check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())