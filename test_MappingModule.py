
import unittest
import os
import tempfile
import shutil
from MappingModule import map_code_blocks_to_paths

class TestMappingModuleExtended(unittest.TestCase):

    def setUp(self):
        self.project_root = tempfile.mkdtemp()

        # Create sample files in the utils directory
        os.makedirs(os.path.join(self.project_root, 'utils'), exist_ok=True)
        with open(os.path.join(self.project_root, 'utils', 'redis_manager.py'), 'w') as f:
            f.write('# Original RedisManager code')
        with open(os.path.join(self.project_root, 'utils', 'logger.py'), 'w') as f:
            f.write('# Original LoggerManager code')
        
        # Add similar files for ambiguous testing
        with open(os.path.join(self.project_root, 'utils', 'redis-manager.py'), 'w') as f:
            f.write('# Similar RedisManager code')

    def tearDown(self):
        shutil.rmtree(self.project_root)

    def test_map_existing_files(self):
        parsed_blocks = [
            ('utils/redis_manager.py', '# Updated RedisManager code'),
            ('utils/logger.py', '# Updated LoggerManager code')
        ]
        result = map_code_blocks_to_paths(parsed_blocks, self.project_root)
        self.assertEqual(len(result), 2)
        self.assertTrue(os.path.isfile(result[0][0]))
        self.assertEqual(result[0][1], '# Updated RedisManager code')
        self.assertTrue(os.path.isfile(result[1][0]))
        self.assertEqual(result[1][1], '# Updated LoggerManager code')

    def test_map_non_existing_file_with_resolution(self):
        parsed_blocks = [
            ('utils/Redis_Manager.py', '# Updated RedisManager code')
        ]
        result = map_code_blocks_to_paths(parsed_blocks, self.project_root)
        self.assertEqual(len(result), 1)
        self.assertTrue(os.path.isfile(result[0][0]))
        self.assertEqual(result[0][1], '# Updated RedisManager code')

    def test_map_non_existing_file_no_resolution(self):
        parsed_blocks = [
            ('utils/non_existing.py', '# Some code')
        ]
        result = map_code_blocks_to_paths(parsed_blocks, self.project_root)
        self.assertEqual(len(result), 0)

    def test_map_with_ambiguous_matches(self):
        parsed_blocks = [
            ('utils/redis_manager.py', '# Updated RedisManager code')
        ]
        result = map_code_blocks_to_paths(parsed_blocks, self.project_root)
        self.assertEqual(len(result), 1)
        self.assertTrue(result[0][0].endswith('redis_manager.py'))

    def test_map_special_characters_in_filenames(self):
        special_filename = 'utils/logger manager.py'
        with open(os.path.join(self.project_root, special_filename), 'w') as f:
            f.write('# Original Logger Manager code')
        
        parsed_blocks = [
            ('utils/Logger_Manager.py', '# Updated Logger Manager code')
        ]
        result = map_code_blocks_to_paths(parsed_blocks, self.project_root)
        self.assertEqual(len(result), 1)
        self.assertTrue(os.path.isfile(result[0][0]))
        self.assertTrue(result[0][0].endswith('logger manager.py'))

if __name__ == '__main__':
    unittest.main()
    