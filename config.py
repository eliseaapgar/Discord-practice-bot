import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Bot configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# Bot settings
COMMAND_PREFIX = '!'