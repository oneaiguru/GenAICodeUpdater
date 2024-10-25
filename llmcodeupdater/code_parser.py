# code_parser.py
import re
import os
from dataclasses import dataclass
from typing import List, Tuple, Optional
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CodeBlock:
    """Represents a parsed code block with metadata"""
    filename: str
    content: str
    is_complete: bool
    line_number: int
    project_path: Optional[str] = None

class CodeParser:
    """Parser for extracting and processing code blocks from LLM output"""
    
    def __init__(self, project_root: Optional[str] = None):
        """Initialize parser with optional project root directory"""
        self.project_root = project_root
        
        # Patterns for different comment styles and filenames
        self.filename_patterns = [
            r'^\s*#\s*([\w/.-]+\.py)\s*$',      # Python style comments
            r'^\s*//\s*([\w/.-]+\.py)\s*$',     # C-style comments
            r'^\s*([\w/.-]+\.py)\s*$',          # Bare filename
            r'^\s*""".*?([\w/.-]+\.py).*?"""',  # Docstring mentions
            r'^\s*Updated?\s*["`\']([\w/.-]+\.py)["`\']'  # Update references
        ]
        
        # Markers that indicate incomplete or placeholder code
        self.incomplete_markers = [
            r'(?i)rest of .*(?:unchanged|remains|same)',
            r'(?i)(?:do not|don\'t) change',
            r'(?i)manual review needed',
            r'(?i)unchanged content',
            r'(?i)original .*(?:code|implementation)',
            r'\.{3,}'  # Ellipsis indicating omitted content
        ]
    
    def _is_incomplete_block(self, content: str) -> bool:
        """Check if a code block contains markers indicating it's incomplete"""
        return any(re.search(pattern, content, re.MULTILINE) for pattern in self.incomplete_markers)
    
    def _find_project_file(self, filename: str) -> Optional[str]:
        """Find the full path of a file in the project directory"""
        if not self.project_root:
            return None
        
        file_path = os.path.join(self.project_root, filename)
        if os.path.exists(file_path):
            return file_path
            
        # Search for the file in project directory if direct path doesn't exist
        for root, _, files in os.walk(self.project_root):
            if filename in files:
                return os.path.join(root, filename)
        return None
    
    def _extract_filename(self, line: str) -> Optional[str]:
        """Extract filename from a line of text using various patterns"""
        for pattern in self.filename_patterns:
            match = re.match(pattern, line)
            if match:
                return match.group(1)
        return None
    
    def parse_code_blocks(self, content: str) -> List[CodeBlock]:
        """
        Parse code blocks from content, handling multiple formats and patterns
        """
        lines = content.split('\n')
        blocks: List[CodeBlock] = []
        
        current_block = []
        current_filename = None
        block_start_line = 0
        in_code_block = False
        
        for i, line in enumerate(lines, 1):
            # Check for markdown code fence
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                continue
            
            # Skip markdown code block start indicators
            if line.strip() == 'python':
                continue
                
            # Look for filename markers
            filename = self._extract_filename(line)
            if filename:
                # Save previous block if exists
                if current_filename and current_block:
                    block_content = '\n'.join(current_block).strip()
                    if block_content:  # Only create block if there's content
                        is_complete = not self._is_incomplete_block(block_content)
                        project_path = self._find_project_file(current_filename) if self.project_root else None
                        
                        blocks.append(CodeBlock(
                            filename=current_filename,
                            content=block_content,
                            is_complete=is_complete,
                            line_number=block_start_line,
                            project_path=project_path
                        ))
                
                current_filename = filename
                current_block = []
                block_start_line = i
                continue
            
            # Add non-empty lines to current block if we have a filename
            if current_filename and line.strip():
                # Only add lines that aren't markdown fences
                if not line.strip().startswith('```'):
                    current_block.append(line)
        
        # Handle final block
        if current_filename and current_block:
            block_content = '\n'.join(current_block).strip()
            if block_content:
                is_complete = not self._is_incomplete_block(block_content)
                project_path = self._find_project_file(current_filename) if self.project_root else None
                
                blocks.append(CodeBlock(
                    filename=current_filename,
                    content=block_content,
                    is_complete=is_complete,
                    line_number=block_start_line,
                    project_path=project_path
                ))
        
        # Log summary
        complete_blocks = sum(1 for b in blocks if b.is_complete)
        incomplete_blocks = len(blocks) - complete_blocks
        
        logger.info(f"Parsed {len(blocks)} total code blocks:")
        logger.info(f"- Complete blocks: {complete_blocks}")
        logger.info(f"- Incomplete blocks: {incomplete_blocks}")
        logger.info(f"- Blocks with project paths: {sum(1 for b in blocks if b.project_path)}")
        
        return blocks

def parse_code_blocks_with_logging(file_content: str) -> List[Tuple[str, str]]:
    """Legacy wrapper for backward compatibility"""
    parser = CodeParser()
    blocks = parser.parse_code_blocks(file_content)
    return [(block.filename, block.content) for block in blocks if block.is_complete]