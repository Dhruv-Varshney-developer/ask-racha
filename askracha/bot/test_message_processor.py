"""
Unit tests for message processing and formatting system.
Tests question extraction, response formatting, validation, and truncation.
"""
import pytest
from datetime import datetime
from message_processor import MessageProcessor, MessageContext


class TestMessageProcessor:
    """Test cases for MessageProcessor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = MessageProcessor(max_response_length=2000)
    
    def test_extract_question_basic(self):
        """Test basic question extraction from Discord mention."""
        message = "<@123456789> How do I upload files to Storacha?"
        result = self.processor.extract_question(message)
        assert result == "How do I upload files to Storacha?"
    
    def test_extract_question_with_nickname_mention(self):
        """Test question extraction with nickname mention format."""
        message = "<@!987654321> What is the pricing for storage?"
        result = self.processor.extract_question(message)
        assert result == "What is the pricing for storage?"
    
    def test_extract_question_multiple_mentions(self):
        """Test question extraction with multiple mentions."""
        message = "<@123456789> <@987654321> How does the API work?"
        result = self.processor.extract_question(message)
        assert result == "How does the API work?"
    
    def test_extract_question_with_extra_whitespace(self):
        """Test question extraction with extra whitespace and newlines."""
        message = "<@123456789>   \n\n  How do I   get started?  \n  "
        result = self.processor.extract_question(message)
        assert result == "How do I get started?"
    
    def test_extract_question_empty_after_mention(self):
        """Test question extraction when only mention exists."""
        message = "<@123456789>"
        result = self.processor.extract_question(message)
        assert result is None
    
    def test_extract_question_empty_message(self):
        """Test question extraction with empty message."""
        result = self.processor.extract_question("")
        assert result is None
    
    def test_extract_question_none_input(self):
        """Test question extraction with None input."""
        result = self.processor.extract_question(None)
        assert result is None
    
    def test_extract_question_whitespace_only_after_mention(self):
        """Test question extraction with only whitespace after mention."""
        message = "<@123456789>   \n\n   "
        result = self.processor.extract_question(message)
        assert result is None


class TestResponseFormatting:
    """Test cases for response formatting."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = MessageProcessor(max_response_length=2000)
    
    def test_format_response_success(self):
        """Test formatting successful API response."""
        api_response = {
            'success': True,
            'answer': 'To upload files to Storacha, use the web interface or CLI tool.',
            'sources': ['docs.storacha.network/upload', 'github.com/storacha/cli']
        }
        result = self.processor.format_response(api_response)
        
        assert "**Hey! There, here's your answer:**" in result
        assert "To upload files to Storacha" in result
        assert "**Sources:**" in result
        assert "docs.storacha.network/upload" in result
        assert "🤖 AskRacha Bot by Storacha" in result
    
    def test_format_response_no_sources(self):
        """Test formatting response without sources."""
        api_response = {
            'success': True,
            'answer': 'Storacha is a decentralized storage platform.',
            'sources': []
        }
        result = self.processor.format_response(api_response)
        
        assert "**Hey! There, here's your answer:**" in result
        assert "Storacha is a decentralized storage platform." in result
        assert "**Sources:**" not in result
        assert "🤖 AskRacha Bot by Storacha" in result
    
    def test_format_response_many_sources(self):
        """Test formatting response with many sources (should limit to 3)."""
        api_response = {
            'success': True,
            'answer': 'Here is information about Storacha.',
            'sources': ['source1', 'source2', 'source3', 'source4', 'source5']
        }
        result = self.processor.format_response(api_response)
        
        assert "1. source1" in result
        assert "2. source2" in result
        assert "3. source3" in result
        assert "source4" not in result
        assert "source5" not in result
    
    def test_format_response_failure(self):
        """Test formatting failed API response."""
        api_response = {
            'success': False,
            'error_message': 'API timeout'
        }
        result = self.processor.format_response(api_response)
        
        assert "I'm having trouble processing your question right now" in result
        assert "🔧" in result
    
    def test_format_response_missing_answer(self):
        """Test formatting response with missing answer."""
        api_response = {
            'success': True,
            'answer': '',
            'sources': []
        }
        result = self.processor.format_response(api_response)
        
        assert "I couldn't find a good answer" in result
        assert "🤔" in result
    
    def test_format_response_none_answer(self):
        """Test formatting response with None answer."""
        api_response = {
            'success': True,
            'sources': []
        }
        result = self.processor.format_response(api_response)
        
        assert "I couldn't find a good answer" in result


