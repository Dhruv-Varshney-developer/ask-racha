import os
from typing import List, Dict
from llama_index.core import Document

class RepoProcessor:
    """Processes GitHub repositories to extract meaningful content for RAG"""
    
    def __init__(self, repos_dir: str = "repos"):
        """Initialize with path to repos directory"""
        self.repos_dir = repos_dir
        self.github_base_url = "https://github.com/storacha"
        
    def process_repos(self) -> List[Document]:
        """Process all repositories in the repos directory"""
        documents = []
        
        repo_dirs = [d for d in os.listdir(self.repos_dir) 
                    if os.path.isdir(os.path.join(self.repos_dir, d)) and not d.startswith('.')]
        
        for repo_dir in repo_dirs:
            repo_path = os.path.join(self.repos_dir, repo_dir)
            repo_docs = self.process_repo_readmes(repo_path, repo_dir)
            documents.extend(repo_docs)
            
        return documents
    
    def process_repo_readmes(self, repo_path: str, repo_name: str) -> List[Document]:
        """Process all README files in a repository"""
        documents = []
        
        for root, _, files in os.walk(repo_path):
            for file in files:
                if file.lower() == 'readme.md':
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        rel_path = os.path.relpath(file_path, repo_path)
                        
                        github_url = f"{self.github_base_url}/{repo_name}/blob/main/{rel_path}"
                        
                        doc = Document(
                            text=content,
                            metadata={
                                'source': github_url,
                                'type': 'readme',
                                'repo': repo_name,
                                'path': rel_path
                            }
                        )
                        documents.append(doc)
                        print(f"Processed README: {rel_path} from {repo_name}")
                        
                    except Exception as e:
                        print(f"Error processing {file_path}: {e}")
                        
        return documents