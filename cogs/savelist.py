import json
from pathlib import Path
from discord.ext import commands

DATA_FILE = Path("data/list_data.json")
DATA_FILE.parent.mkdir(parents=True, exist_ok=True)  # data 폴더 없으면 생성

if not DATA_FILE.exists():
    DATA_FILE.write_text(json.dumps({}))


class List(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = self.load_data()

    def load_data(self):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_data(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def get_guild_data(self, guild_id):
        guild_id = str(guild_id)
        if guild_id not in self.data:
            self.data[guild_id] = {}
        return self.data[guild_id]

    @commands.command(name="저장")
    async def save_list(self, ctx):
        guild_id = str(ctx.guild.id)
        await ctx.send("저장할 내용의 **제목**을 입력해 주세요.")

        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        try:
            name_msg = await self.bot.wait_for("message", timeout=30.0, check=check)
            name = name_msg.content.strip()

            await ctx.send("저장할 내용의 **링크 혹은 설명**을 입력해 주세요.")
            link_msg = await self.bot.wait_for("message", timeout=30.0, check=check)
            link = link_msg.content.strip()

            guild_data = self.get_guild_data(guild_id)
            guild_data[name] = link
            self.save_data()
            await ctx.send(f"**'{name}'** 이(가) 저장되었습니다.")
        except Exception:
            await ctx.send("시간이 초과되었어요. 다시 시도해 주세요!")

    @commands.command(name="삭제")
    async def delete_list(self, ctx):
        guild_id = str(ctx.guild.id)
        await ctx.send("삭제할 리스트의 **제목**을 입력해 주세요.")

        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        try:
            name_msg = await self.bot.wait_for("message", timeout=30.0, check=check)
            name = name_msg.content.strip()

            guild_data = self.get_guild_data(guild_id)
            if name in guild_data:
                del guild_data[name]
                self.save_data()
                await ctx.send(f"**'{name}'** 이(가) 삭제되었습니다.")
            else:
                await ctx.send("해당 이름의 리스트가 존재하지 않아요.")
        except Exception:
            await ctx.send("시간이 초과되었어요. 다시 시도해 주세요!")

    @commands.command(name="목록")
    async def list_lists(self, ctx):
        guild_id = str(ctx.guild.id)
        guild_data = self.get_guild_data(guild_id)

        if not guild_data:
            await ctx.send("저장된 리스트가 없어요.")
        else:
            lines = ["저장된 리스트 목록:\n"]
            for name, link in guild_data.items():
                lines.append(f"• **{name}**: <{link}>")
            await ctx.send("\n".join(lines))


async def setup(bot):
    await bot.add_cog(List(bot))
