import discord
from discord.ext import commands
import asyncio
from config import TOKEN, PREFIX
from aiohttp import web
import aiohttp
import os

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

initial_extensions = [
    "cogs.basic",
    "cogs.help",
    "cogs.savelist",
    "cogs.schedule",
    "cogs.points",
    "cogs.attendance",
    "cogs.dice_gamble"
]

# Health Check API
async def health_check(request):
    return web.Response(text="OK", status=200)

async def start_web_server():
    app = web.Application()
    app.router.add_get('/health', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8000)
    await site.start()

# Self Ping
async def ping_self():
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            async with aiohttp.ClientSession() as session:
                await session.get(os.environ["KOYEP_URL"])
        except:
            pass
        await asyncio.sleep(180)

# on_ready 이벤트
@bot.event
async def on_ready():
    print("✅ Bot Started")
    print("✅ on_ready() fired")
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Game("애인 생각 중")
    )
    bot.loop.create_task(start_web_server())
    bot.loop.create_task(ping_self())

# 메인 함수
async def main():
    async with bot:
        for extension in initial_extensions:
            await bot.load_extension(extension)
        await bot.start(TOKEN)

asyncio.run(main())