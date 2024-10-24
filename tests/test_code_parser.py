import unittest
from llmcodeupdater.code_parser import parse_code_blocks_with_logging

class TestParsingModuleExtended(unittest.TestCase):
    
    def test_incomplete_comment(self):
        content = "# utils/incomplete.py"
        result = parse_code_blocks_with_logging(content)
        self.assertEqual(len(result), 0, "Should return no code blocks for incomplete comment")
    
    def test_malformed_comment(self):
        content = "# This is not a valid filename comment\nprint('Hello')"
        result = parse_code_blocks_with_logging(content)
        self.assertEqual(len(result), 0, "Should ignore malformed comments")

    def test_code_without_comment(self):
        content = "print('This code has no associated comment')"
        result = parse_code_blocks_with_logging(content)
        self.assertEqual(len(result), 0, "Should return no blocks when there is no filename comment")

    def test_multiple_code_blocks_with_placeholders(self):
        content = '''
# utils/redis_manager.py
import redis.asyncio as redis
class RedisManager:
    # rest of methods are not changed
    pass
# utils/logger.py
import logging
class LoggerManager:
    pass
'''
        result = parse_code_blocks_with_logging(content)
        self.assertEqual(len(result), 2, "Should extract two code blocks")

    def test_empty_code_block(self):
        content = "# utils/empty_block.py"
        result = parse_code_blocks_with_logging(content)
        self.assertEqual(len(result), 0, "Should return no code blocks for an empty code block")

    def test_code_with_markdown_block(self):
        content = '''
# utils/example.py
print('This is a code block')
'''
        result = parse_code_blocks_with_logging(content)
        self.assertEqual(len(result), 1, "Should extract one code block with a filename comment")
        self.assertEqual(result[0][0], 'utils/example.py', "Filename should match")

# Run the tests
if __name__ == '__main__':
    unittest.main()
