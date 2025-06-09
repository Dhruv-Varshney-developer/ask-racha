import os
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, Settings
from llama_index.readers.web import SimpleWebPageReader
from llama_index.readers.github import GithubRepositoryReader
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

load_dotenv()

class StorachaRAG:
    def __init__(self):
        # Configure LlamaIndex settings
        Settings.llm = OpenAI(model="gpt-3.5-turbo", temperature=0.1)
        Settings.embed_model = OpenAIEmbedding()
        
        self.index = None
        
    def load_from_urls(self, urls):
        """Load documents from web URLs"""
        print("Loading web documents...")
        reader = SimpleWebPageReader(html_to_text=True)
        documents = reader.load_data(urls)
        return documents
    
    def load_from_github(self, github_urls):
        """Load documents from GitHub repositories"""
        print("Loading GitHub repositories...")
        documents = []
        
        for url in github_urls:
            # Extract owner and repo from URL
            parts = url.replace('https://github.com/', '').split('/')
            owner, repo = parts[0], parts[1]
            
            reader = GithubRepositoryReader(
                github_token=os.getenv("GITHUB_TOKEN"),
                owner=owner,
                repo=repo,
                use_parser=False,
                verbose=True,
                filter_file_extensions=[".md", ".py", ".js", ".ts", ".txt"]
            )
            repo_docs = reader.load_data(branch="main")
            documents.extend(repo_docs)
            
        return documents
    
    def build_index(self, all_urls):
        """Build the RAG index from URLs"""
        # Separate GitHub URLs from regular URLs
        github_urls = [url for url in all_urls if 'github.com' in url]
        web_urls = [url for url in all_urls if 'github.com' not in url]
        
        all_documents = []
        
        # Load web documents
        if web_urls:
            web_docs = self.load_from_urls(web_urls)
            all_documents.extend(web_docs)
        
        # Load GitHub documents
        if github_urls:
            github_docs = self.load_from_github(github_urls)
            all_documents.extend(github_docs)
        
        print(f"Total documents loaded: {len(all_documents)}")
        
        # Create index
        self.index = VectorStoreIndex.from_documents(all_documents)
        return self.index
    
    def query(self, question):
        """Query the RAG system"""
        if not self.index:
            return "Index not built yet. Please build the index first."
        
        query_engine = self.index.as_query_engine()
        response = query_engine.query(question)
        return str(response)