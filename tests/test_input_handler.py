# tests/test_input_handler.py
import unittest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
from llmcodeupdater.input_handler import InputHandler

class TestInputHandler(unittest.TestCase):
    def setUp(self):
        self.handler = InputHandler()

    @patch('pathlib.Path.iterdir')
    def test_get_git_projects(self, mock_iterdir):
        # Set up mock to return directories that simulate git repositories
        mock_iterdir.return_value = [
            MagicMock(is_dir=MagicMock(return_value=True),
                      __truediv__=MagicMock(return_value=MagicMock(exists=MagicMock(return_value=True)))),
            MagicMock(is_dir=MagicMock(return_value=False))  # Not a directory, should be skipped
        ]
        
        expected_projects = ['/mocked/project_path']  # Assuming the first mock returns 'project_path' directory
        projects = self.handler.get_git_projects()
        self.assertEqual(len(projects), 1)  # Only the valid project should be listed

    @patch('llmcodeupdater.input_handler.inquirer.prompt')
    def test_select_project_interactive_empty(self, mock_prompt):
        # Simulate no project selected (user cancels or no projects available)
        mock_prompt.return_value = None
        project = self.handler.select_project_interactive()
        self.assertIsNone(project)

    @patch('llmcodeupdater.input_handler.inquirer.prompt')
    def test_select_project_interactive(self, mock_prompt):
        # Simulate user selecting a project
        mock_prompt.return_value = {'project': '/path/to/project'}
        project = self.handler.select_project_interactive()
        self.assertEqual(project, '/path/to/project')

    @patch('llmcodeupdater.input_handler.pyperclip.paste')
    def test_get_clipboard_content_success(self, mock_paste):
        # Simulate successful clipboard content retrieval
        mock_paste.return_value = "Sample clipboard content"
        content = self.handler.get_clipboard_content()
        self.assertEqual(content, "Sample clipboard content")

    @patch('llmcodeupdater.input_handler.pyperclip.paste', side_effect=Exception("Clipboard error"))
    def test_get_clipboard_content_failure(self, mock_paste):
        # Simulate an error when accessing the clipboard
        content = self.handler.get_clipboard_content()
        self.assertIsNone(content)

    @patch('pathlib.Path.exists', return_value=True)
    def test_validate_path_valid(self, mock_exists):
        # Test validating a valid path
        path = self.handler.validate_path("/valid/path")
        self.assertIsInstance(path, Path)

    @patch('pathlib.Path.exists', return_value=False)
    def test_validate_path_invalid(self, mock_exists):
        # Test validating an invalid path
        path = self.handler.validate_path("/invalid/path")
        self.assertIsNone(path)

    @patch('builtins.open', new_callable=mock_open, read_data='Sample LLM content')
    @patch('pathlib.Path.is_file', return_value=True)
    @patch('pathlib.Path.exists', return_value=True)
    @patch('llmcodeupdater.input_handler.Path.read_text', return_value='Sample LLM content')
    @patch('llmcodeupdater.input_handler.InputHandler.select_project_interactive', return_value=None)
    def test_process_input_content_file(self, mock_select_project, mock_read_text, mock_exists, mock_is_file, mock_open_func):
        # Simulate providing a valid content file
        args = {'content_file': '/path/to/content.txt'}
        result = self.handler.process_input(args)
        self.assertEqual(result['llm_content'], 'Sample LLM content')
        self.assertIsNone(result['project_path'])

    @patch('llmcodeupdater.input_handler.pyperclip.paste', return_value='Clipboard LLM content')
    @patch('llmcodeupdater.input_handler.InputHandler.select_project_interactive', return_value=None)
    @patch('pathlib.Path.is_file', return_value=True)
    @patch('pathlib.Path.exists', return_value=True)
    def test_process_input_clipboard(self, mock_exists, mock_is_file, mock_select_project, mock_paste):
        # Simulate providing LLM content from clipboard
        args = {'use_clipboard': True}
        result = self.handler.process_input(args)
        self.assertEqual(result['llm_content'], 'Clipboard LLM content')
        self.assertIsNone(result['project_path'])

    @patch('llmcodeupdater.input_handler.InputHandler.select_project_interactive', return_value='/path/to/project')
    def test_process_input_interactive_project_selection(self, mock_select_project):
        # Simulate interactive project selection
        args = {'interactive': True}
        result = self.handler.process_input(args)
        self.assertEqual(result['project_path'], '/path/to/project')
        self.assertIsNone(result['llm_content'])

if __name__ == '__main__':
    unittest.main()
