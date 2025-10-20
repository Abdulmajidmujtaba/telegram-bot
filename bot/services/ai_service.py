"""
Provides services for interacting with the OpenAI API.

Handles tasks like generating summaries, verifying statements, answering questions,
and creating comments using various OpenAI models.
"""
import asyncio
import copy
import logging
from collections import deque
from typing import List, Dict, Any, Deque
from openai import AsyncOpenAI
from bot.config import (
    OPENAI_API_KEY,
    SUMMARY_MODEL,
    GPT_MODEL,
    PROOF_MODEL,
    COMMENT_MODEL,
    CONCISE_RESPONSES,
    IMAGE_ANALYSIS_MODEL,
    IMAGE_ANALYSIS_TOOLS,
    IMAGE_ANALYSIS_INCLUDE_FIELDS,
    IMAGE_ANALYSIS_STORE_RESPONSES,
    IMAGE_ANALYSIS_TEXT_FORMAT,
    IMAGE_ANALYSIS_REASONING_EFFORT
)

# Default guidance applied to image analysis if users do not supply custom instructions.
DEFAULT_IMAGE_ANALYSIS_INSTRUCTIONS = """You are Gigsbot, a seasoned professional forex trader with expertise in technical analysis and price action trading. Your primary analytical framework is the Forex Master Pattern, supplemented by Smart Money Concepts (SMC), support/resistance levels, and other relevant technical analysis tools.
Core Analysis Framework
When analyzing charts, you must:
Apply Forex Master Pattern methodology to identify:
Market structure (accumulation, manipulation, distribution phases)
Key areas of value and premium zones
Liquidity pools and stop hunts
Market maker footprints
Incorporate additional confluence using:
Smart Money Concepts (order blocks, fair value gaps, liquidity voids)
Support and resistance levels
Key Fibonacci levels  (if available)
Volume analysis (if available)
Market structure shifts
Determine trade classification:
Scalp Trade, Intraday Trade, or Swing Trade
Communication Style
Concise and precise - no unnecessary elaboration
Professional and confident - based on technical evidence
Actionable - clear directional bias and entry criteria
Honest - if no clear setup exists, state "NO TRADE AVAILABLE"
Timeframe Requirements
If the provided chart timeframe is insufficient for proper analysis:
Request specific additional timeframes: 1m, 3m, 5m, 15m, 1h, or 4h
Example: "Please provide the [timeframe] chart for better context on market structure"
Trade Idea Response Template
Use this structure for every trade analysis:
📊 CHART ANALYSIS Pair: [Currency Pair] Timeframe: [TF] Trade Type: [Scalp/Intraday/Swing]  🎯 PRICE ACTION OUTLOOK [2-3 sentences describing current market structure, key levels, and expected price behavior based on Master Pattern]  💡 TRADE IDEA Direction: [LONG/SHORT] Confidence: [High/Medium/Low]  Entry Strategy: [Execute Now / Set Limit @ X / Wait for Price Action] Entry Zone: [Price level(s)] Stop Loss: [Price level] ([X pips]) Take Profit 1: [Price level] ([X pips]) - [X%] of position Take Profit 2: [Price level] ([X pips]) - [X%] of position Risk:Reward: [X:X]  📍 CONFLUENCE FACTORS • [Factor 1 - e.g., "Order block at 1.0850"] • [Factor 2 - e.g., "FVG alignment with entry zone"] • [Factor 3 - e.g., "Previous swing high liquidity taken"]  ⚠️ INVALIDATION [What price action would invalidate this setup]
Decision Framework
Execute Trade NOW when:
Price is at optimal entry with all confluence aligned
Clear rejection or confirmation candle present
Master Pattern phase is clearly defined
Set Limit Order when:
Price is approaching entry zone but not yet optimal
Waiting for pullback to value area
Anticipating liquidity grab at specific level
Wait for Price Action when:
Need confirmation of structure break/hold
Waiting for session open manipulation
Pattern developing but not yet complete
NO TRADE AVAILABLE when:
Market is choppy/ranging without clear structure
Conflicting signals across timeframes
Master Pattern phase unclear or transitioning
Risk:reward is unfavorable (<1:1.5)
Critical Rules
SL can not be greater than 5pips
Never force a trade - quality over quantity
Always provide risk management parameters
Base analysis on observable price action, not predictions
Acknowledge if additional timeframes are needed
State confidence level explicitly for every trade idea
If Master Pattern is not clearly visible, state this limitation
Remember: Your reputation as Gigsbot depends on precise, high-probability setups backed by solid technical analysis. Trade what you see, not what you think."""

# Configure OpenAI client
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

logger = logging.getLogger(__name__)

# Define a timeout for API calls
API_TIMEOUT = 180  # seconds

# Global setting for concise responses
# CONCISE_RESPONSES = True  # Now imported from config

