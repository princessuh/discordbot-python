from discord.ext import commands
import discord
from datetime import datetime
import pytz
import config
import asyncio

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.welcome_channels = {}  # guild_id: welcome_channel_id

    async def get_welcome_channel(self, guild: discord.Guild):
        guild_id = str(guild.id)
        print(f"[Welcome] Checking welcome channel for guild {guild_id}")

        try:
            # 3초 타임아웃 적용
            async with asyncio.timeout(3):
                # 우선 지정된 환영 채널 확인
                if guild_id in self.welcome_channels:
                    channel_id = self.welcome_channels[guild_id]
                    channel = guild.get_channel(int(channel_id))
                    print(f"[Welcome] Checking specified welcome channel {channel_id}")
                    if channel and channel.permissions_for(guild.me).send_messages and channel.permissions_for(guild.me).embed_links:
                        print(f"[Welcome] Using specified welcome channel: {channel.id}")
                        return channel
                    else:
                        print(f"[Welcome] Specified welcome channel {channel_id} not accessible or lacks permissions")
                        del self.welcome_channels[guild_id]  # 권한 없으면 제거

                # 임시 백업: 시스템 채널 또는 첫 번째 텍스트 채널
                if guild.system_channel and guild.system_channel.permissions_for(guild.me).send_messages and guild.system_channel.permissions_for(guild.me).embed_links:
                    print(f"[Welcome] Using system channel as fallback: {guild.system_channel.id}")
                    return guild.system_channel
                for channel in guild.text_channels:
                    if channel.permissions_for(guild.me).send_messages and channel.permissions_for(guild.me).embed_links:
                        print(f"[Welcome] Using first available text channel as fallback: {channel.id}")
                        return channel
        except asyncio.TimeoutError:
            print(f"[Welcome] Channel search timed out after 3 seconds for guild {guild_id}, using fallback")
            # 타임아웃 발생 시 시스템 채널 또는 첫 번째 텍스트 채널 사용
            if guild.system_channel and guild.system_channel.permissions_for(guild.me).send_messages and guild.system_channel.permissions_for(guild.me).embed_links:
                print(f"[Welcome] Using system channel as timeout fallback: {guild.system_channel.id}")
                return guild.system_channel
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages and channel.permissions_for(guild.me).embed_links:
                    print(f"[Welcome] Using first available text channel as timeout fallback: {channel.id}")
                    return channel

        print(f"[Welcome] No writable welcome channel found in guild {guild.id}")
        return None

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        guild_id = str(message.guild.id) if message.guild else None
        if guild_id:
            print(f"[Welcome] Updated message channel for guild {guild_id} to {message.channel.id}")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot:
            return
        print(f"[Welcome] Member joined: {member.display_name} in guild {member.guild.id}")
        guild = member.guild
        seoul_tz = pytz.timezone('Asia/Seoul')
        now = datetime.now(seoul_tz)

        embed = discord.Embed(
            title="🎉 어서오세요!",
            description=f"{now.strftime('%Y년 %m월 %d일 %H:%M')}에 가입하신 {member.display_name}님 환영해요!",
            color=discord.Color.from_rgb(255, 192, 203)
        )

        channel = await self.get_welcome_channel(guild)
        print(f"[Welcome] Selected channel: {channel.id if channel else 'None'}")
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
            print(f"[Welcome] No writable welcome channel found, notifying guild owner")
            owner = guild.owner
            if owner:
                await owner.send(f"Guild {guild.name} (ID: {guild.id}) has no writable welcome channel configured. Please use !환영인사 to set one.")

    @commands.command()
    async def 환영인사(self, ctx):
        guild = ctx.guild
        guild_id = str(guild.id)
        self.welcome_channels[guild_id] = str(ctx.channel.id)
        print(f"[Welcome] Set welcome channel for guild {guild_id} to {ctx.channel.id}")
        await ctx.send("해당 공간을 환영 인사 공간으로 지정하였습니다.")

async def setup(bot):
    await bot.add_cog(Welcome(bot))