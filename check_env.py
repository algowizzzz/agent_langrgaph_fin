import os
from dotenv import load_dotenv

# This is the most critical step. We force it to load variables from .env
# and override any variables that might already be in the system environment.
print("--- Running Environment Check ---")
print("Attempting to load variables from .env file with override...")
loaded = load_dotenv(override=True, verbose=True)

if loaded:
    print("✅ '.env' file loaded successfully.")
else:
    print("⚠️ '.env' file not found or could not be loaded.")

# Now, we check the environment directly to see what key is present
api_key = os.getenv("OPENAI_API_KEY")

if api_key:
    print(f"✅ OpenAI API Key FOUND in the environment.")
    print(f"   The key ends in: '...{api_key[-4:]}'")
else:
    print("❌ Critical Error: OpenAI API Key NOT FOUND in the environment after loading.")

print("--- Check Complete ---")
