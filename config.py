"""
Configuration module for the Langfuse example server
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Langfuse configuration
    LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
    LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
    LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    # OpenAI configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # Server configuration
    SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT = int(os.getenv("SERVER_PORT", 8000))

    # Application settings
    APP_NAME = "Langfuse Example Server"
    API_VERSION = "v1"
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

    @classmethod
    def validate(cls):
        """Validate required configuration"""
        errors = []

        if not cls.LANGFUSE_SECRET_KEY:
            errors.append("LANGFUSE_SECRET_KEY is required")
        if not cls.LANGFUSE_PUBLIC_KEY:
            errors.append("LANGFUSE_PUBLIC_KEY is required")
        if not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required")

        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")

        return True

config = Config()