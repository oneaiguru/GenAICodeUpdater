Here's a `README.md` for the **MyCodeTree2LLM** project, covering project setup, configuration, usage, and example configurations.

* * *

# MyCodeTree2LLM

MyCodeTree2LLM is a workflow automation tool designed for managing multiple projects with streamlined file selection and organization. This tool helps you automate tasks across various projects, including generating project structure files, selecting files interactively, and managing project switching.

## Table of Contents

* [Features](#features)
* [Prerequisites](#prerequisites)
* [Setup](#setup)
* [Configuration](#configuration)
* [Usage](#usage)
* [Project Management Commands](#project-management-commands)
* [Testing](#testing)

## Features

* **Automated Workflow Execution**: Automate routine tasks across multiple projects.
* **Project File Selection**: Interactive file selection with configurable ignore patterns.
* **Project Switching**: Easily switch between different project contexts.
* **Directory Tree Generation**: Generates a `tree.txt` file representing the directory structure.

## Prerequisites

* Python 3.7+
* Additional packages as specified in `requirements.txt` (e.g., `rich`, `readchar`, `pyperclip`)

## Setup

1. Clone this repository.
2. Install dependencies:
    
    ```bash
    pip install -r requirements.txt
    ```
    
3. Ensure that project directories are correctly set up, and files like `config.json` and `projects.json` are configured.

## Configuration

The primary configuration for MyCodeTree2LLM is the `config.json` file, which defines the default paths and project-specific settings. This file is expected to be located in the root directory of MyCodeTree2LLM and can be customized based on your setup.

### Example Configuration (`config.json`)

The `config.json` file may look like this:

```json
{
    "current_project": "MyCodeTree2LLM",
    "projects_json_path": "/Users/m/Library/Application Support/Cursor/User/globalStorage/alefragnani.project-manager/projects.json",
    "tool_files": [
        "automate_workflow.sh",
        "select_files.py",
        "folder_structure_generator.py"
    ]
}
```

### `projects.json` Structure

The `projects.json` file should list each project with at least its name, root path, and enabled status:

```json
[
    {
        "name": "fast whisper",
        "rootPath": "/Users/m/git/personal/fastwhisper",
        "enabled": true
    },
    {
        "name": "lubot",
        "rootPath": "/Users/m/git/personal/lubot",
        "enabled": true
    }
]
```

## Usage

MyCodeTree2LLM provides several commands to automate and streamline project workflows. Each command can be executed directly from the terminal.

1. **Setup Tools**:
    
    ```bash
    python project_manager.py setup
    ```
    
    This command copies essential tool files to the specified project directory.
    
2. **Switch Project**:
    
    ```bash
    python project_manager.py switch -p 1
    ```
    
    Switch to a specific project by providing its index or name.
    
3. **Run Workflow Automation**:
    
    ```bash
    python workflow_automation.py
    ```
    
    Executes the workflow for the current project, generating `tree.txt` and running file selection scripts.
    
4. **List Projects**:
    
    ```bash
    python project_manager.py list
    ```
    
    Lists all available projects with the current project marked with an asterisk (*).
    
5. **Show Current Project**:
    
    ```bash
    python project_manager.py current
    ```
    
    Displays the currently selected project.
    

### Project Management Commands

These commands can be run as aliases if added to your shell profile. For example, you can set up an alias `p` to refer to `project_manager.py`.

```bash
alias p="python /path/to/project_manager.py"
```

Now you can use:

```bash
p setup
p list
p switch -p 1
p current
```

## Testing

Unit tests are available in the `tests/` directory. To run tests, use:

```bash
python -m unittest discover tests
```

* * *

With this setup, MyCodeTree2LLM is ready to streamline your project management with automated workflows and easy-to-use project switching!