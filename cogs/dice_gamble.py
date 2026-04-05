from discord.ext import commands
import discord
import random
from cogs.points import Points
from config import BOT_NAME
import asyncio

class DiceGamble(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.points: Points = None
        self.loss_streak: dict = {}

    @commands.command(name="주사위")
    async def dice(self, ctx):
        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)
        key = (user_id, guild_id)

        if self.points is None:
            await ctx.send("🚨 포인트 시스템에 연결되어 있지 않습니다.")
            return

        await ctx.send(f"{ctx.author.mention} 씨~ 몇 포인트 거시겠어요? 아참, **숫자**로만 알려주세요!")

        def check(m):
            return (
                m.author == ctx.author
                and m.channel == ctx.channel
                and m.content.isdigit()
            )

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=20)
            amount = int(msg.content)
        except asyncio.TimeoutError:
            await ctx.send("음? 마음이 바뀌셨나? 그럼 나중에 또 봐요~")
            return

        if amount <= 0:
            await ctx.send("에이, 1포인트라도 걸어야 재미가 있지 않겠어요? 다시 시도해 주세요!")
            return

        user_points = self.points.get_points(user_id, guild_id)
        if user_points < amount:
            await ctx.send(f"{ctx.author.mention} 씨, 포인트가 부족하신데요?\n참고로 현재 보유하신 포인트는 {user_points}P예요~")
            return

        user_roll = random.randint(1, 6)
        bot_roll = random.randint(1, 6)

        result = (
            f"{ctx.author.display_name}의 주사위: {user_roll}\n"
            f"{BOT_NAME}의 주사위: {bot_roll}\n"
        )

        if user_roll > bot_roll:
            winnings = amount * 2
            self.points.add_points(user_id, guild_id, winnings)
            result += f"오! 축하드려요~ 약속드린 {winnings}P 입니다~"
            # 승리 또는 무승부 시 연속 패배 기록 초기화
            self.loss_streak.pop(key, None)

        elif user_roll < bot_roll:
            self.points.subtract_points(user_id, guild_id, amount)
            result += f"이런, 이번엔 제가 이겼네요! {amount}P는 제가 잘 받아가겠습니다~"

            # 연속 패배 기록 갱신
            if key not in self.loss_streak:
                self.loss_streak[key] = {"streak": 0, "bets": []}
            self.loss_streak[key]["streak"] += 1
            self.loss_streak[key]["bets"].append(amount)

            # 3연패 달성 시
            if self.loss_streak[key]["streak"] >= 3:
                recent_bets = self.loss_streak[key]["bets"][-3:]  # 최근 3판 베팅액
                consolation = sum(recent_bets) // len(recent_bets)  # 평균 (정수)
                self.points.add_points(user_id, guild_id, consolation)
                result += f"\n\n**[특별 구제!]**\n3연속 패배는 조금 그렇긴 하죠? 자, 여기! {consolation}P 돌려드릴게요~"
                # 초기화
                self.loss_streak.pop(key, None)

        else:
            result += "오, 똑같은 숫자! 이건 저희가 운명이란 뜻일까요? 하하, 농담이에요! 이번 판은 무승부~"
            # 무승부는 연속 패배 기록 초기화
            self.loss_streak.pop(key, None)

        await ctx.send(result)

    async def cog_load(self):
        points_cog = self.bot.get_cog("Points")
        if isinstance(points_cog, Points):
            self.points = points_cog

async def setup(bot):
    cog = DiceGamble(bot)
    await bot.add_cog(cog)