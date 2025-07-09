import discord
import chess
import chess.svg
import cairosvg
import io
from discord import app_commands

# Trạng thái ván cờ toàn cục
chess_board = chess.Board()
players = {}

# Hàm gọi từ main.py để đăng ký lệnh
def setup_chess_commands(bot):

    @bot.tree.command(name="chess_start", description="Bắt đầu ván cờ giữa bạn và 1 người khác")
    @app_commands.describe(opponent="Người bạn muốn chơi cùng")
    async def chess_start(interaction: discord.Interaction, opponent: discord.Member):
        global players, chess_board
        players = {
            "white": interaction.user,
            "black": opponent
        }
        chess_board = chess.Board()
        embed, file = generate_board_embed()
        await interaction.response.send_message(
            f"♟️ Ván cờ bắt đầu!\nTrắng: {interaction.user.mention}\nĐen: {opponent.mention}",
            embed=embed,
            file=file
        )

    @bot.tree.command(name="chess_move", description="Đi nước cờ theo định dạng UCI")
    @app_commands.describe(move="Ví dụ: e2e4")
    async def chess_move(interaction: discord.Interaction, move: str):
        global chess_board, players

        if not players:
            await interaction.response.send_message("❗ Chưa có ván cờ nào đang diễn ra.", ephemeral=True)
            return

        user = interaction.user
        turn = "white" if chess_board.turn == chess.WHITE else "black"

        if players[turn].id != user.id:
            await interaction.response.send_message(f"⏳ Chưa đến lượt bạn ({turn}).", ephemeral=True)
            return

        try:
            chess_move = chess.Move.from_uci(move)
            if chess_move not in chess_board.legal_moves:
                raise ValueError()

            chess_board.push(chess_move)

            embed, file = generate_board_embed()

            if chess_board.is_checkmate():
                await interaction.response.send_message(
                    f"🏁 Chiếu hết! {user.mention} thắng!", embed=embed, file=file
                )
                players.clear()
            elif chess_board.is_stalemate():
                await interaction.response.send_message(
                    f"🤝 Ván cờ hoà!", embed=embed, file=file
                )
                players.clear()
            else:
                await interaction.response.send_message(
                    f"✅ {user.mention} đã đi `{move}`", embed=embed, file=file
                )

        except Exception:
            await interaction.response.send_message("❌ Nước đi không hợp lệ. Định dạng hợp lệ: `e2e4`, `g1f3`,...", ephemeral=True)

# Hàm tạo ảnh bàn cờ và embed
def generate_board_embed():
    svg_data = chess.svg.board(chess_board, size=350)
    png_bytes = cairosvg.svg2png(bytestring=svg_data.encode('utf-8'))
    file = discord.File(io.BytesIO(png_bytes), filename="board.png")
    embed = discord.Embed(title="📷 Bàn Cờ Hiện Tại")
    embed.set_image(url="attachment://board.png")
    return embed, file
