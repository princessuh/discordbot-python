from discord.ext import commands
import discord
import json
import os

POINTS_FILE = "data/points.json"


def load_points():
    if not os.path.exists(POINTS_FILE):
        return {}
    with open(POINTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_points(points):
    with open(POINTS_FILE, "w", encoding="utf-8") as f:
        json.dump(points, f, ensure_ascii=False, indent=2)


class Points(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.points = load_points()

    def add_points(self, user_id: str, guild_id: str, amount: int):
        if guild_id not in self.points:
            self.points[guild_id] = {}

        if user_id not in self.points[guild_id]:
            self.points[guild_id][user_id] = 1000  # 기본 포인트

        self.points[guild_id][user_id] += amount
        save_points(self.points)

    def subtract_points(self, user_id: str, guild_id: str, amount: int) -> bool:
        if self.get_points(user_id, guild_id) >= amount:
            self.points[guild_id][user_id] -= amount
            save_points(self.points)
            return True
        return False

    def get_points(self, user_id: str, guild_id: str) -> int:
        if guild_id not in self.points:
            self.points[guild_id] = {}

        if user_id not in self.points[guild_id]:
            self.points[guild_id][user_id] = 1000
            save_points(self.points)

        return self.points[guild_id][user_id]

    @commands.command(name="포인트")
    async def check_points(self, ctx):
        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)
        point = self.get_points(user_id, guild_id)
        await ctx.send(f"{ctx.author.mention}님의 현재 포인트는 {point}P입니다!")

    @commands.command(name="포인트랭킹")
    async def ranking(self, ctx):
        guild_id = str(ctx.guild.id)

        if guild_id not in self.points or not self.points[guild_id]:
            await ctx.send("아직 아무도 포인트를 모으지 않았어요!")
            return

        sorted_points = sorted(self.points[guild_id].items(), key=lambda x: x[1], reverse=True)
        lines = []
        for rank, (user_id, point) in enumerate(sorted_points[:3], start=1):
            user = await self.bot.fetch_user(int(user_id))
            lines.append(f"{rank}. {user.name} — {point}P")

        msg = f"**{ctx.guild.name} 서버 포인트 랭킹 TOP 3**\n" + "\n".join(lines)
        await ctx.send(msg)


async def setup(bot):
    await bot.add_cog(Points(bot))
