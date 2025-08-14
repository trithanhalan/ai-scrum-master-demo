# This file is kept for backward compatibility
# The main OpenAI service is now in openai_client.py

from .openai_client import openai_service, summarize_list

__all__ = ["openai_service", "summarize_list"]