# tests/test_code_parser.py
import unittest
import os
from textwrap import dedent
import pytest
from llmcodeupdater.code_block import CodeBlock
from llmcodeupdater.code_parser import CodeParser, parse_code_blocks_with_logging

# Regular unittest test class
class TestCodeParser(unittest.TestCase):
    def setUp(self):
        self.parser = CodeParser()

    def test_basic_code_block(self):
        content = dedent("""
            # test.py
            def hello():
                print("Hello")
        """).strip()
        
        blocks = self.parser.parse_code_blocks(content)
        self.assertEqual(len(blocks['manual_update']), 1)
        self.assertEqual(blocks['manual_update'][0].filename, "test.py")
        self.assertTrue(blocks['manual_update'][0].is_complete)
    
    def test_markdown_code_block(self):
        content = dedent("""
            Here's the code:
            
            # utils.py
            ```python
            def add(a, b):
                return a + b
            ```
        """).strip()
        
        blocks = self.parser.parse_code_blocks(content)
        self.assertEqual(len(blocks['manual_update']), 1)
        self.assertIn("def add", blocks['manual_update'][0].content)
        self.assertTrue(blocks['manual_update'][0].is_complete)
    
    def test_multiple_blocks(self):
        content = dedent("""
            First file:
            # one.py
            def first(): pass
            
            Second file:
            # two.py
            def second(): pass
        """).strip()
        
        blocks = self.parser.parse_code_blocks(content)
        filenames = {b.filename for b in blocks['manual_update']}
        self.assertEqual(filenames, {"one.py", "two.py"})
    
    def test_incomplete_block(self):
        content = dedent("""
            # partial.py
            def start():
                pass
                
            # rest of implementation remains unchanged
        """).strip()
        
        blocks = self.parser.parse_code_blocks(content)
        self.assertEqual(len(blocks['manual_update']), 1)
        self.assertFalse(blocks['manual_update'][0].is_complete)
    
    def test_different_comment_styles(self):
        content = dedent("""
            # python_file.py
            def py(): pass
            
            // cpp_style.py
            def cpp(): pass
            
            bare_file.py
            def bare(): pass
        """).strip()
        
        blocks = self.parser.parse_code_blocks(content)
        filenames = {b.filename for b in blocks['manual_update']}
        self.assertEqual(
            filenames,
            {"python_file.py", "cpp_style.py", "bare_file.py"}
        )
    
    def test_nested_paths(self):
        content = dedent("""
            # utils/helpers/math.py
            def calculate(): pass
        """).strip()
        
        blocks = self.parser.parse_code_blocks(content)
        self.assertEqual(blocks['manual_update'][0].filename, "utils/helpers/math.py")
    
    def test_project_path_resolution(self):
        # Create temporary project structure
        import tempfile
        import shutil
        
        temp_dir = tempfile.mkdtemp()
        try:
            # Create nested structure
            os.makedirs(os.path.join(temp_dir, "utils"))
            with open(os.path.join(temp_dir, "utils", "helper.py"), "w") as f:
                f.write("# existing file")
            
            parser = CodeParser(project_root=temp_dir)
            content = "# utils/helper.py\ndef new_function(): pass"
            
            blocks = parser.parse_code_blocks(content)
            self.assertEqual(len(blocks['manual_update']), 1)
            self.assertEqual(
                blocks['manual_update'][0].project_path,
                os.path.join(temp_dir, "utils", "helper.py")
            )
            
        finally:
            shutil.rmtree(temp_dir)
    
    def test_legacy_wrapper(self):
        content = dedent("""
            # complete.py
            def works(): pass
            
            # incomplete.py
            def partial():
                # rest of implementation unchanged
        """).strip()
        
        result = parse_code_blocks_with_logging(content)
        self.assertEqual(len(result), 0)  # No complete blocks over min_lines

    def test_filename_cleanup(self):
        """Test that filenames are properly cleaned of prefixes"""
        content = dedent("""
            # main.py
            def test(): pass
            
            // utils.py
            def util(): pass
            
            ### helper.py
            def help(): pass
        """).strip()
        
        blocks = self.parser.parse_code_blocks(content)
        filenames = {b.filename for b in blocks['manual_update']}
        self.assertEqual(
            filenames,
            {"main.py", "utils.py", "helper.py"}
        )

    def test_filename_with_hash(self):
        """Test that # is properly stripped from filenames"""
        content = "# main.py\ndef main(): pass"
        blocks = self.parser.parse_code_blocks(content)
        self.assertEqual(blocks['manual_update'][0].filename, "main.py")

    def test_legacy_wrapper_filename_cleanup(self):
        """Test that parse_code_blocks_with_logging properly cleans filenames"""
        content = dedent("""
            ```python # main.py
            import os
            import sys
            def main():
                pass
            ```
        """).strip()
        
        result = parse_code_blocks_with_logging(content)
        self.assertEqual(len(result), 1)
        filename, _ = result[0]
        self.assertEqual(filename, "main.py")

