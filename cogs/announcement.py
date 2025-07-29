from discord.ext import commands
import discord
import json
import os

ANNOUNCE_FILE = "../data/announcement.json"

def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

class Announcement(commands.Cog):
    """
    공지 등록과 조회를 담당하는 Cog입니다.
    wait_for를 사용하여 명령어 호출 후 사용자의 다음 두 메시지를 제목과 내용으로 순차적으로 수집합니다.
    """

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.announcements = load_json(ANNOUNCE_FILE)

    def save(self) -> None:
        """현재 공지 데이터를 디스크에 저장합니다."""
        os.makedirs(os.path.dirname(ANNOUNCE_FILE), exist_ok=True)
        save_json(ANNOUNCE_FILE, self.announcements)

    @commands.command(name="공지등록")
    @commands.guild_only()
    async def register_announcement(self, ctx: commands.Context) -> None:
        """
        새 공지를 등록합니다.
        제목과 내용을 순차적으로 입력받아 저장한 뒤 완료 메시지를 보냅니다.
        """
        guild_id = str(ctx.guild.id)

        # 제목 요청
        await ctx.send("공지의 제목을 입력해주세요.")

        def check_title(msg: discord.Message) -> bool:
            return msg.author == ctx.author and msg.channel == ctx.channel

        title_msg: discord.Message = await self.bot.wait_for("message", check=check_title)
        title = title_msg.content.strip()

        # 내용 요청
        await ctx.send("공지의 내용을 입력해주세요.")

        def check_content(msg: discord.Message) -> bool:
            return msg.author == ctx.author and msg.channel == ctx.channel

        content_msg: discord.Message = await self.bot.wait_for("message", check=check_content)
        content = content_msg.content.strip()

        # 저장
        self.announcements[guild_id] = {"title": title, "content": content}
        self.save()
        await ctx.send("공지 등록이 완료됐어요! 앞으로 불러주시면 제가 다른 분들께 알려드릴게요~")

    @commands.command(name="공지")
    @commands.guild_only()
    async def show_announcement(self, ctx: commands.Context) -> None:
        """
        현재 길드의 공지를 보여줍니다.
        등록된 공지가 없으면 안내 메시지를 보냅니다.
        """
        guild_id = str(ctx.guild.id)
        data = self.announcements.get(guild_id)

        if data:
            embed = discord.Embed(
                title=data["title"],
                description=data["content"],
                color=discord.Color.from_rgb(255, 192, 203),
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("이 서버에는 공지가 등록된 적이 없는 것 같은데~ 공지등록으로 먼저 저한테 내용을 알려주세요!.")

async def setup(bot):
    await bot.add_cog(Announcement(bot))
