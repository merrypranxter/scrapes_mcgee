"""
GitHub integration for Scrapes McGee - push scraped content directly to repos.
"""
import os
from pathlib import Path
from typing import Optional, List
from github import Github, GithubException
from datetime import datetime


class GitHubPusher:
    """Handle pushing scraped content to GitHub repositories."""
    
    def __init__(self, token: Optional[str] = None):
        """Initialize GitHub client with token."""
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("GitHub token not found. Set GITHUB_TOKEN in .env")
        
        self.gh = Github(self.token)
        self.user = self.gh.get_user()
    
    def list_repos(self) -> List[str]:
        """List all repos for the authenticated user."""
        return [repo.name for repo in self.user.get_repos()]
    
    def push_file(
        self,
        repo_name: str,
        file_path: str,
        content: str,
        commit_message: Optional[str] = None,
        branch: str = "main"
    ) -> str:
        """
        Push a file to a GitHub repository.
        
        Args:
            repo_name: Name of the repo (e.g., "Terence_McKenna_Corpus")
            file_path: Path in repo (e.g., "data/erowid_dmt.json")
            content: File content as string
            commit_message: Optional custom commit message
            branch: Branch to push to (default: main)
        
        Returns:
            URL to the committed file
        """
        try:
            # Get the repo
            repo = self.user.get_repo(repo_name)
            
            # Default commit message
            if not commit_message:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                commit_message = f"Scrapes McGee: Add {Path(file_path).name} [{timestamp}]"
            
            # Check if file exists (update vs create)
            try:
                existing_file = repo.get_contents(file_path, ref=branch)
                # Update existing file
                result = repo.update_file(
                    path=file_path,
                    message=commit_message,
                    content=content,
                    sha=existing_file.sha,
                    branch=branch
                )
                action = "Updated"
            except GithubException:
                # File doesn't exist, create it
                result = repo.create_file(
                    path=file_path,
                    message=commit_message,
                    content=content,
                    branch=branch
                )
                action = "Created"
            
            file_url = f"https://github.com/{self.user.login}/{repo_name}/blob/{branch}/{file_path}"
            return action, file_url
        
        except GithubException as e:
            raise Exception(f"GitHub error: {e.data.get('message', str(e))}")
    
    def push_multiple_files(
        self,
        repo_name: str,
        files: dict,  # {file_path: content}
        commit_message: Optional[str] = None,
        branch: str = "main"
    ) -> List[str]:
        """
        Push multiple files to a repo in a single commit.
        
        Args:
            repo_name: Name of the repo
            files: Dict of {file_path: content}
            commit_message: Optional custom commit message
            branch: Branch to push to
        
        Returns:
            List of file URLs
        """
        repo = self.user.get_repo(repo_name)
        
        if not commit_message:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            commit_message = f"Scrapes McGee: Batch upload [{timestamp}]"
        
        # Get current commit SHA
        ref = repo.get_git_ref(f"heads/{branch}")
        base_tree = repo.get_git_tree(ref.object.sha)
        
        # Create blobs for each file
        element_list = []
        for file_path, content in files.items():
            blob = repo.create_git_blob(content, "utf-8")
            element_list.append({
                "path": file_path,
                "mode": "100644",
                "type": "blob",
                "sha": blob.sha
            })
        
        # Create tree and commit
        tree = repo.create_git_tree(element_list, base_tree)
        parent = repo.get_git_commit(ref.object.sha)
        commit = repo.create_git_commit(commit_message, tree, [parent])
        ref.edit(commit.sha)
        
        # Return URLs
        urls = [
            f"https://github.com/{self.user.login}/{repo_name}/blob/{branch}/{fp}"
            for fp in files.keys()
        ]
        return urls
    
    def create_repo(
        self,
        name: str,
        description: Optional[str] = None,
        private: bool = False
    ) -> str:
        """
        Create a new GitHub repository.
        
        Args:
            name: Repository name
            description: Optional description
            private: Make repo private (default: False)
        
        Returns:
            URL to the new repo
        """
        try:
            repo = self.user.create_repo(
                name=name,
                description=description or f"Created by Scrapes McGee",
                private=private,
                auto_init=True  # Creates with README
            )
            return repo.html_url
        except GithubException as e:
            raise Exception(f"Failed to create repo: {e.data.get('message', str(e))}")
