"""
Patches for NetExec module and protocol loaders to support path independence.
Apply these patches before building with Nuitka.
"""

import os
import sys
from pathlib import Path


def patch_netexec():
    """
    Apply all necessary patches to make NetExec path-independent.
    Call this at the beginning of netexec.py's main().
    """
    patch_protocol_loader()
    patch_module_loader()
    patch_database_path()
    patch_config_path()


def patch_protocol_loader():
    """
    Patch the protocol loader to use ResourceManager.
    """
    try:
        from nxc.loaders.protocol_loader import ProtocolLoader
        from nxc.helpers.resource_manager import get_resource_manager
        
        rm = get_resource_manager()
        
        # Monkey patch the protocols path
        original_init = ProtocolLoader.__init__
        
        def patched_init(self, args, db, logger):
            # Set the protocols path before calling original init
            self.protocols_path = rm.get_protocols_path()
            original_init(self, args, db, logger)
        
        ProtocolLoader.__init__ = patched_init
        
    except ImportError as e:
        print(f"Warning: Could not patch protocol loader: {e}")


def patch_module_loader():
    """
    Patch the module loader to use ResourceManager.
    """
    try:
        # Import after ResourceManager is available
        from nxc.helpers.resource_manager import get_resource_manager
        
        rm = get_resource_manager()
        
        # Try to patch module loader
        try:
            from nxc.loaders.module_loader import ModuleLoader
            
            original_init = ModuleLoader.__init__
            
            def patched_init(self, args, db, logger):
                # Set modules path
                self.modules_path = rm.get_modules_path()
                original_init(self, args, db, logger)
            
            ModuleLoader.__init__ = patched_init
            
        except ImportError:
            pass  # Module loader might not exist or have different structure
            
    except Exception as e:
        print(f"Warning: Could not patch module loader: {e}")


def patch_database_path():
    """
    Patch database initialization to use writable location.
    """
    try:
        from nxc.helpers.resource_manager import get_resource_manager
        
        rm = get_resource_manager()
        
        # Set NXC_DB environment variable if not set
        if 'NXC_DB' not in os.environ:
            db_path = rm.get_db_path()
            os.environ['NXC_DB'] = str(db_path)
        
    except Exception as e:
        print(f"Warning: Could not patch database path: {e}")


def patch_config_path():
    """
    Patch config file paths to use writable location.
    """
    try:
        from nxc.helpers.resource_manager import get_resource_manager
        
        rm = get_resource_manager()
        
        # Set config directory in user's home
        if 'NXC_CONFIG_PATH' not in os.environ:
            config_path = Path.home() / '.nxc'
            config_path.mkdir(parents=True, exist_ok=True)
            os.environ['NXC_CONFIG_PATH'] = str(config_path)
        
    except Exception as e:
        print(f"Warning: Could not patch config path: {e}")


# Alternative approach: Direct file patching instructions
PATCH_INSTRUCTIONS = """
=============================================================================
MANUAL PATCHING INSTRUCTIONS FOR PATH INDEPENDENCE
=============================================================================

If automatic patching fails, apply these changes manually:

1. CREATE: nxc/helpers/resource_manager.py
   - Copy the ResourceManager class from the artifact

2. MODIFY: nxc/loaders/protocol_loader.py
   Add at the top:
   ```python
   from nxc.helpers.resource_manager import get_resource_manager
   ```
   
   In ProtocolLoader.__init__, replace any hardcoded paths with:
   ```python
   rm = get_resource_manager()
   self.protocols_path = rm.get_protocols_path()
   ```

3. MODIFY: nxc/loaders/module_loader.py (if exists)
   Similar to protocol_loader - use:
   ```python
   self.modules_path = rm.get_modules_path()
   ```

4. MODIFY: nxc/netexec.py
   Add at the beginning of main():
   ```python
   from nxc.helpers.resource_manager import get_resource_manager
   
   # Initialize resource manager
   rm = get_resource_manager()
   
   # Set database path
   import os
   if 'NXC_DB' not in os.environ:
       os.environ['NXC_DB'] = str(rm.get_db_path())
   ```

5. MODIFY: Any file that uses __file__ or os.getcwd()
   Replace with ResourceManager calls:
   ```python
   from nxc.helpers.resource_manager import get_resource_manager
   rm = get_resource_manager()
   path = rm.resolve_path('relative/path')
   ```

=============================================================================
"""


if __name__ == "__main__":
    print(PATCH_INSTRUCTIONS)