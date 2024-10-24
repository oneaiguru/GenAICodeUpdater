import re
from typing import List, Tuple
import logging

# Set up logging for the module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_code_blocks_with_logging(file_content: str) -> List[Tuple[str, str]]:
    """
    Parses the content of a .py file to extract code blocks associated with filenames.
    Includes logging for errors and successful processing.
    
    Args:
        file_content (str): The content of the .py file.
    
    Returns:
        List[Tuple[str, str]]: A list of tuples containing filenames and their corresponding code blocks.
    """
    # Regex to identify filename comments (e.g., # utils/redis_manager.py)
    pattern = re.compile(r'^#\s*(.+\.py)$', re.MULTILINE)
    
    matches = list(pattern.finditer(file_content))
    code_blocks = []
    
    if not matches:
        logger.warning("No filename comments found in the provided content.")
    
    for i, match in enumerate(matches):
        filename = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(file_content)
        code_block = file_content[start:end].strip()
        
        if code_block:
            logger.info(f"Code block found for {filename}")
            code_blocks.append((filename, code_block))
        else:
            logger.error(f"Empty or incomplete code block found for {filename}. Ignored.")
    
    if not code_blocks:
        logger.warning("No valid code blocks were extracted.")

    return code_blocks
    