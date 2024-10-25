import os

def create_dummy_git_repositories(base_path):
    projects = [
        'SubSync', 'Auto-GPTapr21', 'Auto-GPTapr22', 'ChatGPT-History-Downloader',
        'GenAICodeUpdater', 'KanbanView', 'Ollama', 'SuperAGI', 'TaskWeaver',
        'Telegram-Wallet-Token-ERC20', 'WhisperDropbox', 'aaiguru_site', 'agama'
    ]

    for project in projects:
        project_path = os.path.join(base_path, project)
        os.makedirs(project_path, exist_ok=True)
        # Create a .git directory to simulate a git repository
        os.makedirs(os.path.join(project_path, '.git'), exist_ok=True)

# Change '~/git' to wherever you want to set up the dummy repositories
create_dummy_git_repositories(os.path.expanduser('~/git'))
