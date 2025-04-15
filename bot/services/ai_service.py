"""
Provides services for interacting with the OpenAI API.

Handles tasks like generating summaries, verifying statements, answering questions,
and creating comments using various OpenAI models.
"""
import logging
from typing import List, Dict, Any
from openai import AsyncOpenAI
from bot.config import OPENAI_API_KEY, SUMMARY_MODEL, GPT_MODEL, PROOF_MODEL, COMMENT_MODEL

# Configure OpenAI client
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

logger = logging.getLogger(__name__)

# Define a timeout for API calls
API_TIMEOUT = 30  # seconds

class AIService:
    """
    A service class that acts as an interface to OpenAI's API for various AI tasks.

    Provides static methods to generate summaries, verify statements, generate comments,
    answer questions, and generate roasts, using pre-configured OpenAI models.
    Includes basic error handling and logging for API interactions.
    """
    
    @staticmethod
    async def generate_summary(messages: List[Dict[str, Any]]) -> str:
        """
        Generates a concise summary of a list of chat messages using the SUMMARY_MODEL.
        
        Args:
            messages: A list of dictionaries, where each dictionary represents a message
                      and must contain 'user' (str) and 'text' (str) keys.
            
        Returns:
            A string containing the AI-generated summary, or an error message.
        """
        if not messages:
            return "No messages to summarize."
        
        try:
            # Format messages for OpenAI
            prompt = "Summarize the following chat messages, highlighting key points and important information:\n\n"
            for msg in messages:
                prompt += f"{msg['user']}: {msg['text']}\n"
            
            response = await client.chat.completions.create(
                model=SUMMARY_MODEL,
                messages=[
                    {"role": "system", "content": "You are an assistant that creates concise and informative summaries of chat conversations."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.7,
                timeout=API_TIMEOUT
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return "Sorry, I couldn't generate a summary at this time."
    
    @staticmethod
    async def verify_statement(statement: str) -> str:
        """
        Verifies the factuality of a given statement using the PROOF_MODEL.
        
        Args:
            statement: The text statement to be fact-checked.
            
        Returns:
            A string containing the AI's analysis of the statement's factuality,
            potentially including evidence, or an error message.
        """
        try:
            response = await client.chat.completions.create(
                model=PROOF_MODEL,
                messages=[
                    {"role": "system", "content": "You are a factual assistant that verifies statements. "
                                                  "Analyze the statement, determine its factuality, and provide evidence."},
                    {"role": "user", "content": f"Please verify this statement: \"{statement}\""}
                ],
                max_tokens=1000,
                temperature=0.2,
                timeout=API_TIMEOUT
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error verifying statement: {str(e)}")
            return "Sorry, I couldn't verify that statement at this time."
    
    @staticmethod
    async def generate_comment(context_messages: List[Dict[str, Any]]) -> str:
        """
        Generates an insightful comment based on the context of recent chat messages
        using the COMMENT_MODEL.
        
        Args:
            context_messages: A list of recent message dictionaries (containing 'user'
                              and 'text') to provide context for the comment.
            
        Returns:
            A string containing the AI-generated comment, or an error message.
        """
        if not context_messages:
            return "I don't see any recent messages to comment on."
        
        try:
            # Format context for OpenAI
            context = "Here are the recent messages in the chat:\n\n"
            for msg in context_messages:
                context += f"{msg['user']}: {msg['text']}\n"
            
            context += "\nBased on these messages, provide an insightful comment about the discussion."
            
            response = await client.chat.completions.create(
                model=COMMENT_MODEL,
                messages=[
                    {"role": "system", "content": "You are a witty and insightful assistant that provides comments on ongoing discussions."},
                    {"role": "user", "content": context}
                ],
                max_tokens=400,
                temperature=0.8,
                timeout=API_TIMEOUT
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating comment: {str(e)}")
            return "Sorry, I couldn't generate a comment at this time."
    
    @staticmethod
    async def answer_question(question: str) -> str:
        """
        Answers a given question using the general-purpose GPT_MODEL.
        
        Args:
            question: The question string to be answered.
            
        Returns:
            A string containing the AI-generated answer, or an error message.
        """
        try:
            response = await client.chat.completions.create(
                model=GPT_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful, knowledgeable, accurate, and friendly assistant."},
                    {"role": "user", "content": question}
                ],
                max_tokens=1000,
                temperature=0.7,
                timeout=API_TIMEOUT
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error answering question: {str(e)}")
            return "Sorry, I couldn't answer that question at this time."
    
    @staticmethod
    async def roast_post(post_text: str) -> str:
        """
        Generates a humorous, light-hearted roast for a given text post using the COMMENT_MODEL.
        
        Args:
            post_text: The text of the post to be roasted.
            
        Returns:
            A string containing the AI-generated roast, or an error message.
        """
        try:
            response = await client.chat.completions.create(
                model=COMMENT_MODEL,
                messages=[
                    {"role": "system", "content": "You are a witty assistant that creates clever, slightly sarcastic, "
                                                  "but ultimately good-natured roasts of posts. Keep it light and funny, not mean-spirited."},
                    {"role": "user", "content": f"Please roast this post in a funny way: \"{post_text}\""}
                ],
                max_tokens=200,
                temperature=0.9,
                timeout=API_TIMEOUT
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating roast: {str(e)}")
            return "Sorry, I couldn't roast that post at this time." 