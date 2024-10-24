from typing import Dict
import os

def generate_report(validation_results: dict, backup_timestamp: str, target_path: str, report_path: str) -> str:
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"# Code Update Report\n\n")
            f.write(f"Backup Timestamp: {backup_timestamp}\n\n")
            f.write(f"## File Updates\n")
            f.write(f"- Files Updated: {validation_results.get('files_updated', 0)}\n")
            f.write(f"- Files Skipped: {validation_results.get('files_skipped', 0)}\n")
            f.write(f"- Mismatched Files: {len(validation_results.get('mismatched_files', []))}\n")
            if validation_results.get('mismatched_files'):
                f.write(f"  - {', '.join(validation_results['mismatched_files'])}\n")
            f.write(f"\n## Test Results\n")
            f.write(f"- Tests Passed: {validation_results.get('tests_passed', False)}\n")
            f.write(f"- Test Output:\n\n{validation_results.get('test_output', '')}\n\n")
            overall_status = "✅ Success" if validation_results.get('tests_passed', False) and not validation_results.get('mismatched_files') else "❌ Failed"
            f.write(f"## Overall Status\n- {overall_status}\n")
        return report_path
    except OSError as e:
        raise e
