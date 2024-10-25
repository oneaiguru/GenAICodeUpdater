# llmcodeupdater/ignore_handler.py

import os
import fnmatch
from typing import List
import logging

logger = logging.getLogger(__name__)

class IgnoreHandler:
    """Handles loading and matching ignore patterns from various ignore files."""

    def __init__(self, root_dir: str, ignore_files: List[str] = None):
        """
        Initialize with the root directory and list of ignore files.
        
        Args:
            root_dir (str): The root directory to scan for ignore files.
            ignore_files (List[str], optional): List of ignore file names.
                Defaults to ['.gitignore', '.treeignore', '.selectignore'].
        """
        self.root_dir = root_dir
        self.ignore_files = ignore_files if ignore_files else ['.gitignore', '.treeignore', '.selectignore']
        self.ignore_patterns = self.load_ignore_patterns()

    def load_ignore_patterns(self) -> List[str]:
        """Load ignore patterns from specified ignore files."""
        patterns = []
        for ignore_file in self.ignore_files:
            path = os.path.join(self.root_dir, ignore_file)
            if os.path.exists(path):
                with open(path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            patterns.append(line)
                logger.info(f"Loaded patterns from {ignore_file}")
        return patterns

    def is_ignored(self, path: str) -> bool:
        """
        Check if the given path matches any of the ignore patterns.
        
        Args:
            path (str): The file or directory path relative to root_dir.
        
        Returns:
            bool: True if the path should be ignored, False otherwise.
        """
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(path, pattern):
                logger.debug(f"Ignored path: {path} matches pattern: {pattern}")
                return True
        return False
