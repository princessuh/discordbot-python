from discord.ext import commands
import discord
from datetime import datetime
import pytz
import os
import json
from pathlib import Path

WELCOME_CHANNEL_FILE = Path("data/welcome_channel.json")
WELCOME_CHANNEL_FILE.parent.mkdir(parents=True, exist_ok=True)

if not WELCOME_CHANNEL_FILE.exists():
    WELCOME_CHANNEL_FILE.write_text(json.dumps({}))

def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.welcome_channel = load_json(WELCOME_CHANNEL_FILE)  # guild_id: channel_id

    def save_all(self):
        save_json(WELCOME_CHANNEL_FILE, self.welcome_channel)

    @commands.command()
    async def 환영인사(self, ctx):
        guild_id = str(ctx.guild.id)
        self.welcome_channel[guild_id] = str(ctx.channel.id)
        self.save_all()
        await ctx.send("해당 공간을 환영 인사 공간으로 지정하였습니다.")

    async def get_welcome_channel(self, guild: discord.Guild):
        """환영 채널 반환"""
        guild_id = str(guild.id)
        channel_id = self.welcome_channel.get(guild_id)

        if channel_id:
            channel = guild.get_channel(int(channel_id))
            if channel and isinstance(channel, discord.TextChannel):
                return channel
        return None

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot:
            return
        guild = member.guild
        seoul_tz = pytz.timezone('Asia/Seoul')
        now = datetime.now(seoul_tz)

        embed = discord.Embed(
            title="🎉 어서오세요!",
            description=f"{now.strftime('%Y년 %m월 %d일 %H:%M')}에 가입하신 {member.display_name}님 환영해요!",
            color=discord.Color.from_rgb(255, 192, 203)
        )

        channel = await self.get_welcome_channel(guild)
        if channel:
            try:
                await channel.send(embed=embed)
                print(f"[Welcome] Sent welcome message to channel {channel.id}")
            except discord.errors.Forbidden:
                print(f"[Welcome] Failed to send welcome message due to permissions in guild {guild.id}, channel {channel.id}")
            except discord.errors.HTTPException as e:
                print(f"[Welcome] HTTP error sending message in guild {guild.id}, channel {channel.id}: {e}")
            except Exception as e:
                print(f"[Welcome] Unexpected error in guild {guild.id}, channel {channel.id}: {e}")
        else:
            print(f"[Welcome] No writable welcome channel found.")
            owner = guild.owner
            if owner:
                await owner.send(f"Guild {guild.name} (ID: {guild.id})에 환영 인사 채널이 설정되지 않았습니다. `환영인사` 명령어로 채널을 지정해주세요.")


async def setup(bot):
    await bot.add_cog(Welcome(bot))
