import discord
import chess
import random
import io
import cairosvg
from discord.ext import commands

# dùng chung với chess_bot_game
board = chess.Board()
current_game = {}
message_refs = {}

def setup_chess_prefix_commands(bot: commands.Bot):

    @bot.command(name="chess_start")
    async def chess_start(ctx, difficulty: str):
        if difficulty.lower() not in ["easy", "medium", "hard"]:
            await ctx.send("❗ Độ khó không hợp lệ. Chọn: easy, medium, hard.")
            return

        global board, current_game

        board = chess.Board()
        current_game[ctx.author.id] = {
            "difficulty": difficulty.lower(),
            "last_message": None
        }

        embed, file = render_board()
        view = SurrenderView(ctx.author.id)

        message = await ctx.send(
            content=f"🎯 Bạn đang chơi với bot ở chế độ **{difficulty.upper()}**",
            embed=embed,
            file=file,
            view=view
        )

        message_refs[ctx.author.id] = message

    @bot.command(name="move")
    async def move_cmd(ctx, move: str):
        global board, current_game
        user_id = ctx.author.id

        if user_id not in current_game:
            await ctx.send("❗ Bạn chưa bắt đầu ván cờ nào với bot.")
            return

        try:
            player_move = chess.Move.from_uci(move)
            if player_move not in board.legal_moves:
                raise ValueError()
            board.push(player_move)

            if board.is_checkmate():
                await ctx.send(f"🏁 Bạn đã chiếu hết bot!")
                current_game.pop(user_id)
                return

            bot_move = select_bot_move(board, current_game[user_id]['difficulty'])
            board.push(bot_move)

            if board.is_checkmate():
                await ctx.send(f"💀 Bot đã chiếu hết bạn với nước `{bot_move}`!")
                current_game.pop(user_id)
                return

            embed, file = render_board()
            await ctx.send(f"✅ Bạn đi `{move}`, bot phản đòn `{bot_move}`", embed=embed, file=file)

        except:
            await ctx.send("❌ Nước đi không hợp lệ.")

    def render_board():
        svg = chess.svg.board(board, size=350)
        png = cairosvg.svg2png(bytestring=svg.encode("utf-8"))
        file = discord.File(io.BytesIO(png), filename="board.png")
        embed = discord.Embed(title="🤖 Cờ với AI")
        embed.set_image(url="attachment://board.png")
        return embed, file

    def select_bot_move(board, difficulty):
        legal = list(board.legal_moves)
        if difficulty == "easy":
            return random.choice(legal)
        elif difficulty == "medium":
            captures = [m for m in legal if board.is_capture(m)]
            return random.choice(captures or legal)
        else:
            return legal[0]

    class SurrenderView(discord.ui.View):
        def __init__(self, player_id):
            super().__init__()
            self.player_id = player_id

        @discord.ui.button(label="Surrender", style=discord.ButtonStyle.danger)
        async def surrender(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != self.player_id:
                await interaction.response.send_message("❗ Đây không phải ván cờ của bạn.", ephemeral=True)
                return
            await interaction.message.delete()
            await interaction.channel.send(f"🏳️ {interaction.user.mention} đã đầu hàng trước bot.")
            current_game.pop(interaction.user.id, None)
            message_refs.pop(interaction.user.id, None)
