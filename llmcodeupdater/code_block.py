# llmcodeupdater/code_block.py

from dataclasses import dataclass
from typing import Optional

@dataclass
class CodeBlock:
    """Represents a parsed code block with metadata"""
    filename: str
    content: str
    is_complete: bool
    line_number: int
    context_before: str  # 20 lines before
    context_after: str   # 20 lines after
    has_imports: bool
    line_count: int
    project_path: Optional[str] = None

    def to_clipboard_format(self) -> str:
        """Create formatted content for clipboard with context and highlighted block"""
        return f"""
// Context before:
{self.context_before}

// Your code block to update ({self.filename}):
{self.content}

// Context after:
{self.context_after}
"""

    @property
    def needs_manual_update(self) -> bool:
        """Determine if block requires manual update based on size and completeness"""
        return not self.is_complete or self.line_count < 8

    @property
    def is_valid(self) -> bool:
        """Check if the code block is valid for processing"""
        return bool(self.filename and self.content.strip())