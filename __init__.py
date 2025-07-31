from dotenv import load_dotenv

# This code will run automatically when the package is imported.
# It ensures that the .env file is loaded at the very beginning of the application's lifecycle.
print("--- Loading environment variables from .env file ---")
load_dotenv()
