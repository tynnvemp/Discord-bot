import discord
import chess
import chess.svg
import cairosvg
import io
import random
from discord import app_commands

board = chess.Board()
current_game = {}
message_refs = {}

def setup_chess_ai_commands(bot):

    class Difficulty:
        EASY = "easy"
        MEDIUM = "medium"
        HARD = "hard"

    @bot.tree.command(name="chessbot", description="Chơi cờ với bot AI")
    @app_commands.describe(difficulty="Chọn độ khó: easy, medium, hard")
    async def chessbot(interaction: discord.Interaction, difficulty: str):
        global board, current_game

        board = chess.Board()
        current_game[interaction.user.id] = {
            "difficulty": difficulty.lower(),
            "last_message": None
        }

        embed, file = render_board()
        view = SurrenderView(interaction.user.id)

        await interaction.response.send_message(
            content=f"🎯 Bạn đang chơi với bot ở chế độ **{difficulty.upper()}**",
            embed=embed,
            file=file,
            view=view
        )

        message_refs[interaction.user.id] = await interaction.original_response()

    @bot.tree.command(name="move", description="Đi nước cờ với bot")
    @app_commands.describe(move="Ví dụ: e2e4")
    async def move(interaction: discord.Interaction, move: str):
        global board, current_game
        await interaction.response.defer(ephemeral=True)
        user_id = interaction.user.id

        if user_id not in current_game:
            await interaction.response.send_message("❗ Bạn chưa bắt đầu ván cờ nào với bot.", ephemeral=True)
            return

        try:
            player_move = chess.Move.from_uci(move)
            if player_move not in board.legal_moves:
                raise ValueError()
            board.push(player_move)

            if board.is_checkmate():
                await replace_embed(interaction, f"🏁 Bạn đã chiếu hết bot!", final=True)
                current_game.pop(user_id)
                return

            # Bot move
            bot_move = select_bot_move(board, current_game[user_id]['difficulty'])
            board.push(bot_move)

            if board.is_checkmate():
                await replace_embed(interaction, f"💀 Bot đã chiếu hết bạn với nước `{bot_move}`!", final=True)
                current_game.pop(user_id)
                return

            await replace_embed(interaction, f"✅ Bạn đi `{move}`, bot phản đòn `{bot_move}`")

        except:
            await interaction.response.send_message("❌ Nước đi không hợp lệ.", ephemeral=True)

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
            return legal[0]  # sau có thể tích hợp Stockfish cho mode HARD

    async def replace_embed(interaction, content, final=False):
        embed, file = render_board()
        view = None if final else SurrenderView(interaction.user.id)

        old_msg = message_refs.get(interaction.user.id)
        if old_msg:
            try:
                await old_msg.delete()
            except:
                pass

        new_msg = await interaction.channel.send(content=content, embed=embed, file=file, view=view)
        message_refs[interaction.user.id] = new_msg
        if not final:
            await interaction.response.send_message("✅ Đã cập nhật ván cờ.", ephemeral=True)

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