# Separate class for pytest-style tests
class TestCodeParserPytest:
    @pytest.fixture
    def parser(self):
        return CodeParser(min_lines=8)

    def test_small_code_block_detection(self, parser):
        content = dedent("""
            # settings.py
            ```python
            ASYNC_DATABASE_URL = os.getenv('DATABASE_URL')
            OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
            ```
            """)
        
        blocks = parser.parse_code_blocks(content)
        assert len(blocks['manual_update']) == 1
        assert len(blocks['update']) == 0
        assert blocks['manual_update'][0].filename == 'settings.py'
        assert blocks['manual_update'][0].line_count < 8

    def test_no_import_detection(self, parser):
        content = dedent("""
            # repository.py
            ```python
            class UserRepository:
                def get_user(self, user_id):
                    return select(User).filter_by(id=user_id)
            ```
            """)
        
        blocks = parser.parse_code_blocks(content)
        assert len(blocks['manual_update']) == 1
        assert blocks['manual_update'][0].has_imports == False

    def test_context_capture(self, parser):
        content = '\n'.join(['line ' + str(i) for i in range(50)])
        content += '\n# test.py\n```python\ntest = "code"\n```\n'
        content += '\n'.join(['line ' + str(i) for i in range(50, 100)])
        
        blocks = parser.parse_code_blocks(content)
        block = blocks['manual_update'][0]
        
        assert len(block.context_before.split('\n')) <= 20
        assert len(block.context_after.split('\n')) <= 20

    def test_import_detection(self, parser):
        content = dedent("""
            # repository.py
            ```python
            import sqlalchemy
            from sqlalchemy import select
            from models import User
            
            class UserRepository:
                def __init__(self):
                    self.db = None
                    
                def get_user(self, user_id):
                    return select(User).filter_by(id=user_id)
                    
                def create_user(self, user_data):
                    return User(**user_data)
            ```
            """)
        
        blocks = parser.parse_code_blocks(content)
        assert len(blocks['update']) == 1
        assert blocks['update'][0].has_imports == True

    def test_large_block_auto_update(self, parser):
        content = dedent("""
            # large_file.py
            ```python
            import os
            import sys
            
            def function1(): pass
            def function2(): pass
            def function3(): pass
            def function4(): pass
            def function5(): pass
            def function6(): pass
            def function7(): pass
            def function8(): pass
            def function9(): pass
            ```
            """)
        
        blocks = parser.parse_code_blocks(content)
        assert len(blocks['update']) == 1
        assert len(blocks['manual_update']) == 0

    def test_incomplete_block_with_marker(self, parser):
        content = dedent("""
            # incomplete_marker.py
            def incomplete_function():
                # rest of implementation remains unchanged
        """).strip()
        
        blocks = parser.parse_code_blocks(content)
        assert len(blocks['manual_update']) == 1
        assert blocks['manual_update'][0].is_complete == False

    def test_import_detection_with_multiple_imports(self, parser):
        content = dedent("""
            # multi_imports.py
            ```python
            import os
            import sys
            from datetime import datetime
            from typing import Optional, List
            
            class MultiImport:
                def __init__(self):
                    self.time = datetime.now()
                    
                def get_time(self):
                    return self.time
                    
                def set_time(self, new_time):
                    self.time = new_time
            ```
            """)
        
        blocks = parser.parse_code_blocks(content)
        assert len(blocks['update']) == 1
        assert blocks['update'][0].has_imports == True

    def test_no_imports_in_empty_block(self, parser):
        content = dedent("""
            # empty_block.py
            ```python
            # This block is empty
            ```
            """)
        
        blocks = parser.parse_code_blocks(content)
        assert len(blocks['manual_update']) == 1
        assert blocks['manual_update'][0].has_imports == False

    def test_large_incomplete_block(self, parser):
        content = dedent("""
            # large_incomplete.py
            ```python
            def large_function():
                # This function is incomplete
                pass
            # rest of implementation remains unchanged
            ```
            """)
        
        blocks = parser.parse_code_blocks(content)
        assert len(blocks['manual_update']) == 1
        assert blocks['manual_update'][0].is_complete == False
