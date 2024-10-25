import re
import os
import pyperclip
from typing import List, Tuple, Optional, Dict
import logging
from pathlib import Path
from .code_block import CodeBlock

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_code_blocks_with_logging(content: str) -> List[Tuple[str, str]]:
    """
    Parse code blocks from LLM output content with logging.
    Returns a list of tuples (filename, code_content).
    """
    if not content:
        logger.error("Empty content provided to parser")
        return []

    # Regular expression to match code blocks with filenames
    # Matches both Markdown-style blocks, custom format blocks, and inline comment-style blocks
    patterns = [
        # Match ```python filename.py\n...``` style blocks
        r'```python\s+([^\n]+\.py)\n(.*?)```',
        # Match ########## filename.py ########## style blocks
        r'##########\s*([^\n]+\.py)\s*##########\n(.*?)(?=##########|\Z)',
        # Match File: filename.py style with markdown
        r'File:\s*([^\n]+\.py)\n```python\n(.*?)```',
        # Updated inline comment-style block
        r'#\s*([^\n]+\.py)\n(.*?)(?=\n#|```|\Z)'
    ]

    code_blocks = []
    for pattern in patterns:
        matches = re.finditer(pattern, content, re.DOTALL | re.MULTILINE)
        for match in matches:
            # Clean filename by removing leading #, //, and whitespace
            filename = re.sub(r'^[#/\s]+', '', match.group(1).strip())
            code_content = match.group(2).strip()
            
            # Basic validation
            if not filename.endswith('.py'):
                logger.warning(f"Skipping non-Python file: {filename}")
                continue
                
            if not code_content:
                logger.warning(f"Empty code block found for {filename}")
                continue

            logger.info(f"Found code block for file: {filename}")
            code_blocks.append((filename, code_content))
    if not code_blocks:
        logger.warning("No valid code blocks found in content")
    else:
        logger.info(f"Successfully parsed {len(code_blocks)} code blocks")

    return code_blocks

