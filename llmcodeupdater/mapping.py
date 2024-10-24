import os
from typing import List, Tuple, Dict

def update_files(mapped_updates: List[Tuple[str, str]]) -> dict:
    files_updated = 0
    files_skipped = 0
    for file_path, code_block in mapped_updates:
        if 'rest of' in code_block.lower() or 'do not change' in code_block.lower() or 'manual review' in code_block.lower():
            files_skipped += 1
            continue
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(code_block)
                files_updated += 1
        except PermissionError:
            files_skipped += 1
    return { 'files_updated': files_updated, 'files_skipped': files_skipped }
