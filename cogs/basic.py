from discord.ext import commands
import discord
from datetime import datetime, time
import pytz


class Basic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def 반가워(self, ctx):
        await ctx.send("안녕하세요! 제이드라고 해요. 잘 부탁드려요~")

    @commands.command()
    async def 안녕(self, ctx):
        now = datetime.now(pytz.timezone('Asia/Seoul')).time()
        if time(0, 30) <= now < time(6, 30):
            greeting = "좋은 새벽이에요! 피곤하진 않으세요?"
        elif time(6, 30) <= now < time(12, 0):
            greeting = "좋은 아침이에요~ 잘 잤나요? 오늘도 힘내봐요, 우리!"
        elif time(12, 0) <= now < time(14, 0):
            greeting = "좋은 오후예요. 식사는 하셨어요?"
        elif time(14, 0) <= now < time(18, 0):
            greeting = "좋은 오후! 슬슬 쉴 수 있겠네요~ 저는 이따 요셉이랑 데이트 하려고요!"
        elif time(18, 0) <= now < time(20, 0):
            greeting = "좋은 저녁이에요! 얼른 쉬어야겠어요."
        else:
            greeting = "좋은 밤이에요. 시간이 정말 빠르네요~ 그렇죠? 오늘도 좋은 하루 보냈길 바랄게요."

        await ctx.send(f"안녕하세요! {greeting}")

    @commands.command()
    async def 사랑해(self, ctx):
        await ctx.send("앗, 감사해요~ 그런데 저는 사랑하는 사람이 따로 있어서요! 마음만 받을게요.")

    @commands.command()
    async def 고마워(self, ctx):
        await ctx.send("이정도로 뭘요! 도움이 됐다면 다행이에요.")

    @commands.command()
    async def 심심해(self, ctx):
        await ctx.send("그럼 저랑 놀면 되겠네요! 뭐하고 놀까요? 주사위 놀이?")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        content = message.content.lower().strip()

        if not content.startswith("제이드"):
            await self.bot.process_commands(message)
            return

        after_name = content[len("제이드"):].strip()

        goodnight_phrases = ["잘자", "잘 자", "잘자요", "잘 자요"]
        if any(phrase in after_name for phrase in goodnight_phrases):
            await message.channel.send("주무시려고요? 푹 자고 내일 만나요!")
            return

        mood_phrases = ["기분 어때", "기분이 어때", "기분어때", "기분"]
        if any(p in after_name for p in mood_phrases):
            await message.channel.send("제 기분이요? 좋죠~ 이렇게 누군가와 대화하는 건 늘 재밌거든요.")
            return

        time_phrases = ["몇시야", "몇 시야", "몇 시니", "몇 시인지 알아", "지금 몇 시", "현재 시간"]
        if any(p in after_name for p in time_phrases):
            now = datetime.now(pytz.timezone('Asia/Seoul'))
            hour = now.strftime("%I")
            minute = now.strftime("%M")
            period = "오전" if now.hour < 12 else "오후"
            await message.channel.send(f"지금은 {period} {hour}시 {minute}분이에요!")
            return

        doing = ["뭐해", "뭐해?", "뭐하니", "뭐 해", "뭐 하니", "뭐하고 있어?"]
        if any(p in after_name for p in doing):
            await message.channel.send("저요? 귀여운 애인 생각하고 있었죠!")
            return

async def setup(bot):
    await bot.add_cog(Basic(bot))
