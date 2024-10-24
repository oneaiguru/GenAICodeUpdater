import os
from typing import List, Tuple, Dict
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def update_files(mapped_updates: List[Tuple[str, str]]) -> dict:
    """
    Updates files with their corresponding code blocks, with improved validation.
    
    Args:
        mapped_updates: List of tuples containing file paths and their updated code content
        
    Returns:
        dict: Statistics about the update process
    """
    files_updated = 0
    files_skipped = 0
    errors = {}
    
    for file_path, code_block in mapped_updates:
        try:
            # Normalize path
            file_path = os.path.normpath(file_path)
            
            # More precise partial update detection
            # Only skip if these indicators appear in comments or as standalone text
            skip_indicators = [
                '# rest of',
                '// rest of',
                '# do not change',
                '// do not change',
                '# manual review needed',
                '// manual review needed'
            ]
            
            # Check if indicators are present as standalone comments
            lines = code_block.split('\n')
            has_skip_indicator = False
            
            for line in lines:
                stripped = line.strip()
                if any(indicator in stripped for indicator in skip_indicators):
                    has_skip_indicator = True
                    break
            
            # Skip only if genuine partial update indicators are found
            if has_skip_indicator:
                logger.info(f"Skipping {file_path} due to explicit partial update indicators")
                files_skipped += 1
                continue
                
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Write the updated content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(code_block)
                files_updated += 1
                logger.info(f"Successfully updated {file_path}")
                
        except PermissionError as e:
            files_skipped += 1
            errors[file_path] = f"Permission denied: {str(e)}"
            logger.error(f"Permission denied when updating {file_path}: {str(e)}")
            
        except Exception as e:
            files_skipped += 1
            errors[file_path] = str(e)
            logger.error(f"Error updating {file_path}: {str(e)}")
    
    return {
        'files_updated': files_updated,
        'files_skipped': files_skipped,
        'errors': errors
    }