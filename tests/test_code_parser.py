import unittest
import os
from textwrap import dedent
import pytest
from llmcodeupdater.code_parser import CodeParser, parse_code_blocks_with_logging, CodeBlock

class TestCodeParser(unittest.TestCase):
    def setUp(self):
        self.parser = CodeParser()

    def test_basic_code_block(self):
        content = dedent("""
            ```python
            # test.py
            def hello():
                print("Hello")
            ```
        """).strip()
        
        blocks = self.parser.parse_code_blocks(content)
        self.assertEqual(len(blocks['manual_update']), 1)
        self.assertEqual(blocks['manual_update'][0].filename, "test.py")
        self.assertTrue(blocks['manual_update'][0].is_complete)
    
    def test_markdown_code_block(self):
        content = dedent("""
            Here's the code:
            
            ```python
            # utils.py
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
            ```python
            # one.py
            def first(): pass
            
            # two.py
            def second(): pass
            ```
        """).strip()
        
        blocks = self.parser.parse_code_blocks(content)
        filenames = {b.filename for b in blocks['manual_update']}
        self.assertEqual(filenames, {"one.py", "two.py"})
    
    def test_incomplete_block(self):
        content = dedent("""
            ```python
            # partial.py
            def start():
                pass
                
            # rest of implementation remains unchanged
            ```
        """).strip()
        
        blocks = self.parser.parse_code_blocks(content)
        self.assertEqual(len(blocks['manual_update']), 1)
        self.assertFalse(blocks['manual_update'][0].is_complete)
    
    def test_nested_paths(self):
        content = dedent("""
            ```python
            # utils/helpers/math.py
            def calculate(): pass
            ```
        """).strip()
        
        blocks = self.parser.parse_code_blocks(content)
        self.assertEqual(blocks['manual_update'][0].filename, "utils/helpers/math.py")

    def test_import_detection(self):
        content = dedent("""
            ```python
            # repository.py
            import os
            from datetime import datetime
            
            def process():
                pass
            ```
        """).strip()
        
        blocks = self.parser.parse_code_blocks(content)
        self.assertEqual(len(blocks['manual_update']), 1)
        self.assertTrue(blocks['manual_update'][0].has_imports)
    
    def test_line_count(self):
        content = dedent("""
            ```python
            # long.py
            import os
            
            def func1():
                pass
                
            def func2():
                pass
                
            def func3():
                pass
            ```
        """).strip()
        
        blocks = self.parser.parse_code_blocks(content)
        self.assertEqual(len(blocks['update']), 1)
        self.assertTrue(blocks['update'][0].line_count >= 8)

class TestCodeParserEdgeCases:
    @pytest.fixture
    def parser(self):
        return CodeParser(min_lines=8)
        
    def test_no_fence_blocks(self, parser):
        """Test parsing content without code fences"""
        content = dedent("""
            # test.py
            def no_fence():
                pass
        """).strip()
        
        blocks = parser.parse_code_blocks(content)
        assert len(blocks['manual_update']) == 1
        assert blocks['manual_update'][0].filename == "test.py"
        
    def test_empty_content(self, parser):
        """Test handling empty content"""
        blocks = parser.parse_code_blocks("")
        assert len(blocks['update']) == 0
        assert len(blocks['manual_update']) == 0
        
    def test_malformed_blocks(self, parser):
        """Test handling malformed code blocks"""
        content = dedent("""
            ```python
            Not a proper file block
            def broken():
                pass
            ```
        """).strip()
        
        blocks = parser.parse_code_blocks(content)
        assert len(blocks['update']) == 0
        assert len(blocks['manual_update']) == 0

    def test_legacy_wrapper_compatibility(self):
        """Test that legacy wrapper maintains backward compatibility"""
        content = dedent("""
            ```python
            # test.py
            import sys
            import os
            
            def func1(): pass
            def func2(): pass
            def func3(): pass
            def func4(): pass
            def func5(): pass
            ```
        """).strip()
        
        result = parse_code_blocks_with_logging(content)
        assert len(result) == 1
        filename, code = result[0]
        assert filename == "test.py"
        assert "import sys" in code