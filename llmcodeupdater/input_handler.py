# llmcodeupdater/input_handler.py

import os
import pyperclip
import inquirer
import json
from typing import Optional, Dict, Union
from pathlib import Path
import logging
import time

logger = logging.getLogger(__name__)

class InputHandler:
    """Handles various input methods for the LLM code updater."""
    
    def __init__(self, default_git_path: str = "~/git"):
        """Initialize with default git projects path."""
        self.git_path = os.path.expanduser(default_git_path)
        self._performance_metrics = {}  # Added performance metrics attribute
    
    def get_git_projects(self) -> list[str]:
        """Get list of git projects in the default directory."""
        projects = []
        try:
            git_path = Path(self.git_path).expanduser()
            for item in git_path.iterdir():
                if item.is_dir() and (item / '.git').exists():
                    projects.append(str(item))
        except Exception as e:
            logger.error(f"Error scanning git directory: {e}")
        return sorted(projects)
    
    def select_project_interactive(self) -> Optional[str]:
        """Show interactive project selection dialog."""
        projects = self.get_git_projects()  # Use git projects instead of VS Code projects
        if not projects:
            logger.warning("No projects found.")
            return None

        # Create list of project paths for selection
        questions = [
            inquirer.List(
                'project',
                message="Select a project to update",
                choices=projects,
                carousel=True
            )
        ]
        
        try:
            answers = inquirer.prompt(questions)
            return answers['project'] if answers else None
        except Exception as e:
            logger.error(f"Error in project selection: {e}")
            return None
    
    def get_clipboard_content(self) -> Optional[str]:
        """Get content from clipboard."""
        try:
            return pyperclip.paste()
        except Exception as e:
            logger.error(f"Error getting clipboard content: {e}")
            return None
    
    def validate_path(self, path: str) -> Optional[Path]:
        """Validate if path exists and is accessible."""
        try:
            path_obj = Path(path).expanduser().resolve()
            if not path_obj.exists():
                logger.error(f"Path does not exist: {path}")
                return None
            return path_obj
        except Exception as e:
            logger.error(f"Error validating path: {e}")
            return None
    
    def get_projects(self) -> list[dict]:
        """Get list of projects from the VS Code configuration."""
        try:
            config_path = os.path.expanduser('~/.config/Code/User/globalStorage/alefragnani.project-manager/projects.json')
            
            # Ensure path exists
            if not os.path.exists(config_path):
                logger.warning(f"Configuration path not found: {config_path}")
                return []
            
            # Load the JSON file and parse projects
            with open(config_path, 'r') as f:
                projects_data = json.load(f)
            
            # Extract enabled projects with proper path handling
            enabled_projects = [
                {"name": p.get("name", "Unnamed Project"), "path": p.get("path") or p.get("rootPath")}
                for p in projects_data 
                if p.get("enabled", True) and (p.get("path") or p.get("rootPath"))
            ]
            
            return enabled_projects
        
        except Exception as e:
            logger.error(f"Error loading VS Code projects: {e}")
            return []
    
    def process_input(self, args: Dict) -> Dict[str, Union[str, Path, None]]:
        """Process input from various sources based on provided arguments."""
        start_time = time.time()  # Start timing the process
        
        result = {
            'project_path': None,
            'llm_content': None
        }
        
        # Handle project path
        if args.get('project_path'):
            result['project_path'] = self.validate_path(args['project_path'])
        elif args.get('interactive', True):
            result['project_path'] = self.select_project_interactive()
        
        # Handle LLM content
        if args.get('content_file'):
            content_path = self.validate_path(args['content_file'])
            if content_path and content_path.is_file():
                try:
                    result['llm_content'] = content_path.read_text(encoding='utf-8')
                except Exception as e:
                    logger.error(f"Error reading content file: {e}")
        elif args.get('use_clipboard', False):
            result['llm_content'] = self.get_clipboard_content()
        
        self._performance_metrics['process_input'] = time.time() - start_time  # Record performance metric
        return result

def setup_cli_parser():
    """Set up command line argument parser."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='LLM Code Updater - Update code based on LLM output'
    )
    
    # Project selection options
    project_group = parser.add_mutually_exclusive_group()
    project_group.add_argument(
        '--project-path',
        help='Direct path to project directory'
    )
    project_group.add_argument(
        '--no-interactive',
        action='store_false',
        dest='interactive',
        help='Disable interactive project selection'
    )
    
    # Content source options
    content_group = parser.add_mutually_exclusive_group()
    content_group.add_argument(
        '--content-file',
        help='Path to file containing LLM output'
    )
    content_group.add_argument(
        '--clipboard',
        action='store_true',
        dest='use_clipboard',
        help='Use clipboard content as LLM output'
    )
    
    # Additional options
    parser.add_argument(
        '--git-path',
        default='~/git',
        help='Path to git projects directory (default: ~/git)'
    )
    
    return parser
