from discord.ext import commands
import discord
import random
import asyncio
from cogs.points import Points
from config import BOT_NAME


class Blackjack(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.points: Points = None
        self.loss_streaks = {}

    def draw_card(self):
        deck = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        return random.choice(deck)

    def calculate_score(self, cards):
        score = 0
        aces = 0
        for card in cards:
            if card in ["J", "Q", "K"]: score += 10
            elif card == "A":
                score += 11
                aces += 1
            else: score += int(card)
        while score > 21 and aces > 0:
            score -= 10
            aces -= 1
        return score

    def format_cards(self, cards):
        return ", ".join(cards)

    async def handle_streak(self, ctx, user_id, guild_id, amount, result_type):
        streak_key = (guild_id, user_id)
        
        if result_type >= 0:
            self.loss_streaks[streak_key] = []
            return ""

        if streak_key not in self.loss_streaks:
            self.loss_streaks[streak_key] = []
        
        self.loss_streaks[streak_key].append(amount)

        if len(self.loss_streaks[streak_key]) >= 3:
            history = self.loss_streaks[streak_key]
            avg_loss = sum(history) // len(history)
            self.points.add_points(user_id, guild_id, avg_loss)

            pity_msg = f"\n\n**[특별 구제!]**\n3연속 패배는 조금 그렇긴 하죠? 자, 여기! {avg_loss}P 돌려드릴게요~"
            self.loss_streaks[streak_key] = []
            return pity_msg
        
        return ""


    @commands.command(name="블랙잭")
    async def blackjack(self, ctx):
        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)

        if self.points is None:
            await ctx.send("❌ 포인트 시스템이 작동하지 않고 있습니다. 관리자에게 문의해 주세요.")
            return

        await ctx.send(
            f"{ctx.author.mention} 씨, 반가워요! 제 딜러일 적 실력을 보여드리죠! 자, 몇 포인트 걸어볼래요? **숫자**로만 알려주세요~"
        )

        def bet_check(m):
            return (
                m.author == ctx.author
                and m.channel == ctx.channel
                and m.content.isdigit()
            )

        try:
            msg = await self.bot.wait_for("message", check=bet_check, timeout=20)
            amount = int(msg.content)
        except asyncio.TimeoutError:
            await ctx.send("음? 마음이 바뀌셨나? 나중에 하실 마음 생기면 다시 와주세요~")
            return

        if amount <= 0:
            await ctx.send("에이, 1포인트라도 걸어야 재미가 있지 않겠어요? 다시 시도해 주세요!")
            return

        user_points = self.points.get_points(user_id, guild_id)
        if user_points < amount:
            await ctx.send(
                f"{ctx.author.mention} 씨, 포인트가 부족하신데요?\n참고로 현재 보유하신 포인트는 {user_points}P예요~"
            )
            return

        # 초기 카드 배분
        player_cards = [self.draw_card(), self.draw_card()]
        dealer_cards = [self.draw_card(), self.draw_card()]

        player_score = self.calculate_score(player_cards)
        dealer_score = self.calculate_score(dealer_cards)

        # 시작 메시지
        await ctx.send(
            f"{ctx.author.display_name}의 카드: {self.format_cards(player_cards)}(합계: {player_score})\n"
            f"제 패: {dealer_cards[0]}, ? \n"
        )

        # 처음부터 플레이어 블랙잭
        player_blackjack = player_score == 21
        dealer_blackjack = dealer_score == 21

        if player_blackjack or dealer_blackjack:
            result = (
                f"\n{ctx.author.display_name}씨가 받은 카드: {self.format_cards(player_cards)} (합계: {player_score})\n"
                f"제 패도 보여드릴게요~\n{self.format_cards(dealer_cards)} (합계: {dealer_score})\n"
            )

            if player_blackjack and dealer_blackjack:
                result += "\n오! 둘 다 블랙잭이라니, 이거 오늘 복권 사야 하는 거 아닐까요? 포인트는 못 받아가시겠지만~"
                await self.handle_streak(ctx, user_id, guild_id, amount, 0) # 무승부 초기화
            elif player_blackjack:
                bonus = int(amount * 1.5)
                self.points.add_points(user_id, guild_id, bonus)
                result += f"\n와, 처음부터 블랙잭? 이거 맞나요?! {bonus}P 획득입니다! 오늘 운이 정말 좋으시네요~"
                await self.handle_streak(ctx, user_id, guild_id, amount, 1) # 승리 초기화
            else:
                self.points.subtract_points(user_id, guild_id, amount)
                result += f"\n아이고, 더 이어가드리고 싶지만~ 아쉽게도 제가 블랙잭이네요? {amount}P는 제가 잘~ 가지고 있을게요!"
                
                # 반환된 구제 메시지를 result에 추가
                msg_addition = await self.handle_streak(ctx, user_id, guild_id, amount, -1)
                result += msg_addition
                
            await ctx.send(result)
            return

        # 플레이어 턴
        while True:
            await ctx.send(
                f"\n한 장 더 받으시겠어요? 응, 아니 중에 말씀해 주세요~"
            )

            def action_check(m):
                return (
                    m.author == ctx.author
                    and m.channel == ctx.channel
                    and m.content.lower() in ["응", "아니"]
                )

            try:
                action_msg = await self.bot.wait_for(
                    "message", check=action_check, timeout=20
                )
                action = action_msg.content.lower()
            except asyncio.TimeoutError:
                self.points.subtract_points(user_id, guild_id, amount)
                
                # 타임아웃 패배 시에도 구제 메시지를 확인하여 출력
                msg_addition = await self.handle_streak(ctx, user_id, guild_id, amount, -1)
                await ctx.send(f"음? 포기하시는 거예요? 아쉽다. {amount}P는 제가 잘 가지고 있을게요?{msg_addition}")
                return

            if action == "응":
                new_card = self.draw_card()
                player_cards.append(new_card)
                player_score = self.calculate_score(player_cards)

                await ctx.send(
                    f"{ctx.author.display_name}의 새로운 카드: {new_card}\n"
                    f"{ctx.author.display_name}의 카드: {self.format_cards(player_cards)} (합계: {player_score})"
                )

                if player_score > 21:
                    self.points.subtract_points(user_id, guild_id, amount)
                    msg_addition = await self.handle_streak(ctx, user_id, guild_id, amount, -1)
                    await ctx.send(
                        f"앗, 21을 넘었네요! 아쉬워라. {amount}P는 제가 잘 가지고 있을게요~{msg_addition}"
                    )
                    return
            else:
                break

        # 딜러 턴
        reveal_msg = (
            f"자, 이제 제 패를 한 번 볼까요?\n\n"
            f"{self.format_cards(dealer_cards)} (합계: {dealer_score})"
        )
        await ctx.send(reveal_msg)

        while dealer_score < 17:
            new_card = self.draw_card()
            dealer_cards.append(new_card)
            dealer_score = self.calculate_score(dealer_cards)

            await ctx.send(
                f"음~ 한 장 더 뽑아볼게요~\n"
                f"지금 아까 숨긴 패 빼면, {self.format_cards(dealer_cards)}해서 총 {dealer_score}점이에요~\n"
            )

        # 결과 판정
        result = (
                f"\n{ctx.author.display_name}씨가 받으신 카드: {self.format_cards(player_cards)} (합계: {player_score})\n"
                f"자, 제 패는~\n{self.format_cards(dealer_cards)} (합계: {dealer_score})\n"
            )

        if dealer_score > 21:
            self.points.add_points(user_id, guild_id, amount)
            result += f"\n아이고, 제가 버스트가 났네요! {amount}P 여깄습니다~"
            await self.handle_streak(ctx, user_id, guild_id, amount, 1)
        elif player_score > dealer_score:
            self.points.add_points(user_id, guild_id, amount)
            result += f"\n오, 더 높은 숫자~ 아쉽네요! 그래도 축하드려요? 여기, 약속드린 {amount}P도 가져가시고요!"
            await self.handle_streak(ctx, user_id, guild_id, amount, 1)
        elif player_score < dealer_score:
            self.points.subtract_points(user_id, guild_id, amount)
            result += f"\n앗, 아쉽게도 제가 조금 더 높네요! {amount}P는 제가 잘~ 맡아두고 있을게요!"
            
            msg_addition = await self.handle_streak(ctx, user_id, guild_id, amount, -1)
            result += msg_addition
            
        else:
            result += "\n오, 이게 같은 숫자가 뜨기 쉽지 않은데~ 우연이네요! 운명인가? 하하.​​​​​​​​​​​​​​​​"
            await self.handle_streak(ctx, user_id, guild_id, amount, 0)

        await ctx.send(result)

    async def cog_load(self):
        points_cog = self.bot.get_cog("Points")
        if isinstance(points_cog, Points):
            self.points = points_cog


async def setup(bot):
    await bot.add_cog(Blackjack(bot))
