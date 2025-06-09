import os
import requests
import json
import re
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

class StorachaRAG:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.documents = []
        
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        # Remove very short lines
        lines = [line.strip() for line in text.split('\n') if len(line.strip()) > 10]
        return '\n'.join(lines)
    
    def scrape_url(self, url: str) -> str:
        """Simple web scraping"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            # Simple text extraction (no BeautifulSoup to avoid dependencies)
            html = response.text
            
            # Remove script and style tags
            html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
            html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
            
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', ' ', html)
            
            # Decode HTML entities
            text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
            
            return self.clean_text(text)[:8000]  # Limit size
            
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return ""
    
    def simple_similarity(self, text1: str, text2: str) -> float:
        """Simple word-based similarity"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
            
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def load_documents(self, urls: List[str]):
        """Load documents from URLs"""
        self.documents = []
        
        for url in urls:
            print(f"Loading: {url}")
            content = self.scrape_url(url)
            if content and len(content) > 100:
                self.documents.append({
                    'content': content,
                    'source': url,
                    'preview': content[:200] + "..."
                })
                print(f"✓ Loaded {len(content)} characters")
            else:
                print(f"✗ Failed to load content")
        
        print(f"\nTotal documents loaded: {len(self.documents)}")
    
    def find_relevant_content(self, query: str, max_docs: int = 2) -> List[Dict]:
        """Find most relevant documents"""
        if not self.documents:
            return []
        
        scored_docs = []
        query_lower = query.lower()
        
        for doc in self.documents:
            content_lower = doc['content'].lower()
            
            # Simple scoring: keyword matches + similarity
            keyword_score = sum(1 for word in query.split() if word.lower() in content_lower)
            similarity_score = self.simple_similarity(query, doc['content'])
            
            total_score = keyword_score + similarity_score * 10
            
            if total_score > 0:
                scored_docs.append({
                    'content': doc['content'][:3000],  # Limit context
                    'source': doc['source'],
                    'score': total_score
                })
        
        # Sort by score and return top documents
        scored_docs.sort(key=lambda x: x['score'], reverse=True)
        return scored_docs[:max_docs]
    
    def call_openai(self, messages: List[Dict]) -> str:
        """Call OpenAI API directly"""
        try:
            headers = {
                'Authorization': f'Bearer {self.openai_api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': 'gpt-3.5-turbo',
                'messages': messages,
                'max_tokens': 500,
                'temperature': 0.1
            }
            
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                return f"API Error: {response.status_code} - {response.text}"
                
        except Exception as e:
            return f"Error calling OpenAI: {e}"
    
    def query(self, question: str) -> str:
        """Query the RAG system"""
        if not self.documents:
            return "No documents loaded. Please load documents first."
        
        # Find relevant documents
        relevant_docs = self.find_relevant_content(question)
        
        if not relevant_docs:
            return "No relevant information found in the loaded documents."
        
        # Create context
        context_parts = []
        for i, doc in enumerate(relevant_docs, 1):
            context_parts.append(f"Document {i} (Source: {doc['source']}):\n{doc['content']}")
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Create messages for OpenAI
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant answering questions about Storacha based on the provided documentation. Use only the information from the context provided. If the context doesn't contain enough information to answer the question, say so."
            },
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer based on the context above:"
            }
        ]
        
        return self.call_openai(messages)