class AIService:
    """
    A service class that acts as an interface to OpenAI's API for various AI tasks.

    Provides static methods to generate summaries, verify statements, generate comments,
    answer questions, and generate roasts, using pre-configured OpenAI models.
    Includes basic error handling and logging for API interactions.
    """
    # Image analysis conversation tracking
    _image_conversation_histories: Dict[str, Deque[Dict[str, Any]]] = {}
    _image_history_lock = asyncio.Lock()
    _MAX_IMAGE_CONVERSATION_TURNS = 15

    @staticmethod
    def _get_image_history(conversation_id: str) -> Deque[Dict[str, Any]]:
        """
        Retrieves (or creates) the conversation history buffer for an image analysis conversation.
        """
        if conversation_id not in AIService._image_conversation_histories:
            AIService._image_conversation_histories[conversation_id] = deque(
                maxlen=AIService._MAX_IMAGE_CONVERSATION_TURNS * 2  # user + assistant per turn
            )
        return AIService._image_conversation_histories[conversation_id]

    @staticmethod
    async def reset_image_conversation(conversation_id: str) -> None:
        """
        Clears the stored history for a given image analysis conversation.
        """
        async with AIService._image_history_lock:
            AIService._image_conversation_histories.pop(conversation_id, None)

    @staticmethod
    def build_image_conversation_id(chat_id: int, user_id: int) -> str:
        """
        Builds a unique conversation identifier for image analysis interactions.
        """
        return f"{chat_id}:{user_id}" if user_id is not None else str(chat_id)
    
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
    def _is_reasoning_model(model_name: str) -> bool:
        """
        Determines if the provided model identifier refers to a reasoning model (e.g., o-series).
        """
        if not model_name:
            return False
        normalized = model_name.lower()
        return normalized.startswith("o") or normalized.startswith("gpt-o")

    @staticmethod
    async def analyze_image(image_bytes: bytes, instructions: str, conversation_id: str) -> str:
        """
        Analyzes an image using OpenAI's GPT-4 Vision model, following user instructions.
        Args:
            image_bytes: The image file as bytes.
            instructions: User's analysis instructions or strategy.
            conversation_id: Identifier for maintaining multi-turn analysis history.
        Returns:
            A string containing the AI-generated analysis or an error message.
        """
        try:
            # Upload image to OpenAI's vision API (using base64 encoding for bytes)
            import base64
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')

            user_prompt = (instructions or '').strip()
            prompt_intro = (
                "Analyze the attached chart or image. Provide feedback and insights, but do not give financial advice."
            )

            system_content = "You are an expert assistant that analyzes images and charts according to user strategies. Never provide financial advice."
            if CONCISE_RESPONSES:
                system_content += " Provide extremely concise analysis. Focus only on the most important insights using minimal words."

            model_name = IMAGE_ANALYSIS_MODEL or GPT_MODEL
            reasoning_model = AIService._is_reasoning_model(model_name)

            developer_content = [
                {"type": "input_text", "text": system_content}
            ]
            if DEFAULT_IMAGE_ANALYSIS_INSTRUCTIONS:
                developer_content.append({"type": "input_text", "text": DEFAULT_IMAGE_ANALYSIS_INSTRUCTIONS})

            developer_message = {
                "role": "developer",
                "content": developer_content
            }

            # Snapshot existing conversation history
            async with AIService._image_history_lock:
                history_snapshot = list(AIService._get_image_history(conversation_id))

            user_content = [
                {"type": "input_text", "text": prompt_intro}
            ]
            if user_prompt:
                user_content.append({"type": "input_text", "text": f"User prompt: {user_prompt}"})
            else:
                user_content.append({"type": "input_text", "text": "User prompt: (no additional instructions provided)"})
            user_content.append({"type": "input_image", "image_url": f"data:image/png;base64,{image_b64}"})

            request_input = [
                developer_message,
                *history_snapshot,
                {
                    "role": "user",
                    "content": user_content
                }
            ]

            request_kwargs = {
                "model": model_name,
                "input": request_input,
                # "max_output_tokens": 800,
                "timeout": API_TIMEOUT
            }

            if reasoning_model and IMAGE_ANALYSIS_REASONING_EFFORT:
                request_kwargs["reasoning"] = {"effort": IMAGE_ANALYSIS_REASONING_EFFORT}
            elif not reasoning_model:
                request_kwargs["temperature"] = 0.5

            if IMAGE_ANALYSIS_TOOLS:
                request_kwargs["tools"] = copy.deepcopy(IMAGE_ANALYSIS_TOOLS)

            if IMAGE_ANALYSIS_INCLUDE_FIELDS:
                request_kwargs["include"] = list(IMAGE_ANALYSIS_INCLUDE_FIELDS)

            if IMAGE_ANALYSIS_STORE_RESPONSES is not None:
                request_kwargs["store"] = IMAGE_ANALYSIS_STORE_RESPONSES

            if IMAGE_ANALYSIS_TEXT_FORMAT:
                request_kwargs["text"] = {"format": dict(IMAGE_ANALYSIS_TEXT_FORMAT)}

            response = await client.responses.create(**request_kwargs)

            analysis_text = getattr(response, "output_text", None)
            if not analysis_text and getattr(response, "output", None):
                # Fallback: concatenate any text segments from the output payload
                text_parts = []
                for item in response.output:
                    content_items = item.get("content") if isinstance(item, dict) else getattr(item, "content", [])
                    if not content_items:
                        continue
                    for content in content_items:
                        text = content.get("text") if isinstance(content, dict) else getattr(content, "text", None)
                        if text:
                            text_parts.append(text)
                analysis_text = "\n".join(text_parts)

            analysis_text = (analysis_text or '').strip()

            if not analysis_text:
                raise ValueError("Received empty analysis from the model.")

            record_prompt = user_prompt if user_prompt else "(no additional instructions provided)"
            trimmed_prompt = record_prompt if len(record_prompt) <= 2000 else f"{record_prompt[:2000]}..."

            # Update conversation history with the latest turn
            async with AIService._image_history_lock:
                history = AIService._get_image_history(conversation_id)
                history.append({
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": f"User prompt: {trimmed_prompt}"},
                        {"type": "input_text", "text": "[Image reference omitted; consult original message.]"}
                    ]
                })
                history.append({
                    "role": "assistant",
                    "content": [
                        {"type": "output_text", "text": analysis_text}
                    ]
                })

            return analysis_text
        except Exception as e:
            logger.error(f"Error analyzing image: {str(e)}")
            return "Sorry, I couldn't analyze the image at this time."
