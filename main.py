import os
from datetime import datetime
from task_tracking import TaskTracker
from llmcodeupdater.parsing_module.CodeBlockParser import parse_code_blocks_with_logging
from llmcodeupdater.mapping_module.MappingModule import update_files
from llmcodeupdater.backup_module.backup_module import backup_files
from llmcodeupdater.reporting_module.ReportGenerator import ReportGenerator

def main(project_root: str, backup_root: str, report_dir: str, db_path: str):
    """Main function to orchestrate the code update process."""
    
    # Initialize components
    task_tracker = TaskTracker(db_path)
    report_generator = ReportGenerator(report_dir)
    
    try:
        # 1. Collect all Python files
        py_files = []
        for root, _, files in os.walk(project_root):
            for file in files:
                if file.endswith('.py'):
                    py_files.append(os.path.join(root, file))
        
        # 2. Add tasks to tracker
        task_tracker.add_tasks(py_files)
        
        # 3. Create backup
        backup_timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        backup_files(py_files, project_root, backup_root)
        
        # 4. Process updates
        error_files = {}
        update_count = 0
        skip_count = 0
        
        for file_path in py_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                code_blocks = parse_code_blocks_with_logging(content)
                if code_blocks:
                    update_result = update_files([(file_path, block[1]) for block in code_blocks])
                    update_count += update_result['files_updated']
                    skip_count += update_result['files_skipped']
                    
                    if update_result['files_updated'] > 0:
                        task_tracker.update_task_status(file_path, 'updated')
                    else:
                        task_tracker.update_task_status(file_path, 'skipped')
                        
            except Exception as e:
                error_files[file_path] = str(e)
                task_tracker.update_task_status(file_path, 'error', str(e))
        
        # 5. Generate reports
        update_summary = {
            'files_updated': update_count,
            'files_skipped': skip_count,
            'error_files': error_files
        }
        
        task_summary = task_tracker.get_task_summary()
        
        test_results = {
            'tests_passed': True,  # You would get this from running your tests
            'total_tests': 0,
            'failed_tests': 0,
            'test_output': ''
        }
        
        # Generate reports
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
        
        if error_files:
            error_report = report_generator.generate_error_report(error_files)
            print(f"Error report generated: {error_report}")
        
        print(f"Update complete!")
        print(f"Markdown report: {markdown_report}")
        print(f"JSON report: {json_report}")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    # Example usage
    main(
        project_root="/path/to/your/project",
        backup_root="/path/to/backups",
        report_dir="/path/to/reports",
        db_path="/path/to/tasks.db"
    )