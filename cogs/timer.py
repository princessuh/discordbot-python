from discord.ext import commands
import discord
from datetime import datetime
import pytz
import json
import os
from pathlib import Path

TIMER_CHANNEL_FILE = Path("data/timer_channel.json")
TIMER_DATA_FILE = Path("data/timer_data.json")
TIMER_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

if not TIMER_DATA_FILE.exists():
    TIMER_DATA_FILE.write_text(json.dumps({}))

def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

class Timer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.timer_channel = load_json(TIMER_CHANNEL_FILE)
        self.timer_data = load_json(TIMER_DATA_FILE)

    def get_guild_data(self, guild_id: str):
        if guild_id not in self.timer_data:
            self.timer_data[guild_id] = {}
        return self.timer_data[guild_id]

    def save_all(self):
        save_json(TIMER_CHANNEL_FILE, self.timer_channel)
        save_json(TIMER_DATA_FILE, self.timer_data)

    @commands.command(name="타이머")
    async def set_timer_channel(self, ctx):
        """현재 채널을 타이머 채널로 설정"""
        guild_id = str(ctx.guild.id)
        self.timer_channel[guild_id] = ctx.channel.id
        self.save_all()
        await ctx.send("해당 공간을 타이머 기록 공간으로 지정하였습니다.")

    async def get_timer_channel(self, guild: discord.Guild):
        """타이머 채널 반환"""
        guild_id = str(guild.id)
        channel_id = self.timer_channel.get(guild_id)

        if channel_id:
            channel = guild.get_channel(channel_id)
            if channel and isinstance(channel, discord.TextChannel):
                return channel
        return None

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.bot:
            return

        guild = member.guild
        guild_id = str(guild.id)
        user_id = str(member.id)
        guild_data = self.get_guild_data(guild_id)

        seoul_tz = pytz.timezone("Asia/Seoul")
        now = datetime.now(seoul_tz)

        # 입장
        if before.channel is None and after.channel is not None:
            guild_data[user_id] = {
                "join_time": now.strftime("%Y-%m-%d %H:%M:%S")
            }
            self.save_all()

        # 퇴장
        elif before.channel is not None and after.channel is None:
            if user_id in guild_data:
                try:
                    join_time = datetime.strptime(guild_data[user_id]["join_time"], "%Y-%m-%d %H:%M:%S")
                    join_time = seoul_tz.localize(join_time)
                    leave_time = now
                    duration = leave_time - join_time
                    total_seconds = int(duration.total_seconds())
                    h, rem = divmod(total_seconds, 3600)
                    m, s = divmod(rem, 60)
                    duration_str = f"{h}시간 {m}분 {s}초" if h > 0 else f"{m}분 {s}초"

                    embed = discord.Embed(
                        title=f"음성 채널 참여 기록",
                        description=f"{now.strftime('%Y년 %m월 %d일 %H:%M')} 기준",
                        color=discord.Color.from_rgb(255, 192, 203)
                    )
                    embed.add_field(
                        name=f"{member.display_name} 님의 {before.channel.name} 참여 기록",
                        value=(
                            f"입장 시간: {join_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                            f"퇴장 시간: {leave_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                            f"총 참여 시간: {duration_str}"
                        ),
                        inline=False
                    )

                    channel = await self.get_timer_channel(guild)

                    if channel:
                        await channel.send(embed=embed)
                    else:
                        # 시스템 채널 fallback
                        if guild.system_channel:
                            try:
                                await guild.system_channel.send(
                                    f"타이머 채널이 설정되어 있지 않아 {member.display_name} 님의 기록을 저장하지 못했어요.\n"
                                    f"`타이머` 명령어로 채널을 지정해주세요."
                                )
                            except discord.Forbidden:
                                print(f"[Timer] 시스템 채널에 메시지 전송 실패: 권한 부족")
                            except Exception as e:
                                print(f"[Timer] 시스템 채널 전송 오류: {e}")

                        # 관리자에게 DM
                        if guild.owner:
                            try:
                                await guild.owner.send(
                                    f"서버 **{guild.name}** (ID: {guild.id})에서 타이머 기록 채널이 설정되지 않아\n"
                                    f"{member.display_name} 님의 음성 참여 기록을 저장하지 못했어요.\n"
                                    f"`타이머` 명령어로 기록할 채널을 설정해주세요."
                                )
                            except discord.Forbidden:
                                print(f"[Timer] 서버 관리자 DM 전송 실패: 차단 또는 DM 비허용")
                            except Exception as e:
                                print(f"[Timer] 관리자 DM 전송 오류: {e}")

                    del guild_data[user_id]
                    self.save_all()

                except ValueError as e:
                    print(f"[Timer] 시간 파싱 오류: {e}")

async def setup(bot):
    await bot.add_cog(Timer(bot))
