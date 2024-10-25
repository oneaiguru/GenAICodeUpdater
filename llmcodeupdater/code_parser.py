import re
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CodeBlock:
    filename: str
    content: str
    context_before: str = ""
    context_after: str = ""
    project_path: Optional[str] = None
    
    @property
    def line_count(self) -> int:
        return len(self.content.splitlines())
    
    @property
    def has_imports(self) -> bool:
        return bool(re.search(r'^(?:import|from)\s+\w+', self.content, re.MULTILINE))
    
    @property
    def is_complete(self) -> bool:
        return not bool(re.search(r'#.*rest.*unchanged|#.*implementation.*unchanged', self.content, re.MULTILINE))

class CodeParser:
    def __init__(self, project_root: Optional[str] = None, min_lines: int = 8):
        self.project_root = project_root
        self.min_lines = min_lines
    
    def parse_code_blocks(self, content: str) -> Dict[str, List[CodeBlock]]:
        """
        Parse code blocks from content looking for # filename.py markers inside Python code fences.
        Returns a dictionary with two lists of CodeBlocks:
        - 'update': Blocks that can be automatically updated (has imports and >= min_lines)
        - 'manual_update': Blocks that need manual review (small or no imports)
        """
        if not content:
            logger.warning("Empty content provided")
            return {'update': [], 'manual_update': []}

        blocks = {'update': [], 'manual_update': []}
        
        # Find all fenced Python code blocks
        fence_pattern = r'```python\s*\n(.*?)```'
        content_with_fences = content
        
        # If no fences found, treat entire content as a code block
        if '```python' not in content:
            content_with_fences = f"```python\n{content}\n```"
            
        for match in re.finditer(fence_pattern, content_with_fences, re.DOTALL):
            fenced_content = match.group(1).strip()
            # Get context before and after the fence
            start_pos = match.start()
            end_pos = match.end()
            context_before = content_with_fences[max(0, start_pos-200):start_pos].strip()
            context_after = content_with_fences[end_pos:min(len(content_with_fences), end_pos+200)].strip()
            
            # Split on Python-style comments that look like filenames
            file_blocks = re.split(r'\n(?=# [\w/.-]+\.py)', '\n' + fenced_content)
            
            for block in file_blocks:
                if not block.strip():
                    continue
                    
                # Extract filename and code content
                match = re.match(r'#\s*([\w/.-]+\.py)\s*\n(.*)', block.strip(), re.DOTALL)
                if not match:
                    continue
                    
                filename = match.group(1).strip()
                code_content = match.group(2).strip()
                
                if not code_content:
                    logger.warning(f"Empty code block found for {filename}")
                    continue
                
                # Create CodeBlock object
                code_block = CodeBlock(
                    filename=filename,
                    content=code_content,
                    context_before=context_before,
                    context_after=context_after,
                    project_path=f"{self.project_root}/{filename}" if self.project_root else None
                )
                
                # Determine if block can be automatically updated
                if code_block.line_count >= self.min_lines and code_block.has_imports:
                    blocks['update'].append(code_block)
                else:
                    blocks['manual_update'].append(code_block)
                
                logger.info(f"Parsed code block for {filename} ({code_block.line_count} lines)")
        
        return blocks

def parse_code_blocks_with_logging(content: str) -> List[tuple[str, str]]:
    """Legacy wrapper for backward compatibility"""
    parser = CodeParser(min_lines=8)
    blocks = parser.parse_code_blocks(content)
    
    # Only return blocks that are complete and meet minimum line requirements
    result = []
    for block in blocks['update']:
        if block.is_complete:
            result.append((block.filename, block.content))
            
    for block in blocks['manual_update']:
        if block.is_complete and block.line_count >= 8:
            result.append((block.filename, block.content))
            
    return result