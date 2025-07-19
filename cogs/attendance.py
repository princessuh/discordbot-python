from discord.ext import commands
import discord
import json
import os
import random
from datetime import datetime
import pytz
from pathlib import Path

ATTENDANCE_FILE = Path("data/attendance.json")
ATTENDANCE_FILE.parent.mkdir(parents=True, exist_ok=True)

if not ATTENDANCE_FILE.exists():
    ATTENDANCE_FILE.write_text(json.dumps({}))

def load_attendance():
    if not os.path.exists(ATTENDANCE_FILE):
        return {}
    with open(ATTENDANCE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_attendance(data):
    with open(ATTENDANCE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

class Attendance(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.attendance_data = load_attendance()
        self.points = None  # Points Cog는 setup에서 연결

    @commands.command(name="출석")
    async def check_in(self, ctx):
        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)
        today = datetime.now(pytz.timezone('Asia/Seoul')).strftime("%Y-%m-%d")

        if guild_id not in self.attendance_data:
            self.attendance_data[guild_id] = {}

        user_data = self.attendance_data[guild_id].setdefault(user_id, {
            "last_check": "",
            "count": 0
        })

        if user_data["last_check"] == today:
            await ctx.send(f"{ctx.author.mention} 오늘은 이미 출석하셨잖아요~ 저 다 기억하고 있어요! 내일 또 와주실 거죠?")
            return

        # 출석 처리
        user_data["last_check"] = today
        user_data["count"] += 1
        save_attendance(self.attendance_data)

        reward = random.randint(20, 200)
        bonus_msg = ""

        if self.points:
            self.points.add_points(user_id, guild_id, reward)

        # 누적 7일마다 보너스
        if user_data["count"] % 7 == 0:
            bonus = 300
            if self.points:
                self.points.add_points(user_id, guild_id, bonus)
            bonus_msg = f"\n🎉 누적 출석 {user_data['count']}일 보너스 +{bonus}P!"

        await ctx.send(
            f"{ctx.author.mention} 출석 완료! {reward}P를 획득했어요.\n"
            f"누적 출석: {user_data['count']}일{bonus_msg}"
        )

    @commands.command(name="출석통계")
    async def stats(self, ctx):
        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)

        count = self.attendance_data.get(guild_id, {}).get(user_id, {}).get("count", 0)
        await ctx.send(f"{ctx.author.mention}님은... 지금까지 {count}일 출석하셨네요! 멋져요~")

    @commands.command(name="출석랭킹")
    async def attendance_rank(self, ctx):
        guild_id = str(ctx.guild.id)
        server_data = self.attendance_data.get(guild_id, {})

        if not server_data:
            await ctx.send("아직 아무도 출석하지 않았어요!")
            return

        sorted_data = sorted(server_data.items(), key=lambda x: x[1]["count"], reverse=True)
        lines = []
        for rank, (user_id, data) in enumerate(sorted_data[:3], start=1):
            user = await self.bot.fetch_user(int(user_id))
            lines.append(f"{rank}. {user.name} — {data['count']}일")

        msg = f"**{ctx.guild.name} 서버 출석 랭킹 TOP 3**\n" + "\n".join(lines)
        await ctx.send(msg)

async def setup(bot):
    cog = Attendance(bot)

    # Points Cog 연결
    for c in bot.cogs.values():
        if c.__class__.__name__ == "Points":
            cog.points = c
            break

    if cog.points is None:
        print("⚠️ [Attendance] Points Cog를 찾을 수 없습니다. 출석 포인트 지급이 비활성화됩니다.")

    await bot.add_cog(cog)
