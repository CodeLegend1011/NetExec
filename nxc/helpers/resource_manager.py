"""
Resource Manager for Path-Independent NetExec
Handles loading of resources regardless of current working directory.
Compatible with Nuitka single-file builds.
"""

import os
import sys
from pathlib import Path
from typing import Optional


class ResourceManager:
    """
    Manages resource paths for NetExec to work from any directory.
    Handles both development mode and Nuitka-compiled binary mode.
    """
    
    _instance = None
    _base_path = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ResourceManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize the base path for resources"""
        self._base_path = self._find_base_path()
        self._is_frozen = getattr(sys, 'frozen', False)
    
    def _find_base_path(self) -> Path:
        """
        Find the base path for NetExec resources.
        Works in both development and compiled modes.
        """
        # Check if running as a Nuitka compiled binary
        if getattr(sys, 'frozen', False):
            # Running as compiled binary
            if hasattr(sys, '_MEIPASS'):
                # PyInstaller/Nuitka onefile mode
                return Path(sys._MEIPASS)
            else:
                # Nuitka standalone mode
                return Path(sys.executable).parent
        else:
            # Running in development mode
            # Find the nxc package directory
            try:
                import nxc
                return Path(nxc.__file__).parent.parent
            except (ImportError, AttributeError):
                # Fallback: assume we're in the repo root
                return Path(__file__).parent.parent.parent
    
    @property
    def base_path(self) -> Path:
        """Get the base path for the application"""
        return self._base_path
    
    @property
    def nxc_path(self) -> Path:
        """Get the nxc package path"""
        return self._base_path / 'nxc'
    
    @property
    def is_frozen(self) -> bool:
        """Check if running as compiled binary"""
        return self._is_frozen
    
    def get_protocols_path(self) -> Path:
        """Get the path to protocols directory"""
        return self.nxc_path / 'protocols'
    
    def get_modules_path(self) -> Path:
        """Get the path to modules directory"""
        return self.nxc_path / 'modules'
    
    def get_data_path(self) -> Path:
        """Get the path to data directory"""
        return self.nxc_path / 'data'
    
    def get_db_path(self) -> Path:
        """
        Get the database path.
        In frozen mode, use user's home directory to allow writes.
        """
        if self.is_frozen:
            # Use user's home directory for database
            home = Path.home()
            db_dir = home / '.nxc'
            db_dir.mkdir(parents=True, exist_ok=True)
            return db_dir
        else:
            # Development mode: use workspace directory
            workspace = self.base_path / 'workspace'
            workspace.mkdir(parents=True, exist_ok=True)
            return workspace
    
    def resolve_path(self, relative_path: str) -> Path:
        """
        Resolve a relative path to an absolute path based on base_path.
        
        Args:
            relative_path: Path relative to the nxc package
            
        Returns:
            Absolute Path object
        """
        return self.nxc_path / relative_path
    
    def ensure_directory(self, path: Path) -> Path:
        """
        Ensure a directory exists, create if it doesn't.
        
        Args:
            path: Path to directory
            
        Returns:
            The path (for chaining)
        """
        path.mkdir(parents=True, exist_ok=True)
        return path


# Global instance
_resource_manager = None


def get_resource_manager() -> ResourceManager:
    """Get the global ResourceManager instance"""
    global _resource_manager
    if _resource_manager is None:
        _resource_manager = ResourceManager()
    return _resource_manager


def get_data_path(filename: str = '') -> Path:
    """
    Convenience function to get a path in the data directory.
    
    Args:
        filename: Optional filename to append to data path
        
    Returns:
        Path to data directory or file
    """
    rm = get_resource_manager()
    data_path = rm.get_data_path()
    
    if filename:
        return data_path / filename
    return data_path


def get_workspace_path(filename: str = '') -> Path:
    """
    Convenience function to get a path in the workspace directory.
    
    Args:
        filename: Optional filename to append to workspace path
        
    Returns:
        Path to workspace directory or file
    """
    rm = get_resource_manager()
    workspace = rm.get_db_path()
    
    if filename:
        return workspace / filename
    return workspace