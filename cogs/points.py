from discord.ext import commands
import discord
import json
import os
from pathlib import Path

POINTS_FILE = Path("../data/points.json")
POINTS_FILE.parent.mkdir(parents=True, exist_ok=True)

if not POINTS_FILE.exists():
    POINTS_FILE.write_text(json.dumps({}))


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

    def subtract_points(self, user_id: str, guild_id: str, amount: int) -> bool:
        if self.get_points(user_id, guild_id) >= amount:
            self.points[guild_id][user_id] -= amount
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

    @commands.command(name="양도")
    async def transfer_points(self, ctx):
        await ctx.send("포인트를 양도할 대상을 멘션해주세요.")

        def check_mention(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.mentions

        try:
            mention_msg = await self.bot.wait_for("message", check=check_mention, timeout=30.0)
            target_user = mention_msg.mentions[0]
        except Exception:
            await ctx.send("제대로 된 유저 멘션을 받지 못했어요. 다시 시도해주세요.")
            return

        if target_user.id == ctx.author.id:
            await ctx.send("자기 자신에게는 포인트를 양도할 수 없어요!")
            return

        await ctx.send("양도할 포인트 양을 숫자로 입력해주세요.")

        def check_amount(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit()

        try:
            amount_msg = await self.bot.wait_for("message", check=check_amount, timeout=30.0)
            amount = int(amount_msg.content)
        except Exception:
            await ctx.send("숫자를 제대로 입력하지 않으셨어요. 다시 시도해주세요.")
            return

        sender_id = str(ctx.author.id)
        receiver_id = str(target_user.id)
        guild_id = str(ctx.guild.id)

        if self.get_points(sender_id, guild_id) < amount:
            await ctx.send("포인트가 부족해요!")
            return

        # 양도 실행
        self.subtract_points(sender_id, guild_id, amount)
        self.add_points(receiver_id, guild_id, amount)
        save_points(self.points)

        await ctx.send(f"{ctx.author.mention}님이 {target_user.mention}님에게 {amount}P를 양도하셨어요!")


async def setup(bot):
    await bot.add_cog(Points(bot))
