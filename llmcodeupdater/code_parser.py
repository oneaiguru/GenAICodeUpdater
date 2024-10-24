import re
from typing import List, Tuple
import logging

# Set up logging for the module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_code_blocks_with_logging(file_content: str) -> List[Tuple[str, str]]:
    """
    Parses the content of an LLM output file to extract code blocks associated with filenames.
    Supports both markdown-style code blocks and filename comments.
    
    Args:
        file_content (str): The content of the LLM output file.
    
    Returns:
        List[Tuple[str, str]]: A list of tuples containing filenames and their corresponding code blocks.
    """
    # Pattern to match markdown code blocks with optional language specification
    # Matches: ```python, ```py, or just ```
    markdown_pattern = r'```(?:python|py)?\n(.*?)```|(#\s*[\w/.]+\.py)'
    
    # Pattern to match filenames in comments or text
    # Matches both "# filename.py" and just "filename.py"
    filename_pattern = r'[#\s]*([\w/.]+\.py)'
    
    # Find all code blocks
    code_blocks = re.findall(markdown_pattern, file_content, re.DOTALL)
    if not code_blocks:
        logger.warning("No markdown code blocks found in the provided content.")
        return []

    result = []
    current_filename = None
    current_block = []

    for block in code_blocks:
        # Check if the block is a markdown code block or a comment
        if isinstance(block, tuple):
            # This is a filename comment
            filename_match = re.search(filename_pattern, block[1])
            if filename_match:
                # Update current filename
                current_filename = filename_match.group(1).strip()
        else:
            # This is a markdown code block
            # Clean up the block
            block_lines = block.strip().split('\n')
            
            for line in block_lines:
                # Check for filename
                filename_match = re.search(filename_pattern, line)
                if filename_match:
                    # If we have a previous filename and block, save it
                    if current_filename and current_block:
                        code_content = '\n'.join(current_block).strip()
                        if code_content:
                            logger.info(f"Found code block for {current_filename}")
                            result.append((current_filename, code_content))
                        current_block = []
                    
                    # Update current filename
                    current_filename = filename_match.group(1).strip()
                else:
                    # Add non-filename lines to current block
                    current_block.append(line)
            
            # Don't forget to add the last block
            if current_filename and current_block:
                code_content = '\n'.join(current_block).strip()
                if code_content:
                    logger.info(f"Found code block for {current_filename}")
                    result.append((current_filename, code_content))
    
    if not result:
        logger.warning("No valid code blocks with filenames were extracted.")
    else:
        logger.info(f"Successfully extracted {len(result)} code blocks with filenames.")

    return result
