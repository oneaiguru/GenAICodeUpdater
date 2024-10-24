
import os
from typing import List, Tuple

def map_code_blocks_to_paths(parsed_blocks: List[Tuple[str, str]], project_root: str) -> List[Tuple[str, str]]:
    """
    Maps parsed code blocks to actual file paths in the project directory, handling discrepancies in filenames.
    
    Args:
        parsed_blocks (List[Tuple[str, str]]): List of tuples with filenames and code blocks.
        project_root (str): Root directory of the project.
    
    Returns:
        List[Tuple[str, str]]: List of tuples with absolute file paths and code blocks.
    """
    def normalize_filename(filename: str) -> str:
        """Normalize filenames by converting spaces to underscores and lowercasing."""
        return filename.replace(' ', '_').lower()
    
    mapped_updates = []
    for filename, code in parsed_blocks:
        potential_path = os.path.join(project_root, filename)
        if os.path.isfile(potential_path):
            mapped_updates.append((potential_path, code))
        else:
            # Attempt to resolve discrepancies, e.g., case sensitivity, spaces/underscores
            normalized_filename = normalize_filename(os.path.basename(filename))
            for root, dirs, files in os.walk(project_root):
                for file in files:
                    if normalize_filename(file) == normalized_filename:
                        resolved_path = os.path.join(root, file)
                        mapped_updates.append((resolved_path, code))
                        break
    return mapped_updates
    