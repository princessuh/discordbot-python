# 봇 설정값 관리

import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = os.getenv("COMMAND_PREFIX")
BOT_NAME = os.getenv("BOT_NAME", "봇")