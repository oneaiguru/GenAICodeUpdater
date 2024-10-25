import os
import fnmatch
from typing import List, Set
import logging
import time
import unittest

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
        self.ignore_patterns: Set[str] = set()
        self.always_ignore = {
            '__pycache__',
            '*.pyc',
            '.git',
            '.DS_Store',
            'venv',
            'myenv',
            '*.log',
            '.env*',
            '*.rdb',
            'backups',
            'alembic',
            'alembic_multi',
            'tests',
            'initial_data',
            'migrations',
            '.pytest_cache',
            '.mypy_cache',
            '.coverage',
            'htmlcov',
            '*.egg-info',
            'dist',
            'build',
            '.modal',
            '.cache'
        }
        self._pattern_cache = {}  # Cache for fnmatch results
        self.load_ignore_patterns()
        
    def load_ignore_patterns(self) -> None:
        """Load ignore patterns from specified ignore files and add always-ignore patterns."""
        start_time = time.time()
        self.ignore_patterns.update(self.always_ignore)
        
        for ignore_file in self.ignore_files:
            path = os.path.join(self.root_dir, ignore_file)
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                # Handle directory patterns by ensuring they end with /**
                                if line.endswith('/'):
                                    line = line + '**'
                                self.ignore_patterns.add(line)
                        logger.info(f"Loaded patterns from {ignore_file}")
                except Exception as e:
                    logger.error(f"Error loading {ignore_file}: {e}")
        
        logger.info(f"Pattern loading completed in {time.time() - start_time:.2f}s")

    def _check_path_against_patterns(self, path: str, patterns: Set[str]) -> bool:
        """Check if path matches any pattern using caching."""
        cache_key = (path, tuple(sorted(patterns)))
        if cache_key in self._pattern_cache:
            return self._pattern_cache[cache_key]
        
        # Normalize path separators
        path = path.replace('\\', '/')
        
        # Check if any pattern matches
        for pattern in patterns:
            # Handle directory patterns
            if pattern.endswith('/**'):
                base_pattern = pattern[:-3]
                if path.startswith(base_pattern) or fnmatch.fnmatch(path, pattern):
                    self._pattern_cache[cache_key] = True
                    return True
            elif fnmatch.fnmatch(path, pattern):
                self._pattern_cache[cache_key] = True
                return True
        
        self._pattern_cache[cache_key] = False
        return False

    def is_ignored(self, path: str) -> bool:
        """Check if the given path matches any of the ignore patterns."""
        start_time = time.time()
        path = path.replace('\\', '/')
        
        result = self._check_path_against_patterns(path, self.ignore_patterns)
        
        if time.time() - start_time > 0.1:  # Log only if check takes more than 100ms
            logger.warning(f"Slow pattern matching for {path}: {time.time() - start_time:.2f}s")
            
        return result