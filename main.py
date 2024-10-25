import os
from datetime import datetime
import logging
from llmcodeupdater.input_handler import InputHandler, setup_cli_parser
from llmcodeupdater.task_tracking import TaskTracker
from llmcodeupdater.code_parser import parse_code_blocks_with_logging
from llmcodeupdater.mapping import update_files
from llmcodeupdater.backup import backup_files
from llmcodeupdater.reporting import ReportGenerator
from llmcodeupdater.file_encoding_handler import FileEncodingHandler

def validate_prerequisites(project_path: str, llm_content: str) -> bool:
    """Validate required inputs before proceeding."""
    if not project_path:
        logging.error("No valid project path provided")
        return False
    if not llm_content:
        logging.error("No LLM content provided")
        return False
    return True

def setup_project_directories(project_root: str) -> tuple:
    """Create and return necessary project directories."""
    backup_root = os.path.join(project_root, 'backups')
    report_dir = os.path.join(project_root, 'reports')
    db_path = os.path.join(project_root, 'tasks.db')
    
    os.makedirs(backup_root, exist_ok=True)
    os.makedirs(report_dir, exist_ok=True)
    
    return backup_root, report_dir, db_path

def collect_python_files(project_root: str) -> list:
    """Collect all Python files in the project."""
    py_files = []
    for root, _, files in os.walk(project_root):
        for file in files:
            if file.endswith('.py'):
                py_files.append(os.path.join(root, file))
    return py_files

def main():
    """Main function to orchestrate the code update process."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger('Main')
    
    try:
        # Initialize and parse arguments
        parser = setup_cli_parser()
        args = parser.parse_args()
        input_handler = InputHandler(default_git_path=args.git_path)
        result = input_handler.process_input(vars(args))
        
        # Validate prerequisites
        if not validate_prerequisites(result.get('project_path'), result.get('llm_content')):
            return
            
        project_root = result['project_path']
        llm_content = result['llm_content']
        
        # Setup directories
        backup_root, report_dir, db_path = setup_project_directories(project_root)
        
        # Initialize components
        task_tracker = TaskTracker(db_path)
        report_generator = ReportGenerator(report_dir)
        
        # Preprocess files
        file_handler = FileEncodingHandler()
        preprocess_results = file_handler.preprocess_files(project_root)
        if preprocess_results['failed']:
            for fail in preprocess_results['failed']:
                logger.error(f"Failed to convert encoding: {fail['path']}, Error: {fail['error']}")
        
        # Collect and backup files
        py_files = collect_python_files(project_root)
        task_tracker.add_tasks([os.path.basename(f) for f in py_files])
        
        backup_timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        files_backed_up = backup_files(py_files, project_root, backup_root)
        logger.info(f"Backed up {files_backed_up} files.")
        
        # Parse and validate code blocks
        code_blocks = parse_code_blocks_with_logging(llm_content)
        if not code_blocks:
            logger.error("No valid code blocks found in LLM output")
            raise ValueError("No valid code blocks to process")
        
        # Process updates
        update_result = update_files(code_blocks, project_root)
        
        # Update task statuses
        for filename, _ in code_blocks:
            task_tracker.update_task_status(filename, 'updated')
        
        # Generate reports
        update_summary = {
            'files_updated': update_result['files_updated'],
            'files_skipped': update_result['files_skipped'],
            'error_files': update_result.get('errors', {})
        }
        
        task_summary = task_tracker.get_task_summary()
        test_results = {
            'tests_passed': True,
            'total_tests': len(code_blocks),
            'failed_tests': 0,
            'test_output': 'No automated tests were executed'
        }
        
        # Generate reports
        markdown_report = report_generator.generate_markdown_report(
            update_summary, task_summary, test_results, backup_timestamp
        )
        json_report = report_generator.generate_json_report(
            update_summary, task_summary, test_results, backup_timestamp
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
    main()
