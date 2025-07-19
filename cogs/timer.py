from discord.ext import commands
import discord
import json
import os
from datetime import datetime
import pytz

TIMER_FILE = "data/voice_timer.json"

def load_timer_data():
    if not os.path.exists(TIMER_FILE):
        os.makedirs("data", exist_ok=True)
        return {}
    with open(TIMER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_timer_data(data):
    with open(TIMER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

class Timer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.timer_data = load_timer_data()

    def get_guild_data(self, guild_id: str):
        if guild_id not in self.timer_data:
            self.timer_data[guild_id] = {}
        return self.timer_data[guild_id]

    async def get_writable_channel(self, guild: discord.Guild):
        if guild.system_channel and guild.system_channel.permissions_for(guild.me).send_messages:
            return guild.system_channel
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                return channel
        return None

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.bot:
            return

        guild_id = str(member.guild.id)
        user_id = str(member.id)
        guild_data = self.get_guild_data(guild_id)
        seoul_tz = pytz.timezone('Asia/Seoul')
        now = datetime.now(seoul_tz)

        # 음성 채널 입장
        if before.channel is None and after.channel is not None:
            guild_data[user_id] = {
                "join_time": now.strftime("%Y-%m-%d %H:%M:%S")
            }
            save_timer_data(self.timer_data)

        # 음성 채널 퇴장
        elif before.channel is not None and after.channel is None:
            if user_id in guild_data:
                join_time_str = guild_data[user_id]["join_time"]
                try:
                    join_time = datetime.strptime(join_time_str, "%Y-%m-%d %H:%M:%S")
                    join_time = seoul_tz.localize(join_time)
                    leave_time = now
                    duration = leave_time - join_time
                    duration_seconds = int(duration.total_seconds())
                    hours, remainder = divmod(duration_seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)

                    # 임베드 생성
                    duration_str = f"{hours}시간 {minutes}분 {seconds}초" if hours > 0 else f"{minutes}분 {seconds}초"
                    embed = discord.Embed(
                        title=f"오늘의 음성 채널 누적 시간",
                        description=f"{now.strftime('%Y년 %m월 %d일 %H:%M')} 기준",
                        color=discord.Color.from_rgb(255, 192, 203)  # 테두리
                    )
                    embed.add_field(
                        name=f"{member.display_name} 님의 {before.channel.name} 참여 기록",
                        value=f"입장 시간: {join_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                              f"퇴장 시간: {leave_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                              f"총 참여 시간: {duration_str}",
                        inline=False
                    )

                    # 서버 텍스트 채널에 임베드 전송
                    channel = await self.get_writable_channel(member.guild)
                    if channel:
                        try:
                            await channel.send(embed=embed)
                        except discord.errors.Forbidden:
                            print(f"[Timer] Failed to send message to channel {channel.id} in guild {guild_id}")
                    else:
                        print(f"[Timer] No writable text channel found in guild {guild_id}")

                    # 기록 삭제
                    del guild_data[user_id]
                    save_timer_data(self.timer_data)
                except ValueError as e:
                    print(f"[Timer] Error processing join time for {user_id}: {e}")

async def setup(bot):
    await bot.add_cog(Timer(bot))