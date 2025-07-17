import discord
from discord.ext import commands
import asyncio
from discord.ext import commands
from config import TOKEN, PREFIX


intents = discord.Intents.default()
intents.message_content = True  # 이 줄이 있으면 포털에서 메시지 권한 허용해야 함

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

initial_extensions = ["cogs.basic",
                      "cogs.help",
                      "cogs.savelist",
                      "cogs.schedule",
                      "cogs.points",
                      "cogs.attendance",
                      "cogs.dice_gamble"]

async def main():
    async with bot:
        for extension in initial_extensions:
            await bot.load_extension(extension)
        await bot.start(TOKEN)

asyncio.run(main())
