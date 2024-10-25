#!/usr/bin/env python3

import os
import sys
import argparse

class FolderStructureGenerator:
    DEFAULT_IGNORE_PATTERNS = [
        "__pycache__",
        ".git",
        "venv",
        "tests",
        "alembic",
        "*.pyc",
        "*.log",
    ]

    def __init__(self, ignored_folders=None, ignore_file=".treeignore"):
        if ignored_folders is None:
            ignored_folders = []
        self.ignored_folders = set(self.DEFAULT_IGNORE_PATTERNS).union(set(ignored_folders))
        self.ignore_file = ignore_file

    def load_ignore_patterns(self, root_dir):
        patterns = list(self.ignored_folders)
        ignore_path = os.path.join(root_dir, self.ignore_file)
        if os.path.exists(ignore_path):
            with open(ignore_path, 'r') as f:
                file_patterns = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                patterns.extend(file_patterns)
        return patterns

    def generate_folder_structure_txt(self, current_directory, output_path=None):
        if not os.path.exists(current_directory):
            raise FileNotFoundError(f"The directory '{current_directory}' does not exist.")

        ignore_patterns = self.load_ignore_patterns(current_directory)

        tree_lines = [f"{os.path.basename(current_directory)}/"]

        def matches_ignore_pattern(entry):
            for pattern in ignore_patterns:
                if pattern.endswith('/'):
                    # Directory pattern
                    dir_pattern = pattern.rstrip('/')
                    if dir_pattern == entry:
                        return True
                else:
                    # File pattern with possible wildcards
                    if fnmatch.fnmatch(entry, pattern):
                        return True
            return False

        def recurse(dir_path, prefix):
            entries = sorted(os.listdir(dir_path))
            # Exclude the ignore file itself to prevent recursion
            entries = [e for e in entries if e != self.ignore_file]
            entries = [e for e in entries if not matches_ignore_pattern(e)]
            for i, entry in enumerate(entries):
                path = os.path.join(dir_path, entry)
                connector = "├── " if i < len(entries) - 1 else "└── "
                if os.path.isdir(path):
                    tree_lines.append(f"{prefix}{connector}{entry}/")
                    new_prefix = prefix + ("│   " if i < len(entries) - 1 else "    ")
                    recurse(path, new_prefix)
                else:
                    tree_lines.append(f"{prefix}{connector}{entry}")

        import fnmatch  # Moved inside to avoid potential issues
        recurse(current_directory, "")
        tree_str = "\n".join(tree_lines) + "\n"

        if output_path:
            with open(output_path, 'w') as f:
                f.write(tree_str)
            print(f"Folder structure written to {output_path}")
            return tree_str

        return tree_str

def main():
    parser = argparse.ArgumentParser(description="Generate a tree structure of a directory.")
    parser.add_argument("directory", help="The root directory to generate the tree from.")
    parser.add_argument("--output", "-o", help="Path to the output file (e.g., tree.txt). If not specified, prints to stdout.")
    args = parser.parse_args()

    root_dir = os.path.abspath(args.directory)
    generator = FolderStructureGenerator()
    generator.generate_folder_structure_txt(root_dir, args.output)

if __name__ == "__main__":
    main()
