import os
from typing import List, Tuple, Dict, Optional
import logging
from pathlib import Path
import difflib
from termcolor import colored
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)

@dataclass
class FileUpdateInfo:
    """Information about file updates"""
    old_path: str
    new_path: str
    old_size: int
    new_size: int
    old_lines: int
    new_lines: int
    percent_change: float
    diff: str

def find_file(project_root: str, filename: str) -> str:
    """
    Searches for a file within the project directory. Matches by basename unless
    filename contains path separators.
    
    Args:
        project_root (str): The root directory of the project
        filename (str): Name of the file to find (can include path)
        
    Returns:
        str: Absolute path to the file if found, empty string otherwise
    """
    try:
        # Special handling for __init__.py files - require exact path match
        if filename == '__init__.py' or '/' in filename or '\\' in filename:
            full_path = os.path.join(project_root, filename)
            return full_path if os.path.exists(full_path) else ""
            
        # For other files, search by basename
        target_name = os.path.basename(filename)
        matches = []
        
        for root, _, files in os.walk(project_root):
            if target_name in files:
                matches.append(os.path.join(root, target_name))
                
        # Return first match if found
        return matches[0] if matches else ""
        
    except Exception as e:
        logger.error(f"Error searching for file {filename}: {str(e)}")
        return ""

def preserve_imports(old_content: str, new_content: str) -> str:
    """
    Preserve imports from old file if new content lacks imports.
    
    Args:
        old_content (str): Original file content
        new_content (str): New file content
        
    Returns:
        str: Modified content with preserved imports if needed
    """
    # Check if new content has imports
    if re.search(r'^(?:import|from)\s+\w+', new_content, re.MULTILINE):
        return new_content
        
    # Extract imports from old content
    import_lines = []
    
    for line in old_content.splitlines():
        if re.match(r'^(?:import|from)\s+\w+', line):
            import_lines.append(line)
            
    # Combine preserved imports with new content
    if import_lines:
        preserved_imports = '\n'.join(import_lines)
        return f"{preserved_imports}\n\n{new_content}"
        
    return new_content

def get_change_color(percent: float) -> str:
    """Get color based on percentage change."""
    if percent <= 70:
        return 'red'
    elif percent <= 80:
        return 'yellow'
    elif percent <= 90:
        return 'white'
    elif percent <= 110:
        return 'green'
    elif percent <= 120:
        return 'magenta'
    elif percent <= 140:
        return 'magenta'
    else:
        return 'blue'

def format_size_bar(percent: float, width: int = 40) -> str:
    """Create a visual representation of size change."""
    filled = int((min(percent, 200) / 200) * width)
    bar = '=' * filled + ' ' * (width - filled)
    color = get_change_color(percent)
    return colored(f'[{bar}]', color)

def create_diff(old_content: str, new_content: str) -> str:
    """Create a colored diff between old and new content."""
    diff = difflib.unified_diff(
        old_content.splitlines(keepends=True),
        new_content.splitlines(keepends=True),
        lineterm=''
    )
    
    result = []
    for line in diff:
        if line.startswith('+'):
            result.append(colored(line, 'green'))
        elif line.startswith('-'):
            result.append(colored(line, 'red'))
        elif line.startswith('^'):
            result.append(colored(line, 'blue'))
        else:
            result.append(line)
            
    return ''.join(result)

def is_partial_update(old_content: str, new_content: str) -> bool:
    """
    Check if the update is partial (preserves some original content).
    
    Args:
        old_content (str): Original file content
        new_content (str): New file content
        
    Returns:
        bool: True if update is partial, False otherwise
    """
    old_lines = set(old_content.splitlines())
    new_lines = set(new_content.splitlines())
    return bool(old_lines & new_lines)

def update_files(mapped_updates: List[Tuple[str, str]], project_root: str) -> Dict:
    """
    Updates files with their corresponding code blocks, preserving imports when needed
    and providing detailed update information.
    
    Args:
        mapped_updates (List[Tuple[str, str]]): List of tuples containing filenames 
            and their updated code content
        project_root (str): Root directory of the project
        
    Returns:
        Dict: Statistics and detailed information about the update process
    """
    files_updated = 0
    files_skipped = 0
    errors = {}
    unmatched_files = []
    processed_files = set()
    update_details = []

    for filename, code_block in mapped_updates:
        try:
            # Search for the file in the project directory
            file_path = find_file(project_root, filename)
            
            if not file_path:
                logger.warning(f"File '{filename}' not found in project directory")
                unmatched_files.append(filename)
                files_skipped += 1
                continue
                
            # Skip if this file has already been processed
            if file_path in processed_files:
                logger.warning(f"Duplicate update attempt for '{file_path}'. Using first occurrence only.")
                files_skipped += 1
                continue
                
            # Read original content
            with open(file_path, 'r', encoding='utf-8') as f:
                old_content = f.read()
                
            # Preserve imports if needed
            new_content = preserve_imports(old_content, code_block)
            
            # Calculate metrics
            old_size = len(old_content.encode('utf-8'))
            new_size = len(new_content.encode('utf-8'))
            old_lines = len(old_content.splitlines())
            new_lines = len(new_content.splitlines())
            percent_change = (new_size / old_size * 100) if old_size > 0 else 100
            
            # Create diff
            diff_content = create_diff(old_content, new_content)
            
            # Store update info
            update_info = FileUpdateInfo(
                old_path=file_path,
                new_path=file_path,
                old_size=old_size,
                new_size=new_size,
                old_lines=old_lines,
                new_lines=new_lines,
                percent_change=percent_change,
                diff=diff_content
            )
            update_details.append(update_info)
            
            # Write updated content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            files_updated += 1
            processed_files.add(file_path)
            
            # Log detailed update information
            print(f"\nFile: {file_path}")
            print(f"Lines: {old_lines} -> {new_lines}")
            print(f"Size: {old_size/1024:.1f}KB -> {new_size/1024:.1f}KB")
            print(f"Change: {percent_change:.1f}%")
            print(format_size_bar(percent_change))
            print("\nDiff:")
            print(diff_content)

        except Exception as e:
            error_msg = f"Error updating '{filename}': {str(e)}"
            logger.error(error_msg)
            errors[filename] = str(e)
            files_skipped += 1

    # Log summary
    logger.info(f"Update complete: {files_updated} files updated, {files_skipped} files skipped")
    if unmatched_files:
        logger.warning(f"Unmatched files: {', '.join(unmatched_files)}")
    if errors:
        logger.error(f"Errors encountered: {len(errors)} files")

    return {
        'files_updated': files_updated,
        'files_skipped': files_skipped,
        'errors': errors,
        'unmatched_files': unmatched_files,
        'update_details': update_details
    }