class TestQuestionValidation:
    """Test cases for question validation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = MessageProcessor(max_response_length=2000)
    
    def test_is_valid_question_normal(self):
        """Test validation of normal questions."""
        assert self.processor.is_valid_question("How do I upload files?")
        assert self.processor.is_valid_question("What is Storacha?")
        assert self.processor.is_valid_question("Can you help me with the API?")
    
    def test_is_valid_question_edge_cases(self):
        """Test validation edge cases."""
        # Minimum length (3 characters)
        assert self.processor.is_valid_question("Hi?")
        assert not self.processor.is_valid_question("Hi")
        assert not self.processor.is_valid_question("H")
    
    def test_is_valid_question_empty_or_none(self):
        """Test validation of empty or None questions."""
        assert not self.processor.is_valid_question("")
        assert not self.processor.is_valid_question(None)
        assert not self.processor.is_valid_question("   ")
    
    def test_is_valid_question_non_string(self):
        """Test validation of non-string input."""
        assert not self.processor.is_valid_question(123)
        assert not self.processor.is_valid_question(['question'])
        assert not self.processor.is_valid_question({'question': 'test'})
    
    def test_is_valid_question_too_long(self):
        """Test validation of very long questions."""
        long_question = "a" * 1001  # Over 1000 character limit
        assert not self.processor.is_valid_question(long_question)
        
        acceptable_question = "a" * 1000  # Exactly at limit
        assert self.processor.is_valid_question(acceptable_question)
    
    def test_is_valid_question_only_punctuation(self):
        """Test validation of questions with only punctuation."""
        assert not self.processor.is_valid_question("???")
        assert not self.processor.is_valid_question("!!!")
        assert not self.processor.is_valid_question("...")
        assert not self.processor.is_valid_question("@#$%")
    
    def test_is_valid_question_mixed_content(self):
        """Test validation of questions with mixed content."""
        assert self.processor.is_valid_question("What??? Really?")
        assert self.processor.is_valid_question("Help! I need assistance.")
        assert self.processor.is_valid_question("123 + 456 = ?")


class TestResponseTruncation:
    """Test cases for response truncation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = MessageProcessor(max_response_length=100)  # Small limit for testing
    
    def test_truncate_response_no_truncation_needed(self):
        """Test truncation when text is within limits."""
        short_text = "This is a short response."
        result = self.processor.truncate_response(short_text)
        assert result == short_text
        assert "[Response truncated" not in result
    
    def test_truncate_response_basic_truncation(self):
        """Test basic truncation of long text."""
        long_text = "a" * 200  # Much longer than limit
        result = self.processor.truncate_response(long_text)
        
        assert len(result) <= 100
        assert "[Response truncated due to Discord's character limit]" in result
    
    def test_truncate_response_sentence_boundary(self):
        """Test truncation at sentence boundaries."""
        # Create text longer than limit with clear sentence boundaries
        text = "First sentence. " * 20  # Much longer than 100 char limit
        result = self.processor.truncate_response(text)
        
        assert "[Response truncated" in result
        # Should try to cut at sentence boundary
        assert result.count('.') >= 1  # At least one complete sentence
    
    def test_truncate_response_word_boundary(self):
        """Test truncation at word boundaries when no sentence boundary found."""
        # Create text without sentence endings, longer than limit
        text = "word " * 50  # No periods, just words - much longer than 100 chars
        result = self.processor.truncate_response(text)
        
        assert "[Response truncated" in result
        # Should end with complete word, not cut mid-word
        truncated_part = result.split('\n\n*[Response truncated')[0]
        assert truncated_part.endswith('word')  # Should end with complete word
    
    def test_truncate_response_very_long_single_word(self):
        """Test truncation with very long single word."""
        text = "a" * 200
        result = self.processor.truncate_response(text)
        
        assert len(result) <= 100
        assert "[Response truncated" in result


class TestMessageContext:
    """Test cases for MessageContext dataclass."""
    
    def test_message_context_creation(self):
        """Test MessageContext creation and attributes."""
        timestamp = datetime.now()
        context = MessageContext(
            user_id="123456789",
            username="testuser",
            channel_id="987654321",
            guild_id="111222333",
            message_id="444555666",
            timestamp=timestamp,
            question="How does this work?"
        )
        
        assert context.user_id == "123456789"
        assert context.username == "testuser"
        assert context.channel_id == "987654321"
        assert context.guild_id == "111222333"
        assert context.message_id == "444555666"
        assert context.timestamp == timestamp
        assert context.question == "How does this work?"


class TestIntegrationScenarios:
    """Integration test scenarios for complete message processing flow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = MessageProcessor(max_response_length=2000)
    
    def test_complete_processing_flow_success(self):
        """Test complete flow from message to formatted response."""
        # Step 1: Extract question
        message = "<@123456789> How do I get started with Storacha?"
        question = self.processor.extract_question(message)
        assert question is not None
        
        # Step 2: Validate question
        assert self.processor.is_valid_question(question)
        
        # Step 3: Format API response
        api_response = {
            'success': True,
            'answer': 'To get started with Storacha, visit our documentation.',
            'sources': ['docs.storacha.network']
        }
        formatted = self.processor.format_response(api_response)
        
        assert "**Hey! There, here's your answer:**" in formatted
        assert "To get started with Storacha" in formatted
        assert "🤖 AskRacha Bot by Storacha" in formatted
    
    def test_complete_processing_flow_invalid_question(self):
        """Test complete flow with invalid question."""
        # Extract empty question
        message = "<@123456789>"
        question = self.processor.extract_question(message)
        assert question is None
        
        # If question is None, validation should handle it
        assert not self.processor.is_valid_question(question)
    
    def test_complete_processing_flow_api_failure(self):
        """Test complete flow with API failure."""
        # Valid question extraction and validation
        message = "<@123456789> Help me please"
        question = self.processor.extract_question(message)
        assert self.processor.is_valid_question(question)
        
        # API failure response
        api_response = {
            'success': False,
            'error_message': 'Service unavailable'
        }
        formatted = self.processor.format_response(api_response)
        
        assert "I'm having trouble processing your question" in formatted
        assert "🔧" in formatted


if __name__ == "__main__":
    pytest.main([__file__, "-v"])