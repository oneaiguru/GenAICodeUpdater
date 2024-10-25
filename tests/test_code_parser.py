# tests/test_code_parser.py
#  Unit tests for the code parser
import unittest
from textwrap import dedent
from llmcodeupdater.code_parser import CodeParser, parse_code_blocks_with_logging
import os

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
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].filename, "test.py")
        self.assertTrue(blocks[0].is_complete)
    
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
        self.assertEqual(len(blocks), 1)
        self.assertIn("def add", blocks[0].content)
        self.assertTrue(blocks[0].is_complete)
    
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
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0].filename, "one.py")
        self.assertEqual(blocks[1].filename, "two.py")
    
    def test_incomplete_block(self):
        content = dedent("""
            # partial.py
            def start():
                pass
                
            # rest of implementation remains unchanged
        """).strip()
        
        blocks = self.parser.parse_code_blocks(content)
        self.assertEqual(len(blocks), 1)
        self.assertFalse(blocks[0].is_complete)
    
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
        self.assertEqual(len(blocks), 3)
        self.assertEqual(
            {b.filename for b in blocks},
            {"python_file.py", "cpp_style.py", "bare_file.py"}
        )
    
    def test_nested_paths(self):
        content = dedent("""
            # utils/helpers/math.py
            def calculate(): pass
        """).strip()
        
        blocks = self.parser.parse_code_blocks(content)
        self.assertEqual(blocks[0].filename, "utils/helpers/math.py")
    
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
            self.assertEqual(len(blocks), 1)
            self.assertEqual(
                blocks[0].project_path,
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
        self.assertEqual(len(result), 1)  # Only complete blocks
        self.assertEqual(result[0][0], "complete.py")

if __name__ == '__main__':
    unittest.main()