class CodeParser:
    """Parser for extracting and processing code blocks from LLM output"""
    
    def __init__(self, project_root: Optional[str] = None, min_lines: int = 8):
        """Initialize parser with optional project root directory"""
        self.project_root = project_root
        self.min_lines = min_lines
        
        # Patterns for different comment styles and filenames
        self.filename_patterns = [
            r'^\s*[#/]+\s*([\w/.-]+\.py)\s*$',  # Python/C-style comments with multiple #/
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

    def _extract_filename(self, line: str) -> Optional[str]:
        """Extract filename from a line using various patterns"""
        for pattern in self.filename_patterns:
            match = re.search(pattern, line)
            if match:
                # Strip any leading/trailing whitespace and remove any leading '#' or '//'
                filename = match.group(1).strip()
                filename = re.sub(r'^[#/\s]+', '', filename)
                return filename
        return None

    def _is_incomplete_block(self, content: str) -> bool:
        """Check if code block contains markers indicating it's incomplete"""
        return any(re.search(pattern, content) for pattern in self.incomplete_markers)

    def _has_imports(self, content: str) -> bool:
        """Check if code block contains import statements"""
        import_patterns = [
            r'^\s*import\s+\w+',
            r'^\s*from\s+[\w.]+\s+import\s+',
        ]
        return any(re.search(pattern, content, re.MULTILINE) for pattern in import_patterns)

    def _get_context(self, lines: List[str], block_start: int, block_end: int) -> Tuple[str, str]:
        """Get 20 lines of context before and after the code block"""
        context_before = '\n'.join(lines[max(0, block_start - 20):block_start])
        context_after = '\n'.join(lines[block_end:min(len(lines), block_end + 20)])
        return context_before, context_after

    def _find_project_file(self, filename: str) -> Optional[str]:
        """Find full path of file in project directory"""
        if not self.project_root:
            return None
        file_path = os.path.join(self.project_root, filename)
        return file_path if os.path.exists(file_path) else None

    def _finalize_block(self, block_info: dict, lines: List[str]) -> CodeBlock:
        """
        Create a CodeBlock instance with all necessary metadata.
        Improved version that combines functionality from both versions.
        """
        content = block_info['content']
        
        # Clean up content
        content_lines = content.split('\n')
        while content_lines and not content_lines[0].strip():
            content_lines.pop(0)
        while content_lines and not content_lines[-1].strip():
            content_lines.pop(-1)
        
        cleaned_content = '\n'.join(content_lines)
        
        # Get context
        context_before, context_after = self._get_context(
            lines, block_info['start_line'], block_info['end_line']
        )
        
        is_complete = not self._is_incomplete_block(cleaned_content)
        has_imports = self._has_imports(cleaned_content)
        line_count = len([l for l in content_lines if l.strip()])
        project_path = self._find_project_file(block_info['filename'])

        return CodeBlock(
            filename=block_info['filename'],
            content=cleaned_content,
            is_complete=is_complete,
            line_number=block_info['start_line'],
            context_before=context_before,
            context_after=context_after,
            has_imports=has_imports,
            line_count=line_count,
            project_path=project_path
        )

    def parse_code_blocks(self, content: str) -> Dict[str, List[CodeBlock]]:
        """
        Parse code blocks from content, handling multiple formats and patterns.
        Returns dictionary with two lists: 'update' and 'manual_update'
        """
        lines = content.split('\n')
        blocks: Dict[str, List[CodeBlock]] = {
            'update': [],
            'manual_update': []
        }
        
        current_block = None
        in_markdown_fence = False
        current_filename = None  # Track the current filename separately
        
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            
            # Check for new file markers first
            filename = self._extract_filename(line)
            if filename:
                # If we were building a block, finalize it before starting new one
                if current_block:
                    current_block['end_line'] = i - 1
                    block = self._finalize_block(current_block, lines)
                    if block.is_complete and block.line_count >= self.min_lines and block.has_imports:
                        blocks['update'].append(block)
                    else:
                        blocks['manual_update'].append(block)
                        self._handle_small_block(block)
                
                current_filename = filename
                if not in_markdown_fence:
                    # Start new block immediately for non-markdown blocks
                    current_block = {
                        'filename': filename,
                        'content': '',
                        'start_line': i + 1,
                        'end_line': None
                    }
                continue
            
            # Handle markdown code fences
            if stripped_line.startswith('```'):
                if in_markdown_fence:
                    # End of markdown block
                    if current_block:
                        current_block['end_line'] = i
                        block = self._finalize_block(current_block, lines)
                        if block.is_complete and block.line_count >= self.min_lines and block.has_imports:
                            blocks['update'].append(block)
                        else:
                            blocks['manual_update'].append(block)
                            self._handle_small_block(block)
                        current_block = None
                else:
                    # Start of markdown block - if we have a filename waiting, create the block
                    if current_filename:
                        current_block = {
                            'filename': current_filename,
                            'content': '',
                            'start_line': i + 1,
                            'end_line': None
                        }
                in_markdown_fence = not in_markdown_fence
                continue
            
            # Add content to current block if we have one and we're either:
            # 1. Inside a markdown fence, or
            # 2. Not in a markdown block and the line isn't empty
            if current_block is not None and (in_markdown_fence or stripped_line):
                current_block['content'] += line + '\n'
        
        # Handle any remaining block
        if current_block:
            current_block['end_line'] = len(lines)
            block = self._finalize_block(current_block, lines)
            if block.is_complete and block.line_count >= self.min_lines and block.has_imports:
                blocks['update'].append(block)
            else:
                blocks['manual_update'].append(block)
                self._handle_small_block(block)

        return blocks

    def _handle_small_block(self, block: CodeBlock):
        """Handle blocks that are too small for automated update"""
        try:
            pyperclip.copy(block.to_clipboard_format())
            logger.info(
                f"Small code block ({block.line_count} lines) for {block.filename} "
                f"copied to clipboard with context"
            )
        except Exception as e:
            logger.error(f"Error copying to clipboard: {e}")
