# main.py

import os
from datetime import datetime
import logging
from llmcodeupdater.task_tracking import TaskTracker
from llmcodeupdater.code_parser import parse_code_blocks_with_logging
from llmcodeupdater.mapping import update_files
from llmcodeupdater.backup import backup_files
from llmcodeupdater.reporting import ReportGenerator
from llmcodeupdater.file_encoding_handler import FileEncodingHandler

def preprocess_files(project_root: str) -> dict:
    """
    Preprocess files to ensure UTF-8 encoding.
    Returns dict with preprocessing results.
    """
    handler = FileEncodingHandler(logger=logging.getLogger('FileEncodingHandler'))
    backup_dir = os.path.join(project_root, 'encoding_backups')
    
    results = handler.process_directory(
        directory=project_root,
        backup_dir=backup_dir
    )
    
    # Log results
    logging.info(f"Encoding conversion results:")
    logging.info(f"Successfully converted: {len(results['successful'])} files")
    logging.info(f"Failed to convert: {len(results['failed'])} files")
    logging.info(f"Already UTF-8 (skipped): {len(results['skipped'])} files")
    
    return results

def main(project_root: str, backup_root: str, report_dir: str, db_path: str, llm_output_file: str):
    """Main function to orchestrate the code update process."""
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger('Main')
    
    # Create necessary directories
    os.makedirs(backup_root, exist_ok=True)
    os.makedirs(report_dir, exist_ok=True)
    
    try:
        # Initialize components
        task_tracker = TaskTracker(db_path)
        report_generator = ReportGenerator(report_dir)
        
        # Step 1: Preprocess files for encoding
        preprocess_results = preprocess_files(project_root)
        if preprocess_results['failed']:
            for fail in preprocess_results['failed']:
                logger.error(f"Failed to convert encoding: {fail['path']}, Error: {fail['error']}")
        
        # Step 2: Collect all Python files
        py_files = []
        for root, _, files in os.walk(project_root):
            for file in files:
                if file.endswith('.py'):
                    py_files.append(file)  # Collect filenames only for mapping
        
        # Step 3: Add tasks to tracker
        task_tracker.add_tasks(py_files)
        
        # Step 4: Create backup
        backup_timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        # Since update_files handles file paths, we pass full paths here
        full_py_files = [os.path.join(project_root, f) for f in py_files]
        files_backed_up = backup_files(full_py_files, project_root, backup_root)
        logger.info(f"Backed up {files_backed_up} files.")
        
        # Step 5: Parse LLM output to get code blocks
        with open(llm_output_file, 'r', encoding='utf-8') as f:
            llm_content = f.read()
        
        code_blocks = parse_code_blocks_with_logging(llm_content)
        
        # Step 6: Process updates
        if not code_blocks:
            logger.warning("No valid code blocks found in LLM output. Exiting update process.")
            return
        
        mapped_updates = []
        for filename, code_block in code_blocks:
            mapped_updates.append((filename, code_block))
        
        update_result = update_files(mapped_updates, project_root)
        
        logger.info(f"Files updated: {update_result['files_updated']}")
        logger.info(f"Files skipped: {update_result['files_skipped']}")
        if update_result.get('errors'):
            logger.error("Errors encountered during file updates:")
            for file_path, error in update_result['errors'].items():
                logger.error(f"  {file_path}: {error}")
        
        if update_result.get('unmatched_files'):
            logger.warning("Unmatched files that were not found in the project directory:")
            for filename in update_result['unmatched_files']:
                logger.warning(f"  {filename}")
        
        # Step 7: Update task statuses
        for filename, _ in mapped_updates:
            task_tracker.update_task_status(filename, 'updated')
        
        # Step 8: Generate reports
        update_summary = {
            'files_updated': update_result['files_updated'],
            'files_skipped': update_result['files_skipped'],
            'error_files': update_result.get('errors', {})
        }
        
        task_summary = task_tracker.get_task_summary()
        
        test_results = {
            'tests_passed': True,  # You would get this from running your tests
            'total_tests': len(mapped_updates),
            'failed_tests': 0,
            'test_output': 'No automated tests were executed'
        }
        
        markdown_report = report_generator.generate_markdown_report(
            update_summary,
            task_summary,
            test_results,
            backup_timestamp
        )
        
        json_report = report_generator.generate_json_report(
            update_summary,
            task_summary,
            test_results,
            backup_timestamp
        )
        
        if update_result.get('errors'):
            error_report = report_generator.generate_error_report(update_result['errors'])
            logger.info(f"Error report generated: {error_report}")
        
        logger.info("Update process completed!")
        logger.info(f"Markdown report: {markdown_report}")
        logger.info(f"JSON report: {json_report}")
        
    except Exception as e:
        logger.error(f"An error occurred during the update process: {str(e)}")
        raise

if __name__ == "__main__":
    # Example usage with local paths
    main(
        project_root='/Users/m/git/lubot',
        backup_root='/Users/m/backups',
        report_dir='/Users/m/reports',
        db_path='/Users/m/tasks.db',
        llm_output_file='/Users/m/llm_output.txt'
    )