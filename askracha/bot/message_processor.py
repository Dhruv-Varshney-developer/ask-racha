"""
Message processing and formatting system.
This module will be implemented in task 3.
"""
import logging
from typing import Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class MessageContext:
    """Context information for a Discord message."""
    user_id: str
    username: str
    channel_id: str
    guild_id: str
    message_id: str
    timestamp: datetime
    question: str


class MessageProcessor:
    """Handles message processing and response formatting."""
    
    def __init__(self, max_response_length: int):
        """Initialize the message processor."""
        self.max_response_length = max_response_length
        logger.info(f"Message processor initialized with max length {max_response_length}")
    
    def extract_question(self, message_content: str) -> Optional[str]:
        """
        Extract question from Discord mention.
        
        Args:
            message_content: The raw Discord message content
            
        Returns:
            Optional[str]: Extracted question or None if invalid
        """
        if not message_content:
            logger.debug("Empty message content")
            return None
        
        # Remove the bot mention (e.g., <@!123456789> or <@123456789>)
        import re
        mention_pattern = r'<@!?\d+>'
        cleaned_content = re.sub(mention_pattern, '', message_content).strip()
        
        # Clean up extra whitespace and newlines
        cleaned_content = ' '.join(cleaned_content.split())
        
        if not cleaned_content:
            logger.debug("No question content after removing mention")
            return None
        
        logger.debug(f"Extracted question: {cleaned_content[:100]}...")
        return cleaned_content
    
    def format_response(self, api_response: dict) -> str:
        """
        Format API response for Discord display.
        
        Args:
            api_response: Response from the AskRacha API
            
        Returns:
            str: Formatted response for Discord
        """
        # TODO: Implement in task 3
        logger.warning("Response formatting not yet implemented")
        return "Response formatting not yet implemented"
    
    def is_valid_question(self, question: str) -> bool:
        """
        Validate question content and length.
        
        Args:
            question: The question to validate
            
        Returns:
            bool: True if question is valid, False otherwise
        """
        # TODO: Implement in task 3
        logger.warning("Question validation not yet implemented")
        return False
    
    def truncate_response(self, text: str) -> str:
        """
        Truncate response to fit Discord message limits.
        
        Args:
            text: The text to truncate
            
        Returns:
            str: Truncated text with indicator if shortened
        """
        # TODO: Implement in task 3
        if len(text) <= self.max_response_length:
            return text
        
        truncated = text[:self.max_response_length - 50]  # Leave room for indicator
        return f"{truncated}...\n\n*[Response truncated due to length]*"