# tests/test_main.py
import unittest
from unittest.mock import patch, Mock, mock_open
import main
from llmcodeupdater.code_parser import CodeParser, parse_code_blocks_with_logging
from llmcodeupdater.file_encoding_handler import FileEncodingHandler

class TestMainFunctionality(unittest.TestCase):
    @patch('main.os.makedirs')
    @patch('main.FileEncodingHandler')
    @patch('main.update_files')
    @patch('main.backup_files')
    @patch('main.TaskTracker')
    @patch('main.ReportGenerator')
    @patch('main.setup_cli_parser')
    @patch('main.parse_code_blocks_with_logging')
    def test_main_complete_success(self, mock_parse_blocks, mock_parser, mock_report_generator, 
                             mock_task_tracker, mock_backup, mock_update, mock_file_handler, 
                             mock_makedirs):
        # Setup mock parser
        mock_args = Mock()
        mock_args.git_path = "dummy/path"
        mock_parser.return_value.parse_args.return_value = mock_args
        
        # Mock code blocks with valid content
        mock_parse_blocks.return_value = [('test.py', 'def test(): pass')]
        
        # Setup mock input handler with proper return values
        mock_input_handler = Mock()
        mock_input_handler.process_input.return_value = {
            'project_path': '/valid/project/path',
            'llm_content': 'some content'
        }
        
        # Patch the InputHandler class
        with patch('main.InputHandler', return_value=mock_input_handler):
            # Setting up mock returns
            mock_file_handler.return_value.preprocess_files.return_value = {
                'successful': [], 'failed': [], 'skipped': []
            }
            mock_update.return_value = {'files_updated': 5, 'files_skipped': 0, 'errors': {}}
            mock_backup.return_value = 5
            
            mock_task_tracker_instance = mock_task_tracker.return_value
            mock_task_tracker_instance.get_task_summary.return_value = {
                'total': 5, 'updated': 5, 'skipped': 0, 'error': 0, 'pending': 0
            }
            
            # Call main function
            main.main()
            
            # Verify process execution
            mock_parser.assert_called_once()
            mock_file_handler.return_value.preprocess_files.assert_called_once()
            mock_update.assert_called_once()
            mock_backup.assert_called_once()

    @patch('main.logging.getLogger')
    @patch('main.setup_cli_parser')
    @patch('main.update_files', side_effect=Exception("Update failed"))
    @patch('main.os.makedirs')
    @patch('main.parse_code_blocks_with_logging')
    @patch('main.FileEncodingHandler')
    def test_main_processing_error(self, mock_file_handler, mock_parse_blocks, 
                             mock_makedirs, mock_update, mock_parser, mock_get_logger):
        # Setup mock parser
        mock_args = Mock()
        mock_args.git_path = "dummy/path"
        mock_parser.return_value.parse_args.return_value = mock_args
        
        # Mock FileEncodingHandler
        mock_file_handler.return_value.preprocess_files.return_value = {
            'successful': [], 'failed': [], 'skipped': []
        }
        
        # Mock code blocks to ensure update_files is called
        mock_parse_blocks.return_value = [('test.py', 'def test(): pass')]
        
        # Setup mock input handler with proper return values
        mock_input_handler = Mock()
        mock_input_handler.process_input.return_value = {
            'project_path': '/valid/project/path',
            'llm_content': 'some content'
        }
        
        # Set up the mock logger
        mock_logger = mock_get_logger.return_value
        
        # Mock TaskTracker
        with patch('main.TaskTracker') as mock_task_tracker:
            mock_tracker = Mock()
            mock_task_tracker.return_value = mock_tracker
            
            # Patch the InputHandler class
            with patch('main.InputHandler', return_value=mock_input_handler):
                # Call main function, which should trigger an error in update_files
                with self.assertRaises(Exception) as context:
                    main.main()
                
                # Verify the error message
                self.assertEqual(str(context.exception), "Update failed")
                mock_logger.error.assert_called_with(
                    "An error occurred during the update process: Update failed"
                )

    @patch('main.logging.getLogger')
    @patch('main.setup_cli_parser')
    @patch('main.os.makedirs')
    @patch('main.parse_code_blocks_with_logging')
    @patch('main.FileEncodingHandler')
    @patch('main.TaskTracker')  # Add TaskTracker mock
    def test_main_no_valid_code_blocks(self, mock_task_tracker, mock_file_handler, 
                                 mock_parse_blocks, mock_makedirs, mock_parser, 
                                 mock_get_logger):
        # Setup mock parser
        mock_args = Mock()
        mock_args.git_path = "dummy/path"
        mock_parser.return_value.parse_args.return_value = mock_args
        
        # Mock FileEncodingHandler
        mock_file_handler.return_value.preprocess_files.return_value = {
            'successful': [], 'failed': [], 'skipped': []
        }
        
        # Mock code blocks to return empty list
        mock_parse_blocks.return_value = []
        
        # Setup mock input handler
        mock_input_handler = Mock()
        mock_input_handler.process_input.return_value = {
            'project_path': '/valid/project/path',
            'llm_content': 'some content'
        }
        
        # Set up the mock logger
        mock_logger = mock_get_logger.return_value
        
        # Mock TaskTracker instance
        mock_tracker = Mock()
        mock_task_tracker.return_value = mock_tracker
        
        # Patch the InputHandler class
        with patch('main.InputHandler', return_value=mock_input_handler):
            # Call main function, expect ValueError
            with self.assertRaises(ValueError) as context:
                main.main()
            
            # Verify the error messages
            self.assertEqual(str(context.exception), "No valid code blocks to process")
            mock_logger.error.assert_any_call("No valid code blocks found in LLM output")
            mock_logger.error.assert_any_call(
                "An error occurred during the update process: No valid code blocks to process"
            )

    @patch('main.os.makedirs')
    @patch('main.FileEncodingHandler')
    @patch('main.update_files')
    @patch('main.backup_files')
    @patch('main.TaskTracker')
    @patch('main.ReportGenerator')
    @patch('main.setup_cli_parser')
    @patch('main.parse_code_blocks_with_logging')
    def test_main_with_project_handling(self, mock_parse_blocks, mock_parser, 
                                      mock_report_gen, mock_task_tracker, 
                                      mock_backup, mock_update, mock_file_handler, 
                                      mock_makedirs):
        # Setup mocks
        mock_args = Mock()
        mock_args.git_path = "dummy/path"
        mock_parser.return_value.parse_args.return_value = mock_args
        
        project_path = "/test/project"
        mock_input_handler = Mock()
        mock_input_handler.process_input.return_value = {
            'project_path': project_path,
            'llm_content': 'some content'
        }
        
        # Setup TaskTracker mock
        mock_task_tracker_instance = Mock()
        mock_task_tracker.return_value = mock_task_tracker_instance
        mock_task_tracker_instance.get_task_summary.return_value = {
            'total': 5, 'updated': 5, 'skipped': 0, 'error': 0, 'pending': 0
        }
        
        # Setup mock for parse_code_blocks_with_logging
        mock_parse_blocks.return_value = [('test.py', 'def test(): pass')]
        
        # Setup mock for update_files
        mock_update.return_value = {'files_updated': 5, 'files_skipped': 0, 'errors': {}}
        
        with patch('main.InputHandler', return_value=mock_input_handler):
            main.main()
            
            # Verify that add_tasks was called instead of clear_project_tasks
            mock_task_tracker_instance.add_tasks.assert_called_once()
            mock_task_tracker_instance.get_task_summary.assert_called_once()

if __name__ == '__main__':
    unittest.main()
