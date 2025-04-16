"""
Provides services for interacting with the OpenAI API.

Handles tasks like generating summaries, verifying statements, answering questions,
and creating comments using various OpenAI models.
"""
import logging
from typing import List, Dict, Any
from openai import AsyncOpenAI
from bot.config import OPENAI_API_KEY, SUMMARY_MODEL, GPT_MODEL, PROOF_MODEL, COMMENT_MODEL, CONCISE_RESPONSES

# Configure OpenAI client
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

logger = logging.getLogger(__name__)

# Define a timeout for API calls
API_TIMEOUT = 30  # seconds

# Global setting for concise responses
# CONCISE_RESPONSES = True  # Now imported from config

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
            
            system_content = "You are an assistant that creates concise and informative summaries of chat conversations."
            if CONCISE_RESPONSES:
                system_content += " Always provide extremely brief and concise responses, focusing only on the most essential information."
            
            response = await client.chat.completions.create(
                model=SUMMARY_MODEL,
                messages=[
                    {"role": "system", "content": system_content},
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
            system_content = "You are a factual assistant that verifies statements. Analyze the statement, determine its factuality, and provide evidence."
            if CONCISE_RESPONSES:
                system_content += " Be extremely concise and to the point. Focus on key facts only."
            
            response = await client.chat.completions.create(
                model=PROOF_MODEL,
                messages=[
                    {"role": "system", "content": system_content},
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
            
            system_content = "You are a witty and insightful assistant that provides comments on ongoing discussions."
            if CONCISE_RESPONSES:
                system_content += " Keep your comments extremely brief and to the point."
            
            response = await client.chat.completions.create(
                model=COMMENT_MODEL,
                messages=[
                    {"role": "system", "content": system_content},
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
    async def answer_question(question: str, context_messages: List[Dict[str, Any]] = None) -> str:
        """
        Answers a given question using the general-purpose GPT_MODEL.
        
        Args:
            question: The question string to be answered.
            context_messages: Optional list of recent message dictionaries to provide context.
            
        Returns:
            A string containing the AI-generated answer, or an error message.
        """
        try:
            system_content = "You are a helpful, knowledgeable, accurate, and friendly assistant."
            if CONCISE_RESPONSES:
                system_content += " Always provide extremely brief and concise answers. Use as few words as possible while remaining clear and helpful."
            
            messages = [
                {"role": "system", "content": system_content}
            ]
            
            # Add context messages if provided
            if context_messages:
                context = "Recent chat context:\n\n"
                for msg in context_messages:
                    context += f"{msg['user']}: {msg['text']}\n"
                context += "\n"
                messages.append({"role": "user", "content": context})
            
            # Add the question
            messages.append({"role": "user", "content": question})
            
            response = await client.chat.completions.create(
                model=GPT_MODEL,
                messages=messages,
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
            system_content = "You are a witty assistant that creates clever, slightly sarcastic, but ultimately good-natured roasts of posts. Keep it light and funny, not mean-spirited."
            if CONCISE_RESPONSES:
                system_content += " Make your roasts very brief and punchy - one or two sentences maximum."
            
            response = await client.chat.completions.create(
                model=COMMENT_MODEL,
                messages=[
                    {"role": "system", "content": system_content},
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
    
    @staticmethod
    async def analyze_image(image_bytes: bytes, instructions: str) -> str:
        """
        Analyzes an image using OpenAI's GPT-4 Vision model, following user instructions.
        Args:
            image_bytes: The image file as bytes.
            instructions: User's analysis instructions or strategy.
        Returns:
            A string containing the AI-generated analysis or an error message.
        """
        try:
            # Upload image to OpenAI's vision API (using base64 encoding for bytes)
            import base64
            import io
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')
            # Compose the prompt
            prompt = (
                f"Analyze the following chart or image according to these instructions: {instructions}\n"
                "Provide feedback and insights, but do not give financial advice."
            )
            
            system_content = "You are an expert assistant that analyzes images and charts according to user strategies. Never provide financial advice."
            if CONCISE_RESPONSES:
                system_content += " Provide extremely concise analysis. Focus only on the most important insights using minimal words."
            
            response = await client.chat.completions.create(
                model=GPT_MODEL,
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}
                    ]}
                ],
                max_tokens=800,
                temperature=0.5,
                timeout=API_TIMEOUT
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error analyzing image: {str(e)}")
            return "Sorry, I couldn't analyze the image at this time." 