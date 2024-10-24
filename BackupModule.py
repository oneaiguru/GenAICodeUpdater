
import os
import shutil
from datetime import datetime
from typing import List

def backup_files(file_paths: List[str], project_root: str, backup_root: str) -> int:
    """
    Creates backups of the specified files, preserving directory structure, and handles errors gracefully.

    Args:
        file_paths (List[str]): List of absolute file paths to back up.
        project_root (str): Root directory of the project.
        backup_root (str): Root directory where backups will be stored.

    Returns:
        int: Number of files successfully backed up.
    """
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    files_backed_up = 0
    backup_dir = os.path.join(backup_root, timestamp)

    try:
        for file_path in file_paths:
            if not os.path.exists(file_path):
                # Skip if file doesn't exist
                continue

            relative_path = os.path.relpath(file_path, project_root)
            backup_path = os.path.join(backup_dir, relative_path)
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            shutil.copy2(file_path, backup_path)
            files_backed_up += 1

        return files_backed_up
    except Exception as e:
        # Clean up partial backup in case of failure
        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir)
        raise e
    