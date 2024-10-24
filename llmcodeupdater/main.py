# llmcodeupdater/main.py

import os
import shutil
from datetime import datetime
from .task_tracking import TaskTracker
from .code_parser import parse_code_blocks_with_logging
from .mapping import update_files
from .backup import backup_files
from .reporting import ReportGenerator
from .logger import setup_logger
from .validation import generate_report

def map_code_blocks_to_paths(parsed_blocks, project_root):
    """Map parsed code blocks to their corresponding file paths."""
    mapped_updates = []
    for filename, code_block in parsed_blocks:
        full_path = os.path.join(project_root, filename)
        mapped_updates.append((full_path, code_block))
    return mapped_updates

def validate_updates(backup_dir, project_root, test_directory):
    """Validate the updates by comparing files and running tests."""
    import pytest
    
    mismatched_files = []
    for root, _, files in os.walk(backup_dir):
        for file in files:
            backup_file = os.path.join(root, file)
            project_file = os.path.join(project_root, os.path.relpath(backup_file, backup_dir))
            
            if os.path.exists(project_file):
                with open(backup_file, 'r') as bf, open(project_file, 'r') as pf:
                    if bf.read() != pf.read():
                        mismatched_files.append(os.path.relpath(project_file, project_root))
    
    # Run tests
    test_result = pytest.main([test_directory])
    tests_passed = test_result == 0
    
    return {
        'mismatched_files': mismatched_files,
        'tests_passed': tests_passed,
        'test_output': 'Test execution complete'
    }

def main(zip_file_path: str, project_root: str, backup_root: str, report_directory: str, 
         db_path: str, test_directory: str):
    """
    Main function to orchestrate the code update process.
    """
    extraction_path = 'temp_extracted'
    os.makedirs(extraction_path, exist_ok=True)
    os.makedirs(backup_root, exist_ok=True)
    os.makedirs(report_directory, exist_ok=True)
    
    # Setup logging
    log_file = os.path.join(report_directory, 'update_tool.log')
    logger = setup_logger('update_tool', log_file)
    
    try:
        logger.info("Starting code update process.")
        
        # Initialize Task Tracker
        tracker = TaskTracker(db_path)
        
        # Fetch all .py files in the project root
        py_files = []
        for root, dirs, files in os.walk(project_root):
            for file in files:
                if file.endswith('.py'):
                    py_files.append(os.path.join(root, file))
        tracker.add_tasks(py_files)
        
        # Parse code blocks
        parsed_blocks = []
        for file_path in py_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                parsed = parse_code_blocks_with_logging(content)
                parsed_blocks.extend(parsed)
        
        # Map code blocks to file paths
        mapped_updates = map_code_blocks_to_paths(parsed_blocks, project_root)
        
        # Backup original files
        files_to_backup = [path for path, _ in mapped_updates]
        backup_count = backup_files(files_to_backup, project_root, backup_root)
        
        # Apply updates
        update_result = update_files(mapped_updates)
        
        # Get latest backup timestamp
        backup_timestamps = sorted(os.listdir(backup_root))
        if not backup_timestamps:
            logger.error("No backups found for validation.")
            return
        
        backup_timestamp = backup_timestamps[-1]
        original_backup_dir = os.path.join(backup_root, backup_timestamp)
        
        # Validate updates
        validation_results = validate_updates(original_backup_dir, project_root, test_directory)
        
        # Generate reports
        report_generator = ReportGenerator(report_directory)
        task_summary = tracker.get_task_summary()
        
        test_results = {
            'tests_passed': validation_results['tests_passed'],
            'total_tests': len(py_files),
            'failed_tests': 0 if validation_results['tests_passed'] else 1,
            'test_output': validation_results['test_output']
        }
        
        report_generator.generate_markdown_report(
            update_result,
            task_summary,
            test_results,
            backup_timestamp
        )
        
        # Update task statuses
        for file_path in files_to_backup:
            relative_path = os.path.relpath(file_path, project_root)
            if relative_path in validation_results['mismatched_files']:
                tracker.update_task_status(file_path, 'error', 'Mismatch after update')
            elif any(update[0] == file_path for update in mapped_updates):
                tracker.update_task_status(file_path, 'updated')
            else:
                tracker.update_task_status(file_path, 'skipped')
        
        logger.info("Code update process completed successfully.")
    
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
    finally:
        # Cleanup extraction directory
        if os.path.exists(extraction_path):
            shutil.rmtree(extraction_path)
        logger.info("Cleanup complete.")

if __name__ == "__main__":
    main(
        zip_file_path='path/to/llm_outputs.zip',
        project_root='path/to/project',
        backup_root='path/to/backups',
        report_directory='path/to/reports',
        db_path='path/to/update_tasks.db',
        test_directory='path/to/tests'
    )
