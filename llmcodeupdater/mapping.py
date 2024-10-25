import os
from typing import List, Tuple, Dict
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def find_file(project_root: str, filename: str) -> str:
    """
    Searches for a file within the project directory, including subdirectories.
    If multiple files with the same name exist, returns the first match.
    
    Args:
        project_root (str): The root directory of the project
        filename (str): Name of the file to find
        
    Returns:
        str: Absolute path to the file if found, empty string otherwise
    """
    try:
        for root, _, files in os.walk(project_root):
            if filename in files:
                return os.path.join(root, filename)
        return ""
    except Exception as e:
        logger.error(f"Error searching for file {filename}: {str(e)}")
        return ""

def is_partial_update(code_block: str) -> bool:
    """
    Detects if a code block contains indicators of being a partial update.
    
    Args:
        code_block (str): The code content to check
        
    Returns:
        bool: True if partial update indicators are found, False otherwise
    """
    skip_indicators = [
        'rest of',
        'do not change',
        'manual review needed',
        'unchanged',
        'remaining code',
        '...'
    ]
    
    # Convert to lowercase for case-insensitive matching
    lower_code = code_block.lower()
    
    # Check each line for indicators
    for line in lower_code.split('\n'):
        stripped = line.strip()
        # Look for indicators in comments or standalone text
        if any(indicator in stripped for indicator in skip_indicators):
            if stripped.startswith('#') or stripped.startswith('//') or stripped.startswith('/*'):
                return True
    
    return False

def update_files(mapped_updates: List[Tuple[str, str]], project_root: str) -> Dict:
    """
    Updates files with their corresponding code blocks, handling nested directories
    and ensuring accurate file mapping.
    
    Args:
        mapped_updates (List[Tuple[str, str]]): List of tuples containing filenames 
            and their updated code content
        project_root (str): Root directory of the project
        
    Returns:
        Dict: Statistics about the update process including:
            - files_updated: number of successfully updated files
            - files_skipped: number of skipped files
            - errors: dictionary of errors encountered
            - unmatched_files: list of files that couldn't be found
    """
    files_updated = 0
    files_skipped = 0
    errors = {}
    unmatched_files = []
    processed_files = set()  # Track processed files to handle duplicates

    for filename, code_block in mapped_updates:
        try:
            # Get just the filename if a path is provided
            base_filename = os.path.basename(filename)
            
            # Search for the file in the project directory
            file_path = find_file(project_root, base_filename)
            
            if not file_path:
                logger.warning(
                    f"File '{filename}' not found in project directory"
                )
                unmatched_files.append(filename)
                files_skipped += 1
                continue
                
            # Skip if this file has already been processed
            if file_path in processed_files:
                logger.warning(
                    f"Duplicate update attempt for '{file_path}'. Using first occurrence only."
                )
                files_skipped += 1
                continue
                
            # Check for partial updates
            if is_partial_update(code_block):
                logger.info(
                    f"Skipping '{file_path}' - detected partial update indicators"
                )
                files_skipped += 1
                continue
                
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Write updated content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(code_block)
                
            files_updated += 1
            processed_files.add(file_path)
            logger.info(f"Successfully updated '{file_path}'")

        except PermissionError as e:
            error_msg = f"Permission denied: {str(e)}"
            logger.error(f"Permission error updating '{filename}': {error_msg}")
            errors[filename] = error_msg
            files_skipped += 1
            
        except FileNotFoundError as e:
            error_msg = f"File not found: {str(e)}"
            logger.error(f"File not found error updating '{filename}': {error_msg}")
            errors[filename] = error_msg
            files_skipped += 1
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Error updating '{filename}': {error_msg}")
            errors[filename] = error_msg
            files_skipped += 1

    # Log summary
    logger.info(f"Update complete: {files_updated} files updated, "
                f"{files_skipped} files skipped")
    if unmatched_files:
        logger.warning(f"Unmatched files: {', '.join(unmatched_files)}")
    if errors:
        logger.error(f"Errors encountered: {len(errors)} files")

    return {
        'files_updated': files_updated,
        'files_skipped': files_skipped,
        'errors': errors,
        'unmatched_files': unmatched_files
    }