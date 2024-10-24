import os
import chardet
from typing import Dict, Tuple, Optional
import logging
from pathlib import Path

class FileEncodingHandler:
    """Handles file encoding detection and conversion for code updates."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        # Common encodings to try if detection fails
        self.fallback_encodings = [
            'utf-8', 'latin1', 'cp1252', 'iso-8859-1', 
            'ascii', 'utf-16', 'utf-32'
        ]
    
    def detect_file_encoding(self, file_path: str, sample_size: int = 10000) -> Tuple[str, float]:
        """
        Detect the encoding of a file using chardet.
        
        Args:
            file_path: Path to the file
            sample_size: Number of bytes to sample for detection
            
        Returns:
            Tuple[str, float]: Detected encoding and confidence score
        """
        with open(file_path, 'rb') as f:
            raw_data = f.read(sample_size)
            result = chardet.detect(raw_data)
            return result['encoding'], result['confidence']
    
    def validate_utf8(self, file_path: str) -> bool:
        """
        Check if a file is valid UTF-8.
        
        Args:
            file_path: Path to the file
            
        Returns:
            bool: True if file is valid UTF-8
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                f.read()
            return True
        except UnicodeDecodeError:
            return False
    
    def convert_to_utf8(self, file_path: str, 
                       backup_dir: Optional[str] = None) -> Dict[str, any]:
        """
        Convert a file to UTF-8 encoding.
        
        Args:
            file_path: Path to the file
            backup_dir: Directory to store backup files
            
        Returns:
            Dict containing operation results
        """
        result = {
            'success': False,
            'original_encoding': None,
            'confidence': 0,
            'backup_path': None,
            'error': None
        }
        
        try:
            # Create backup if directory specified
            if backup_dir:
                os.makedirs(backup_dir, exist_ok=True)
                backup_path = os.path.join(
                    backup_dir, 
                    f"{Path(file_path).name}.bak"
                )
                with open(file_path, 'rb') as src, open(backup_path, 'wb') as dst:
                    dst.write(src.read())
                result['backup_path'] = backup_path
            
            # Detect original encoding
            encoding, confidence = self.detect_file_encoding(file_path)
            result['original_encoding'] = encoding
            result['confidence'] = confidence
            
            # If detection failed or confidence is low, try fallback encodings
            if not encoding or confidence < 0.8:
                content = None
                for enc in self.fallback_encodings:
                    try:
                        with open(file_path, 'r', encoding=enc) as f:
                            content = f.read()
                            encoding = enc
                            break
                    except UnicodeDecodeError:
                        continue
                
                if content is None:
                    raise UnicodeError("Unable to decode file with any known encoding")
            else:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
            
            # Write content back in UTF-8
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"Error converting {file_path}: {str(e)}")
            
            # Restore from backup if conversion failed
            if backup_dir and result['backup_path']:
                try:
                    with open(result['backup_path'], 'rb') as src:
                        with open(file_path, 'wb') as dst:
                            dst.write(src.read())
                except Exception as restore_error:
                    self.logger.error(
                        f"Error restoring backup for {file_path}: {str(restore_error)}"
                    )
        
        return result
    
    def process_directory(self, 
                         directory: str,
                         backup_dir: Optional[str] = None,
                         file_extensions: tuple = ('.py',)) -> Dict[str, list]:
        """
        Process all files in a directory, converting them to UTF-8.
        
        Args:
            directory: Directory to process
            backup_dir: Directory to store backups
            file_extensions: Tuple of file extensions to process
            
        Returns:
            Dict containing lists of successful and failed files
        """
        results = {
            'successful': [],
            'failed': [],
            'skipped': []
        }
        
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(file_extensions):
                    file_path = os.path.join(root, file)
                    
                    # Skip if already valid UTF-8
                    if self.validate_utf8(file_path):
                        results['skipped'].append(file_path)
                        continue
                    
                    result = self.convert_to_utf8(file_path, backup_dir)
                    if result['success']:
                        results['successful'].append({
                            'path': file_path,
                            'original_encoding': result['original_encoding'],
                            'confidence': result['confidence']
                        })
                    else:
                        results['failed'].append({
                            'path': file_path,
                            'error': result['error']
                        })
        
        return results
