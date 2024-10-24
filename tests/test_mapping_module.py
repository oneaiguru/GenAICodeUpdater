import unittest
import os
import tempfile
import shutil
from llmcodeupdater.mapping import update_files  # Correct import

class TestUpdateModuleExtended(unittest.TestCase):
    def setUp(self):
        self.project_root = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.project_root, 'utils'), exist_ok=True)
        with open(os.path.join(self.project_root, 'utils', 'redis_manager.py'), 'w') as f:
            f.write('# Original RedisManager code')
        with open(os.path.join(self.project_root, 'utils', 'logger.py'), 'w') as f:
            f.write('# Original LoggerManager code')

        self.mapped_updates = [
            (os.path.join(self.project_root, 'utils', 'redis_manager.py'), '# Updated RedisManager code'),
            (os.path.join(self.project_root, 'utils', 'logger.py'), '# rest of methods are not changed')
        ]

    def tearDown(self):
        shutil.rmtree(self.project_root)

    def test_update_files(self):
        result = update_files(self.mapped_updates)
        self.assertEqual(result['files_updated'], 1)
        self.assertEqual(result['files_skipped'], 1)

        with open(os.path.join(self.project_root, 'utils', 'redis_manager.py'), 'r') as f:
            content = f.read()
            self.assertEqual(content, '# Updated RedisManager code')

        with open(os.path.join(self.project_root, 'utils', 'logger.py'), 'r') as f:
            content = f.read()
            self.assertEqual(content, '# Original LoggerManager code')

if __name__ == '__main__':
    unittest.TextTestRunner().run(unittest.makeSuite(TestUpdateModuleExtended))
