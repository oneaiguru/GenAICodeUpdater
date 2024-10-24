import unittest
import os
from llmcodeupdater.validation import generate_report

class TestReportingModuleExtended(unittest.TestCase):
    def setUp(self):
        self.validation_results = {
            'files_updated': 5,
            'files_skipped': 2,
            'mismatched_files': [],
            'tests_passed': True,
            'test_output': 'Ran 10 tests in 0.002s\n\nOK'
        }
        self.backup_timestamp = '20231024120000'
        self.target_path = '/path/to/updated_files'
        self.report_path = 'report.md'

    def tearDown(self):
        if os.path.exists(self.report_path):
            os.remove(self.report_path)

    def test_generate_report_success(self):
        report = generate_report(self.validation_results, self.backup_timestamp, self.target_path, self.report_path)
        self.assertTrue(os.path.isfile(report))
        with open(report, 'r') as f:
            content = f.read()
            self.assertIn("# Code Update Report", content)
            self.assertIn("Backup Timestamp: 20231024120000", content)
            self.assertIn("- Files Updated: 5", content)
            self.assertIn("- Files Skipped: 2", content)
            self.assertIn("- Mismatched Files: 0", content)
            self.assertIn("- Tests Passed: True", content)
            self.assertIn("✅ Success", content)

    def test_generate_report_failure(self):
        self.validation_results['tests_passed'] = False
        self.validation_results['mismatched_files'] = ['utils/redis_manager.py']
        report = generate_report(self.validation_results, self.backup_timestamp, self.target_path, self.report_path)
        self.assertTrue(os.path.isfile(report))
        with open(report, 'r') as f:
            content = f.read()
            self.assertIn("❌ Failed", content)

    def test_generate_report_missing_fields(self):
        del self.validation_results['mismatched_files']
        del self.validation_results['test_output']
        report = generate_report(self.validation_results, self.backup_timestamp, self.target_path, self.report_path)
        self.assertTrue(os.path.isfile(report))
        with open(report, 'r') as f:
            content = f.read()
            self.assertIn("- Mismatched Files: 0", content)
            self.assertIn("- Test Output:\n\n\n", content)

    def test_handle_file_write_error(self):
        invalid_report_path = '/invalid_path/report.md'
        with self.assertRaises(OSError, msg="Expected OSError due to invalid file path"):
            generate_report(self.validation_results, self.backup_timestamp, self.target_path, invalid_report_path)

unittest.TextTestRunner().run(unittest.makeSuite(TestReportingModuleExtended))
