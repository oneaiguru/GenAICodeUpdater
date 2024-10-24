
import filecmp
import subprocess
from typing import List, Dict

def compare_files(updated_file: str, backup_file: str) -> bool:
    return not filecmp.cmp(updated_file, backup_file, shallow=False)

def run_unit_tests(project_root: str) -> Dict[str, bool]:
    try:
        result = subprocess.run(['python', '-m', 'unittest', 'discover', project_root], capture_output=True, text=True)
        success = result.returncode == 0
        return {'success': success, 'output': result.stdout}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def generate_validation_report(comparison_results: List[Dict[str, str]], test_results: Dict[str, bool]) -> str:
    report = "Validation Report:\n"
    report += "-" * 20 + "\n"
    for result in comparison_results:
        report += f"File: {result['file']}, Status: {result['status']}\n"
    
    if test_results['success']:
        report += "All tests passed successfully.\n"
    else:
        report += "Test failures detected.\n"
        if 'output' in test_results:
            report += f"Test Output: {test_results['output']}\n"
        if 'error' in test_results:
            report += f"Error: {test_results['error']}\n"
    
    return report
    