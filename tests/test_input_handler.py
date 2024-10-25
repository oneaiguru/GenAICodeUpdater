import unittest
from unittest.mock import patch, MagicMock, mock_open, Mock
from pathlib import Path
from llmcodeupdater.input_handler import InputHandler
import os
import json
import time

class TestInputHandler(unittest.TestCase):
    def setUp(self):
        # Set up test directory
        self.temp_dir = os.path.join(os.path.dirname(__file__), 'test_temp')
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Set up test VS Code projects data
        self.vscode_projects = [
            {
                "name": "Project1",
                "path": "/path/to/project1",
                "enabled": True
            },
            {
                "name": "Project2",
                "path": "/path/to/project2",
                "enabled": False
            }
        ]
        
        self.handler = InputHandler()

    def tearDown(self):
        # Clean up test directory
        if os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)

    @patch('pathlib.Path.iterdir')
    def test_get_git_projects(self, mock_iterdir):
        # Mock directory with git projects
        mock_projects = [
            MagicMock(
                is_dir=MagicMock(return_value=True),
                __str__=MagicMock(return_value='/path/to/project1'),
                __truediv__=MagicMock(return_value=MagicMock(exists=MagicMock(return_value=True)))
            ),
            MagicMock(
                is_dir=MagicMock(return_value=True),
                __str__=MagicMock(return_value='/path/to/project2'),
                __truediv__=MagicMock(return_value=MagicMock(exists=MagicMock(return_value=True)))
            )
        ]
        mock_iterdir.return_value = mock_projects
        
        projects = self.handler.get_git_projects()
        self.assertEqual(len(projects), 2)
        self.assertIn('/path/to/project1', projects)
        self.assertIn('/path/to/project2', projects)

    @patch('llmcodeupdater.input_handler.inquirer.prompt')
    @patch('llmcodeupdater.input_handler.InputHandler.get_git_projects')
    def test_select_project_interactive(self, mock_get_projects, mock_prompt):
        # Setup mock projects
        mock_projects = ['/path/to/project1', '/path/to/project2']
        mock_get_projects.return_value = mock_projects
        
        # Mock user selection
        mock_prompt.return_value = {'project': '/path/to/project1'}
        
        project = self.handler.select_project_interactive()
        self.assertEqual(project, '/path/to/project1')

    @patch('llmcodeupdater.input_handler.inquirer.prompt')
    def test_select_project_interactive_empty(self, mock_prompt):
        # Simulate no project selected
        mock_prompt.return_value = None
        project = self.handler.select_project_interactive()
        self.assertIsNone(project)

    @patch('llmcodeupdater.input_handler.pyperclip.paste')
    def test_get_clipboard_content_success(self, mock_paste):
        mock_paste.return_value = "Sample clipboard content"
        content = self.handler.get_clipboard_content()
        self.assertEqual(content, "Sample clipboard content")

    @patch('llmcodeupdater.input_handler.pyperclip.paste', side_effect=Exception("Clipboard error"))
    def test_get_clipboard_content_failure(self, mock_paste):
        content = self.handler.get_clipboard_content()
        self.assertIsNone(content)

    def test_validate_path_valid(self):
        test_path = os.path.join(self.temp_dir, 'test_file')
        with open(test_path, 'w') as f:
            f.write('test')
        path = self.handler.validate_path(test_path)
        self.assertIsInstance(path, Path)

    def test_validate_path_invalid(self):
        invalid_path = os.path.join(self.temp_dir, 'nonexistent')
        path = self.handler.validate_path(invalid_path)
        self.assertIsNone(path)

    def test_process_input_with_performance_logging(self):
        with patch('time.time') as mock_time:
            mock_time.side_effect = [0, 1]  # Start and end times
            
            args = {
                'project_path': self.temp_dir,
                'use_clipboard': False,
                'content_file': None
            }
            
            result = self.handler.process_input(args)
            self.assertIsNotNone(result['project_path'])
            mock_time.assert_called()

    def test_process_input_content_file(self):
        test_file = os.path.join(self.temp_dir, 'content.txt')
        with open(test_file, 'w') as f:
            f.write('Sample content')
            
        args = {'content_file': test_file}
        result = self.handler.process_input(args)
        self.assertEqual(result['llm_content'], 'Sample content')

    @patch('llmcodeupdater.input_handler.pyperclip.paste')
    def test_process_input_clipboard(self, mock_paste):
        mock_paste.return_value = 'Clipboard content'
        args = {'use_clipboard': True}
        result = self.handler.process_input(args)
        self.assertEqual(result['llm_content'], 'Clipboard content')

    def test_process_input_interactive_project_selection(self):
        with patch.object(self.handler, 'select_project_interactive', return_value='/path/to/project'):
            args = {'interactive': True}
            result = self.handler.process_input(args)
            self.assertEqual(result['project_path'], '/path/to/project')

    def test_load_vscode_projects(self):
        config_path = os.path.join(self.temp_dir, '.vscode', 'projects.json')
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(self.vscode_projects, f)
            
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=json.dumps(self.vscode_projects))):
            projects = self.handler.get_projects()
            self.assertEqual(len(projects), 1)  # Only enabled projects
            self.assertEqual(projects[0]['name'], 'Project1')

if __name__ == '__main__':
    unittest.main()