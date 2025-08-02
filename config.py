import os
from dotenv import load_dotenv

# Load environment variables from .env file at the very beginning
load_dotenv()

class Config:
    def __init__(self):
        self.ai = self.AI()
        self.api = self.API()
        self.logging = self.Logging()
        self.upload = self.Upload()

    class AI:
        def __init__(self):
            # The API key is now loaded from the environment
            self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
            self.anthropic_model = "claude-3-5-sonnet-20241022"

    class API:
        def __init__(self):
            self.host = "0.0.0.0"
            self.port = 8000
            self.cors_origins = ["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"]

    class Logging:
        def __init__(self):
            self.level = "DEBUG"  # Enable verbose logging
            self.format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    class Upload:
        def __init__(self):
            self.allowed_extensions = ['.pdf', '.docx', '.csv', '.txt']
            self.allowed_mime_types = [
                'application/pdf',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'text/csv',
                'text/plain'
            ]
            self.max_file_size_mb = 200

# Instantiate the config
config = Config()
