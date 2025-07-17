# cogs/schedule.py

from discord.ext import commands, tasks
import discord
import json
import os
from datetime import datetime, timedelta
import pytz

SCHEDULE_FILE = "data/schedules.json"

def load_schedules():
    if not os.path.exists(SCHEDULE_FILE):
        return {}
    with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_schedules(data):
    with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class Schedule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.schedules = load_schedules()
        self.notified = {}  # 알림 보낸 일정 기록
        self.schedule_notifier.start()

    def cog_unload(self):
        self.schedule_notifier.cancel()

    @commands.command(name="일정추가")
    async def add_schedule(self, ctx):
        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        await ctx.send("추가할 일정의 이름을 입력해주세요:")
        try:
            name_msg = await self.bot.wait_for("message", timeout=60.0, check=check)
        except:
            return await ctx.send("시간이 초과되었습니다. 다시 시도해주세요.")

        await ctx.send("일정 날짜와 시간을 `YYYY-MM-DD HH:MM` 형식으로 입력해주세요:")
        try:
            time_msg = await self.bot.wait_for("message", timeout=60.0, check=check)
        except:
            return await ctx.send("시간이 초과되었습니다. 다시 시도해주세요.")

        try:
            dt = datetime.strptime(time_msg.content, "%Y-%m-%d %H:%M")
            dt = dt.astimezone(pytz.timezone('Asia/Seoul'))
        except ValueError:
            return await ctx.send("날짜/시간 형식이 잘못되었어요. 다시 시도해주세요.")

        guild_id = str(ctx.guild.id)
        user_id = str(ctx.author.id)
        self.schedules.setdefault(guild_id, []).append({
            "name": name_msg.content,
            "time": dt.strftime("%Y-%m-%d %H:%M"),
            "user_id": user_id
        })
        save_schedules(self.schedules)
        await ctx.send(f"일정 `{name_msg.content}` 이(가) 추가되었어요!")

    @commands.command(name="일정삭제")
    async def delete_schedule(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.schedules or not self.schedules[guild_id]:
            return await ctx.send("삭제할 일정이 없어요!")

        await ctx.send("삭제할 일정의 이름을 입력해주세요:")

        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        try:
            msg = await self.bot.wait_for("message", timeout=60.0, check=check)
        except:
            return await ctx.send("시간이 초과되었습니다.")

        old_count = len(self.schedules[guild_id])
        self.schedules[guild_id] = [
            s for s in self.schedules[guild_id] if s["name"] != msg.content
        ]
        if len(self.schedules[guild_id]) == old_count:
            return await ctx.send("해당 이름의 일정을 찾지 못했어요.")
        else:
            save_schedules(self.schedules)
            return await ctx.send(f"일정 `{msg.content}` 이(가) 삭제되었어요.")

    @commands.command(name="일정조회")
    async def show_schedules(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.schedules or not self.schedules[guild_id]:
            return await ctx.send("저장된 일정이 없어요!")

        embed = discord.Embed(title=f"{ctx.guild.name}의 일정 목록", color=discord.Color.green())
        for s in self.schedules[guild_id]:
            embed.add_field(name=s["name"], value=s["time"], inline=False)
        await ctx.send(embed=embed)

    @tasks.loop(seconds=10.0)
    async def schedule_notifier(self):
        now = datetime.now(pytz.timezone('Asia/Seoul'))
        for guild_id, schedule_list in self.schedules.items():
            for item in schedule_list:
                name = item["name"]
                user_id = item["user_id"]
                time_str = item["time"]
                schedule_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
                schedule_time = pytz.timezone('Asia/Seoul').localize(schedule_time)

                key = f"{guild_id}-{user_id}-{name}-{time_str}"
                if key in self.notified:
                    continue

                # 10분 전 조건
                if 0 <= (schedule_time - now).total_seconds() <= 600:
                    try:
                        user = await self.bot.fetch_user(int(user_id))
                        await user.send(f"`{name}` 일정이 10분 뒤 시작 돼요!")
                        self.notified[key] = True
                    except Exception as e:
                        print(f"[알림 오류] {e}")


async def setup(bot):
    await bot.add_cog(Schedule(bot))
