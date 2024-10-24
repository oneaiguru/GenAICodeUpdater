
from typing import List
import os
import sqlite3
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMCodeFileHandler:
    """
    A class to handle LLM-generated Python files, allowing for reading and parsing of code blocks,
    handling multi-file code blocks, and managing logging of file operations.
    """

    def __init__(self, directory: str, db_path: str):
        """
        Initialize the handler with the directory containing the .py files and the path to the database.

        Args:
            directory (str): The path to the directory containing the Python files.
            db_path (str): Path to the SQLite database for logging operations.
        """
        self.directory = directory
        self.db_path = db_path

    def _log_file_operation(self, file_name: str, status: str) -> None:
        """
        Log file operations (e.g., processed, ignored, error) in the database.

        Args:
            file_name (str): Name of the file being processed.
            status (str): Status of the operation (e.g., 'processed', 'ignored', 'error').
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO file_logs (file_name, status) VALUES (?, ?)", (file_name, status))
            conn.commit()

    def process_files(self) -> List[str]:
        """
        Process all Python files in the directory, handling multi-file code blocks and logging operations.

        Returns:
            List[str]: The combined content of valid Python files processed.
        """
        processed_content = []
        
        for file_name in sorted(os.listdir(self.directory)):
            # Ignore hidden files (e.g., starting with '.')
            if file_name.startswith('.'):
                self._log_file_operation(file_name, 'ignored')
                continue

            file_path = os.path.join(self.directory, file_name)
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    # Check for simple validity (here we just check for print statements for simplicity)
                    if 'print' not in content:
                        raise ValueError(f"Malformed file: {file_name}")
                    
                    processed_content.append(content)
                    self._log_file_operation(file_name, 'processed')
            except Exception as e:
                logger.error(f"Error processing file {file_name}: {e}")
                self._log_file_operation(file_name, 'error')

        return processed_content
    