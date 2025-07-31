import os
from dotenv import load_dotenv

# Load environment variables from .env file at the very beginning
load_dotenv()

class Config:
    def __init__(self):
        self.ai = self.AI()

    class AI:
        def __init__(self):
            # The API key is now loaded from the environment
            self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
            self.anthropic_model = "claude-3-5-sonnet-20241022"

# Instantiate the config
config = Config()
