"""
Analyze NetExec codebase for path dependencies.
This helps identify what needs to be patched for path independence.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Set


def find_path_usages(directory: Path) -> Dict[str, List[Dict]]:
    """
    Scan Python files for path-related operations.
    
    Returns:
        Dictionary mapping file paths to list of found issues
    """
    issues = {}
    
    # Patterns to search for
    patterns = {
        '__file__': r'__file__',
        'os.getcwd()': r'os\.getcwd\(\)',
        'os.path.dirname': r'os\.path\.dirname',
        'os.path.abspath': r'os\.path\.abspath',
        'os.path.join': r'os\.path\.join',
        'open(': r'\bopen\s*\(',
        'Path(': r'\bPath\s*\(',
        'pkg_resources': r'pkg_resources',
        'importlib.resources': r'importlib\.resources',
    }
    
    for py_file in directory.rglob('*.py'):
        # Skip __pycache__ and venv
        if '__pycache__' in str(py_file) or 'venv' in str(py_file):
            continue
        
        try:
            with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
            
            file_issues = []
            
            for pattern_name, pattern in patterns.items():
                for i, line in enumerate(lines, 1):
                    if re.search(pattern, line):
                        file_issues.append({
                            'line': i,
                            'pattern': pattern_name,
                            'content': line.strip()
                        })
            
            if file_issues:
                relative_path = py_file.relative_to(directory)
                issues[str(relative_path)] = file_issues
                
        except Exception as e:
            print(f"Error reading {py_file}: {e}")
    
    return issues


def find_data_files(directory: Path) -> List[Path]:
    """
    Find non-Python files that may need to be bundled.
    """
    data_extensions = {'.txt', '.yaml', '.yml', '.json', '.xml', '.conf', '.cfg', '.ini'}
    data_files = []
    
    for file in directory.rglob('*'):
        if file.is_file() and file.suffix in data_extensions:
            if '__pycache__' not in str(file) and 'venv' not in str(file):
                data_files.append(file.relative_to(directory))
    
    return data_files


def analyze_imports(directory: Path) -> Set[str]:
    """
    Find all imported modules to understand dependencies.
    """
    imports = set()
    import_pattern = r'^\s*(?:from\s+([\w.]+)|import\s+([\w.]+))'
    
    for py_file in directory.rglob('*.py'):
        if '__pycache__' in str(py_file) or 'venv' in str(py_file):
            continue
        
        try:
            with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    match = re.match(import_pattern, line)
                    if match:
                        module = match.group(1) or match.group(2)
                        if module:
                            # Get top-level module
                            top_module = module.split('.')[0]
                            imports.add(top_module)
        except Exception:
            pass
    
    return imports


def print_analysis(nxc_path: Path):
    """Print analysis results"""
    
    print("=" * 80)
    print("NetExec Path Dependency Analysis")
    print("=" * 80)
    print()
    
    # Find path usages
    print("🔍 Scanning for path-dependent code...")
    issues = find_path_usages(nxc_path)
    
    print(f"\n📊 Found {len(issues)} files with path operations\n")
    
    # Show critical files
    critical_files = [
        'netexec.py',
        'loaders/protocol_loader.py',
        'loaders/module_loader.py',
        'database.py',
        'config.py'
    ]
    
    print("🚨 CRITICAL FILES TO PATCH:")
    print("-" * 80)
    
    for file in critical_files:
        matching_files = [k for k in issues.keys() if file in k]
        if matching_files:
            for matched_file in matching_files:
                print(f"\n📄 {matched_file}")
                for issue in issues[matched_file][:5]:  # Show first 5 issues
                    print(f"   Line {issue['line']:4d} | {issue['pattern']:20s} | {issue['content'][:60]}")
                if len(issues[matched_file]) > 5:
                    print(f"   ... and {len(issues[matched_file]) - 5} more")
        else:
            print(f"\n📄 {file} - NOT FOUND or no issues")
    
    # Data files
    print("\n\n📦 DATA FILES TO BUNDLE:")
    print("-" * 80)
    data_files = find_data_files(nxc_path)
    
    if data_files:
        for df in sorted(data_files)[:20]:  # Show first 20
            print(f"   {df}")
        if len(data_files) > 20:
            print(f"   ... and {len(data_files) - 20} more")
    else:
        print("   No data files found")
    
    # Imports
    print("\n\n📚 EXTERNAL DEPENDENCIES:")
    print("-" * 80)
    imports = analyze_imports(nxc_path)
    
    # Filter to likely external packages (not stdlib)
    stdlib = {'os', 'sys', 're', 'json', 'pathlib', 'logging', 'argparse', 
              'datetime', 'time', 'socket', 'ssl', 'base64', 'hashlib', 
              'collections', 'itertools', 'functools', 'typing'}
    
    external = sorted(imports - stdlib)
    
    for imp in external[:30]:  # Show first 30
        print(f"   {imp}")
    if len(external) > 30:
        print(f"   ... and {len(external) - 30} more")
    
    print("\n" + "=" * 80)
    print("✅ Analysis complete!")
    print("=" * 80)


if __name__ == "__main__":
    # Detect NetExec path
    current = Path.cwd()
    
    # Look for nxc directory
    if (current / 'nxc').exists():
        nxc_path = current
    elif (current.parent / 'nxc').exists():
        nxc_path = current.parent
    else:
        print("Error: Could not find NetExec (nxc) directory")
        print("Please run this script from the NetExec repository root")
        exit(1)
    
    print(f"Analyzing: {nxc_path}")
    print_analysis(nxc_path)