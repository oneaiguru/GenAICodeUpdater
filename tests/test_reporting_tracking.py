# tests/test_reporting_tracking.py
import unittest
import os
import tempfile
import json
from llmcodeupdater.reporting import ReportGenerator

class TestReportGenerator(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.report_generator = ReportGenerator(self.temp_dir)
        
        # Sample data for testing
        self.update_summary = {
            'files_updated': 5,
            'files_skipped': 2,
            'error_files': {
                'path/to/file1.py': 'Permission denied',
                'path/to/file2.py': 'Syntax error'
            }
        }
        
        self.task_summary = {
            'total': 10,
            'pending': 1,
            'updated': 5,
            'skipped': 2,
            'error': 2
        }
        
        self.test_results = {
            'tests_passed': True,
            'total_tests': 15,
            'failed_tests': 0,
            'test_output': 'All tests passed successfully'
        }

    def tearDown(self):
        for file in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, file))
        os.rmdir(self.temp_dir)

    def test_generate_markdown_report(self):
        report_path = self.report_generator.generate_markdown_report(
            self.update_summary,
            self.task_summary,
            self.test_results,
            'backup_20241024'
        )
        
        self.assertTrue(os.path.exists(report_path))
        with open(report_path, 'r') as f:
            content = f.read()
            # Check basic structure
            self.assertIn("# Code Update Report", content)
            self.assertIn("## Update Summary", content)
            self.assertIn("## Task Status", content)
            self.assertIn("## Test Results", content)
            
            # Check specific details
            self.assertIn("Files Updated: 5", content)
            self.assertIn("Files Skipped: 2", content)
            self.assertIn("Error Files: 2", content)
            
            # Check task summary
            self.assertIn("Total Tasks: 10", content)
            self.assertIn("Pending: 1", content)
            
            # Check test results
            self.assertIn("Total Tests: 15", content)
            self.assertIn("✅ All tests passed", content)

    def test_generate_json_report(self):
        report_path = self.report_generator.generate_json_report(
            self.update_summary,
            self.task_summary,
            self.test_results,
            'backup_20241024'
        )
        
        self.assertTrue(os.path.exists(report_path))
        import json
        with open(report_path, 'r') as f:
            data = json.load(f)
            self.assertEqual(data['update_summary']['files_updated'], 5)
            self.assertEqual(data['task_summary']['total'], 10)
            self.assertEqual(data['test_results']['total_tests'], 15)

    def test_generate_error_report(self):
        error_report_path = self.report_generator.generate_error_report(
            self.update_summary['error_files']
        )
        
        self.assertTrue(os.path.exists(error_report_path))
        with open(error_report_path, 'r') as f:
            content = f.read()
            self.assertIn("path/to/file1.py", content)
            self.assertIn("Permission denied", content)

    def test_handle_empty_summaries(self):
        empty_summary = {
            'files_updated': 0,
            'files_skipped': 0,
            'error_files': {}
        }
        
        report_path = self.report_generator.generate_markdown_report(
            empty_summary,
            {'total': 0, 'pending': 0, 'updated': 0, 'skipped': 0, 'error': 0},
            {'tests_passed': True, 'total_tests': 0, 'failed_tests': 0, 'test_output': ''},
            'backup_20241024'
        )
        
        self.assertTrue(os.path.exists(report_path))
        with open(report_path, 'r') as f:
            content = f.read()
            self.assertIn("No files were updated", content)
            self.assertIn("No tasks were processed", content)

if __name__ == '__main__':
    unittest.TextTestRunner().run(unittest.TestLoader().loadTestsFromTestCase(TestReportGenerator))
