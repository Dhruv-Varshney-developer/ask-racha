"""
Message processing and formatting system for Discord bot integration.
Handles question extraction, response formatting, and message validation.
"""
import logging
import re
from typing import Optional
from dataclasses import dataclass
from datetime import datetime
from html import unescape
from urllib.parse import urlparse

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
    
    def _strip_html(self, text: str) -> str:
        """Remove HTML tags from text and unescape HTML entities."""
        if not text:
            return ""
        text = unescape(text)
        text = re.sub(r"<[^>]+>", " ", text)
        text = " ".join(text.split())
        return text
    
    def _escape_markdown(self, text: str) -> str:
        """Escape Markdown characters that can break Discord formatting."""
        if not text:
            return ""

        specials = r"\\`*_{}[]()#+!|>"
        return re.sub(f"([${specials}])", r"\\\1", text)
    
    def _normalize_url(self, url: str) -> Optional[str]:
        """Return URL if it has a scheme/host; otherwise None to avoid broken links."""
        if not url:
            return None
        parsed = urlparse(url)
        if parsed.scheme in ("http", "https") and parsed.netloc:
            return url
        if not parsed.scheme and parsed.path:
            candidate = "https://" + parsed.path
            p2 = urlparse(candidate)
            if p2.scheme and p2.netloc:
                return candidate
        return None
    
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
        if not api_response.get('success', False):
            error_msg = api_response.get('error_message', 'Unknown error occurred')
            logger.warning(f"API response indicates failure: {error_msg}")
            return "I'm having trouble processing your question right now. Please try again later! 🔧"
        
        answer = api_response.get('answer', '')
        if not answer:
            logger.warning("API response missing answer content")
            return "I couldn't find a good answer to your question. Could you try rephrasing it? 🤔"
        
        # Truncate if necessary
        formatted_response = self.truncate_response(answer)
        
        logger.debug(f"Formatted response length: {len(formatted_response)}")
        return formatted_response
    
    def is_valid_question(self, question: str) -> bool:
        """
        Validate question content and length.
        
        Args:
            question: The question to validate
            
        Returns:
            bool: True if question is valid, False otherwise
        """
        if not question or not isinstance(question, str):
            logger.debug("Question is empty or not a string")
            return False
        
        # Remove extra whitespace for validation
        cleaned_question = question.strip()
        
        # Check minimum length (at least 3 characters)
        if len(cleaned_question) < 3:
            logger.debug(f"Question too short: {len(cleaned_question)} characters")
            return False
        
        # Check maximum length (reasonable limit for questions)
        if len(cleaned_question) > 1000:
            logger.debug(f"Question too long: {len(cleaned_question)} characters")
            return False
        
        # Check if it's just punctuation or special characters
        import re
        if not re.search(r'[a-zA-Z0-9]', cleaned_question):
            logger.debug("Question contains no alphanumeric characters")
            return False
        
        logger.debug(f"Question validation passed: {len(cleaned_question)} characters")
        return True
    
    def truncate_response(self, text: str) -> str:
        """
        Truncate response to fit Discord message limits.
        
        Args:
            text: The text to truncate
            
        Returns:
            str: Truncated text with indicator if shortened
        """
        if len(text) <= self.max_response_length:
            return text
        
        # Reserve space for truncation indicator
        truncation_indicator = "\n\n*[Response truncated due to Discord's character limit]*"
        available_length = self.max_response_length - len(truncation_indicator)
        
        # Try to truncate at a sentence boundary if possible
        truncated = text[:available_length]
        
        # Look for the last sentence ending within a reasonable range
        sentence_endings = ['. ', '! ', '? ', '\n\n']
        best_cut = -1
        
        # Search backwards from the end for a good cut point
        for i in range(min(100, len(truncated))):  # Look back up to 100 chars
            pos = available_length - i
            if pos < available_length * 0.8:  # Don't cut too much (at least 80% of content)
                break
            
            for ending in sentence_endings:
                if truncated[pos:pos+len(ending)] == ending:
                    best_cut = pos + len(ending)
                    break
            
            if best_cut != -1:
                break
        
        # Use the sentence boundary if found, otherwise just cut at character limit
        if best_cut != -1:
            truncated = truncated[:best_cut].rstrip()
        else:
            # Cut at word boundary if possible
            words = truncated.split()
            if len(words) > 1:
                truncated = ' '.join(words[:-1])
        
        result = truncated + truncation_indicator
        logger.info(f"Response truncated from {len(text)} to {len(result)} characters")
        return result