from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
import uuid
import json
import os
from dotenv import load_dotenv
from google import genai
import tiktoken

load_dotenv()

@dataclass
class Message:
    role: str  # "user" or "assistant"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict = field(default_factory=dict)

@dataclass
class ChatSession:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[Message] = field(default_factory=list)
    context_summary: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_active: str = field(default_factory=lambda: datetime.now().isoformat())

class ChatContextManager:
    def __init__(self):
        self.sessions: Dict[str, ChatSession] = {}
        self.max_context_messages = 10  # Default max messages
        self.max_tokens = 4000 
        
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
            
        self.genai_client = genai.Client(api_key=self.gemini_api_key)
    
    def create_session(self) -> str:
        """Create a new chat session and return its ID"""
        session = ChatSession()
        self.sessions[session.session_id] = session
        return session.session_id
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get a session by ID"""
        return self.sessions.get(session_id)
    
    def add_message(self, session_id: str, role: str, content: str, metadata: Dict = None) -> bool:
        """Add a message to a session"""
        session = self.get_session(session_id)
        if not session:
            return False
            
        session.messages.append(Message(role=role, content=content, metadata=metadata or {}))
        session.last_active = datetime.now().isoformat()
        
        if len(session.messages) > self.max_context_messages:
            self._summarize_session(session)
            
        return True
    
    def get_context(self, session_id: str) -> List[Dict]:
        """Get formatted context for a session"""
        session = self.get_session(session_id)
        if not session:
            return []
            
        context = []
        if session.context_summary:
            context.append({
                "role": "system",
                "content": f"Previous conversation summary: {session.context_summary}"
            })
            
        for msg in session.messages[-self.max_context_messages:]:
            context.append({
                "role": msg.role,
                "content": msg.content
            })
            
        return context
    
    def _summarize_session(self, session: ChatSession) -> None:
        """Summarize older messages using Gemini"""
        messages_for_context = [{
            "role": msg.role,
            "content": msg.content
        } for msg in session.messages]
        
        current_tokens = count_tokens(messages_for_context)
        
        if current_tokens < self.max_tokens:
            return
        
        recent_messages = []
        recent_tokens = 0
        for msg in reversed(session.messages):
            msg_tokens = count_tokens([{"role": msg.role, "content": msg.content}])
            if recent_tokens + msg_tokens > self.max_tokens * 0.5: 
                break
            recent_messages.insert(0, msg)
            recent_tokens += msg_tokens
        
        older_messages = session.messages[:-len(recent_messages)] if recent_messages else session.messages
        if older_messages:
            conversation = "\n".join([f"{msg.role}: {msg.content}" for msg in older_messages])
            prompt = f"""Summarize this conversation while preserving key technical details and context:

{conversation}

Provide a concise summary that captures:
1. Main technical topics discussed
2. Key decisions or information shared
3. Important context for future reference

Summary:"""

            try:
                response = self.genai_client.models.generate_content(
                    model='gemini-pro',
                    contents=prompt
                )
                summary = response.text if response.text else "No summary generated."
            except Exception as e:
                print(f"Error generating summary: {e}")
                summary = f"Earlier conversation included {len(older_messages)} messages about: " + \
                         ", ".join(msg.content[:50] + "..." for msg in older_messages[:3])
            
            session.context_summary = summary
            session.messages = recent_messages

def count_tokens(messages: List[Dict]) -> int:
    """Count the number of tokens in a list of messages"""
    encoding = tiktoken.get_encoding("cl100k_base")
    
    total_tokens = 0
    for message in messages:
        content_tokens = len(encoding.encode(message.get("content", "")))
        total_tokens += content_tokens + 4  
    
    return total_tokens
