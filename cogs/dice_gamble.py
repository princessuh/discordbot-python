from discord.ext import commands
import discord
import random
from cogs.points import Points
from config import BOT_NAME


class DiceGamble(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.points: Points = None  # Points Cog는 setup에서 연결

    @commands.command(name="주사위")
    async def dice(self, ctx):
        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)

        if self.points is None:
            await ctx.send("❌ 포인트 시스템에 연결되어 있지 않아요.")
            return

        await ctx.send(f"{ctx.author.mention}, 몇 포인트를 거시겠어요? (숫자로만 입력해주세요)")

        def check(m):
            return (
                m.author == ctx.author
                and m.channel == ctx.channel
                and m.content.isdigit()
            )

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=20)
            amount = int(msg.content)
        except TimeoutError:
            await ctx.send("⏰ 시간이 초과되어 도박을 취소했어요!")
            return

        if amount <= 0:
            await ctx.send("1P 이상을 입력해주세요!")
            return

        user_points = self.points.get_points(user_id, guild_id)
        if user_points < amount:
            await ctx.send(f"{ctx.author.mention} 포인트가 부족해요. 현재 보유 포인트: {user_points}P")
            return

        # 주사위 게임 시작
        user_roll = random.randint(1, 6)
        bot_roll = random.randint(1, 6)

        result = (
            f"🎲 {ctx.author.display_name}의 주사위: {user_roll}\n"
            f"🎲 {BOT_NAME}의 주사위: {bot_roll}\n"
        )

        if user_roll > bot_roll:
            winnings = amount * 2
            self.points.add_points(user_id, guild_id, winnings)
            result += f"🎉 이겼어요! {winnings}P 획득!"
        elif user_roll < bot_roll:
            self.points.subtract_points(user_id, guild_id, amount)
            result += f"😭 졌어요... {amount}P 잃었어요."
        else:
            result += "😮 비겼어요! 포인트는 그대로예요."

        await ctx.send(result)

    async def cog_load(self):
        # 봇 cog들 중 Points Cog 자동 연결
        points_cog = self.bot.get_cog("Points")
        if isinstance(points_cog, Points):
            self.points = points_cog


async def setup(bot):
    cog = DiceGamble(bot)
    await bot.add_cog(cog)
