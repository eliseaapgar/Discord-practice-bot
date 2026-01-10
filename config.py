import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Bot configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Bot settings
COMMAND_PREFIX = '!'