import os
import json
from datetime import datetime
from typing import Dict, Any

class ReportGenerator:
    def __init__(self, report_dir: str):
        """Initialize ReportGenerator with output directory."""
        self.report_dir = report_dir
        os.makedirs(report_dir, exist_ok=True)

    def generate_markdown_report(
        self,
        update_summary: Dict[str, Any],
        task_summary: Dict[str, int],
        test_results: Dict[str, Any],
        backup_timestamp: str
    ) -> str:
        """Generate a markdown report with all update information."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = os.path.join(self.report_dir, f'update_report_{timestamp}.md')
        
        with open(report_path, 'w') as f:
            # Header
            f.write("# Code Update Report\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Backup Reference: {backup_timestamp}\n\n")
            
            # Update Summary
            f.write("## Update Summary\n")
            if update_summary['files_updated'] == 0 and update_summary['files_skipped'] == 0:
                f.write("No files were updated\n")
            else:
                f.write(f"- Files Updated: {update_summary['files_updated']}\n")
                f.write(f"- Files Skipped: {update_summary['files_skipped']}\n")
                f.write(f"- Error Files: {len(update_summary['error_files'])}\n")
            
            # Task Status
            f.write("\n## Task Status\n")
            if task_summary['total'] == 0:
                f.write("No tasks were processed\n")
            else:
                f.write(f"- Total Tasks: {task_summary['total']}\n")
                f.write(f"- Pending: {task_summary['pending']}\n")
                f.write(f"- Updated: {task_summary['updated']}\n")
                f.write(f"- Skipped: {task_summary['skipped']}\n")
                f.write(f"- Errors: {task_summary['error']}\n")
            
            # Test Results
            f.write("\n## Test Results\n")
            status = "✅ All tests passed" if test_results['tests_passed'] else "❌ Some tests failed"
            f.write(f"Status: {status}\n")
            f.write(f"- Total Tests: {test_results['total_tests']}\n")
            f.write(f"- Failed Tests: {test_results['failed_tests']}\n")
            f.write("\n### Test Output\n")
            f.write(f"```\n{test_results['test_output']}\n```\n")
            
            # Error Details
            if update_summary['error_files']:
                f.write("\n## Error Details\n")
                for file_path, error in update_summary['error_files'].items():
                    f.write(f"### {file_path}\n")
                    f.write(f"Error: {error}\n\n")
        
        return report_path

    def generate_json_report(
        self,
        update_summary: Dict[str, Any],
        task_summary: Dict[str, int],
        test_results: Dict[str, Any],
        backup_timestamp: str
    ) -> str:
        """Generate a JSON report with all update information."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = os.path.join(self.report_dir, f'update_report_{timestamp}.json')
        
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'backup_reference': backup_timestamp,
            'update_summary': update_summary,
            'task_summary': task_summary,
            'test_results': test_results
        }
        
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        return report_path

    def generate_error_report(self, error_files: Dict[str, str]) -> str:
        """Generate a detailed error report."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = os.path.join(self.report_dir, f'error_report_{timestamp}.txt')
        
        with open(report_path, 'w') as f:
            f.write("Code Update Error Report\n")
            f.write("=" * 50 + "\n\n")
            
            if not error_files:
                f.write("No errors were encountered during the update process.\n")
            else:
                f.write(f"Total Errors: {len(error_files)}\n\n")
                for file_path, error in error_files.items():
                    f.write(f"File: {file_path}\n")
                    f.write(f"Error: {error}\n")
                    f.write("-" * 50 + "\n")
        
        return report_path
