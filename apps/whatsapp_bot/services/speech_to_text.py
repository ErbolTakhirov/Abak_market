# ==============================================
# SPEECH-TO-TEXT SERVICE
# ==============================================
"""
Speech-to-text service for processing voice messages.
Supports Google Cloud Speech and OpenAI Whisper.
"""

import os
import tempfile
import logging
from typing import Optional
from django.conf import settings
from apps.core.exceptions import SpeechRecognitionError

logger = logging.getLogger(__name__)


class SpeechToTextService:
    """
    Speech-to-text service with multiple backend support.
    """
    

    def __init__(self, backend: str = None):
        """
        Initialize service with specified backend.
        
        Args:
            backend: 'google', 'openai', or 'local'. Defaults to settings.STT_BACKEND.
        """
        self.backend = backend or settings.STT_BACKEND
    
    def transcribe(self, audio_data: bytes, language: str = 'ru-RU') -> str:
        """
        Transcribe audio to text.
        
        Args:
            audio_data: Raw audio bytes
            language: Language code
        
        Returns:
            Transcribed text
        """
        if self.backend == 'openai':
            return self._transcribe_openai(audio_data)
        elif self.backend == 'local':
            return self._transcribe_local(audio_data)
        else:
            return self._transcribe_google(audio_data, language)
    
    def _transcribe_google(self, audio_data: bytes, language: str) -> str:
        """
        Transcribe using Google Cloud Speech-to-Text.
        """
        try:
            from google.cloud import speech
            
            client = speech.SpeechClient()
            
            # WhatsApp uses OGG/Opus format
            audio = speech.RecognitionAudio(content=audio_data)
            
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
                sample_rate_hertz=16000,
                language_code=language,
                enable_automatic_punctuation=True,
                model='default',
                audio_channel_count=1,
            )
            
            response = client.recognize(config=config, audio=audio)
            
            # Extract transcription
            transcript = ''
            for result in response.results:
                transcript += result.alternatives[0].transcript + ' '
            
            transcript = transcript.strip()
            logger.info(f"Google STT transcription: {transcript[:100]}...")
            
            return transcript
            
        except Exception as e:
            logger.error(f"Google STT error: {e}")
            raise SpeechRecognitionError(f"Google transcription failed: {e}", e)
    
    def _transcribe_openai(self, audio_data: bytes) -> str:
        """
        Transcribe using OpenAI Whisper API.
        """
        try:
            import openai
            
            client = openai.OpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url="https://api.openai.com/v1" # Explicitly use OpenAI for Whisper unless changed
            )
            
            # Save to temporary file (Whisper API requires file)
            with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as f:
                f.write(audio_data)
                temp_path = f.name
            
            try:
                with open(temp_path, 'rb') as audio_file:
                    response = client.audio.transcriptions.create(
                        model='whisper-1',
                        file=audio_file,
                        language='ru',
                        response_format='text'
                    )
                
                transcript = str(response).strip() 
                logger.info(f"OpenAI Whisper transcription: {transcript[:100]}...")
                
                return transcript
                
            finally:
                # Cleanup temp file
                os.unlink(temp_path)
            
        except Exception as e:
            logger.error(f"OpenAI Whisper error: {e}")
            raise SpeechRecognitionError(f"OpenAI transcription failed: {e}", e)

    def _transcribe_local(self, audio_data: bytes) -> str:
        """
        Transcribe using local Whisper model.
        """
        try:
            import whisper
            import torch
            
            model_name = getattr(settings, 'WHISPER_MODEL', 'base')
            logger.info(f"Loading local Whisper model: {model_name}")
            
            # Check for GPU
            device = "cuda" if torch.cuda.is_available() else "cpu"
            model = whisper.load_model(model_name, device=device)
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as f:
                f.write(audio_data)
                temp_path = f.name
            
            try:
                # Transcribe
                result = model.transcribe(temp_path, language='ru')
                transcript = result['text'].strip()
                
                logger.info(f"Local Whisper transcription: {transcript[:100]}...")
                return transcript
                
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except ImportError:
            error_msg = "openai-whisper library is not installed. Please run: pip install openai-whisper"
            logger.error(error_msg)
            raise SpeechRecognitionError(error_msg)
        except Exception as e:
            logger.error(f"Local Whisper error: {e}")
            raise SpeechRecognitionError(f"Local transcription failed: {e}", e)
    
    def analyze_intent(self, text: str) -> dict:
        """
        Analyze transcribed text to detect intent.
        
        Returns:
            dict with 'intent' and 'confidence' keys
        """
        from apps.core.utils import parse_menu_command
        
        text_lower = text.lower()
        
        # Check for known commands
        command = parse_menu_command(text)
        if command:
            return {
                'intent': command,
                'confidence': 0.9,
                'requires_operator': False
            }
        
        # Check for order-related keywords
        order_keywords = ['заказ', 'купить', 'хочу', 'доставка', 'заказать']
        if any(kw in text_lower for kw in order_keywords):
            return {
                'intent': 'order',
                'confidence': 0.7,
                'requires_operator': True
            }
        
        # Check for question keywords
        question_keywords = ['сколько', 'когда', 'где', 'как', 'почему', 'что']
        if any(kw in text_lower for kw in question_keywords):
            return {
                'intent': 'question',
                'confidence': 0.6,
                'requires_operator': True
            }
        
        # Default: needs operator attention
        return {
            'intent': 'unknown',
            'confidence': 0.3,
            'requires_operator': True
        }
