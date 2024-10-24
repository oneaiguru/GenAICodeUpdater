# main_update_tool.py
import os
import shutil
import sqlite3
from datetime import datetime
from modules.file_input_module.LLMCodeFileHandler import LLMCodeFileHandler
from modules.parsing_module.CodeBlockParser import parse_code_blocks
from modules.mapping_module.MappingModule import map_code_blocks_to_paths
from modules.backup_module.backup_module import backup_files
from modules.update_module.update_module import update_files
from modules.validation_module.ValidationModule import validate_updates
from modules.task_tracking_module.TaskTrackingModule import TaskTracker
from modules.reporting_module.ReportingModule import generate_report
from logger_module import setup_logger

def main(zip_file_path: str, project_root: str, backup_root: str, report_directory: str, db_path: str, test_directory: str):
    """
    Main function to orchestrate the code update process.
    
    Args:
        zip_file_path (str): Path to the uploaded zip file containing LLM outputs.
        project_root (str): Root directory of the project codebase.
        backup_root (str): Root directory where backups will be stored.
        report_directory (str): Directory where reports will be saved.
        db_path (str): Path to the SQLite database for task tracking.
        test_directory (str): Directory containing unit tests.
    """
    extraction_path = 'temp_extracted'
    target_path = project_root
    os.makedirs(extraction_path, exist_ok=True)
    os.makedirs(backup_root, exist_ok=True)
    os.makedirs(report_directory, exist_ok=True)
    
    # Setup logging
    log_file = os.path.join(report_directory, 'update_tool.log')
    logger = setup_logger('update_tool', log_file)
    
    try:
        logger.info("Starting code update process.")
        
        # Step 1: Unzip and move files
        move_result = LLMCodeFileHandler.unzip_and_move(zip_file_path, extraction_path, target_path, db_path)
        logger.info(f"Files moved: {move_result['files_moved']}")
        logger.info(f"Database entries: {move_result['db_entries']}")
        
        # Initialize Task Tracker
        tracker = TaskTracker(db_path)
        # Fetch all .py files in the project root to add as tasks
        py_files = []
        for root, dirs, files in os.walk(project_root):
            for file in files:
                if file.endswith('.py'):
                    py_files.append(os.path.join(root, file))
        tracker.add_tasks(py_files)
        
        # Step 2: Parse code blocks
        parsed_blocks = []
        for file_path in py_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                parsed = parse_code_blocks(content)
                parsed_blocks.extend(parsed)
        logger.info(f"Parsed {len(parsed_blocks)} code blocks.")
        
        # Step 3: Map code blocks to file paths
        mapped_updates = map_code_blocks_to_paths(parsed_blocks, project_root)
        logger.info(f"Mapped updates to {len(mapped_updates)} files.")
        
        # Step 4: Backup original files
        files_to_backup = [path for path, code in mapped_updates]
        backup_count = backup_files(files_to_backup, project_root, backup_root)
        logger.info(f"Files backed up: {backup_count}")
        
        # Step 5: Apply updates
        update_result = update_files(mapped_updates)
        logger.info(f"Files updated: {update_result['files_updated']}")
        logger.info(f"Files skipped: {update_result['files_skipped']}")
        
        # Step 6: Validate updates
        # Assume backup timestamp is the latest backup
        backup_timestamps = sorted(os.listdir(backup_root))
        if not backup_timestamps:
            logger.error("No backups found for validation.")
            return
        backup_timestamp = backup_timestamps[-1]
        original_backup_dir = os.path.join(backup_root, backup_timestamp)
        validation_results = validate_updates(original_backup_dir, project_root, test_directory)
        logger.info(f"Validation Results: {validation_results}")
        
        # Step 7: Generate report
        report_path = os.path.join(report_directory, f"update_report_{backup_timestamp}.md")
        generate_report(validation_results, backup_timestamp, project_root, report_path)
        logger.info(f"Report generated at: {report_path}")
        
        # Step 8: Update task statuses
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

# Example usage
if __name__ == "__main__":
    main(
        zip_file_path='/Users/m/Downloads/untitled folder 122/Full_Integrated_With_Reporting_Module/llm_outputs.zip',  # Update with actual zip file path
        project_root='/Users/m/git/lubot',                                                       # Update with actual project root
        backup_root='/Users/m/git/lubot_backups',                                             # Update with actual backup directory
        report_directory='/Users/m/git/lubot_reports',                                        # Update with actual report directory
        db_path='/Users/m/git/lubot/update_tasks.db',                                         # Update with actual database path
        test_directory='/Users/m/git/lubot/tests'                                             # Update with actual test directory
    )
