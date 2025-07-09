import discord
from discord import app_commands
from discord.ext import commands
import random
import threading
from flask import Flask
import os

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

user_coins = {}
def get_coins(user_id):
    return user_coins.get(user_id, 100)

def set_coins(user_id, amount):
    user_coins[user_id] = amount

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"🤖 Bot đã sẵn sàng dưới tên: {bot.user}")

@bot.tree.command(name="dice", description="Tung xúc xắc (1-6)")
async def dice(interaction: discord.Interaction):
    roll = random.randint(1, 6)
    embed = discord.Embed(title="🎲 Xúc Xắc", description=f"Bạn tung ra: **{roll}**", color=0x00ff00)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="wallet", description="Xem số coin hiện tại")
async def wallet(interaction: discord.Interaction):
    coins = get_coins(interaction.user.id)
    await interaction.response.send_message(f"💰 Bạn hiện có **{coins}** coins.")

@bot.tree.command(name="lwheel", description="Cược coins vào vòng quay đỏ/đen")
@app_commands.describe(
    amount="Số coin muốn cược",
    color="Màu bạn muốn cược: do hoặc den"
)
async def lwheel(interaction: discord.Interaction, amount: int, color: str):
    user_id = interaction.user.id
    current = get_coins(user_id)

    if amount > current:
        await interaction.response.send_message("❌ Bạn không đủ coin để cược!", ephemeral=True)
        return

    if color.lower() not in ["do", "den"]:
        await interaction.response.send_message("⚠️ Chỉ được cược vào `do` hoặc `den`.", ephemeral=True)
        return

    mau_nguoi = color.lower()
    ket_qua = random.choice(["do", "den"] * 5)

    embed = discord.Embed(
        title="🎡 Vòng Quay May Mắn",
        description=f"Bạn chọn: **{mau_nguoi.upper()}**\nKết quả quay: **{ket_qua.upper()}**",
        color=0xff0000 if ket_qua == "do" else 0x000000
    )

    if ket_qua == mau_nguoi:
        set_coins(user_id, current + amount)
        embed.add_field(name="🎉 Chúc mừng!", value=f"Bạn thắng **{amount}** coins!", inline=False)
    else:
        set_coins(user_id, current - amount)
        embed.add_field(name="💸 Rất tiếc!", value=f"Bạn thua **{amount}** coins.", inline=False)

    embed.set_footer(text=f"💼 Số coin còn lại: {get_coins(user_id)}")
    await interaction.response.send_message(embed=embed)

# Flask server để giữ bot sống
app = Flask('')

@app.route('/')
def home():
    return "Bot đang hoạt động!"

def run():
    app.run(host='0.0.0.0', port=8080)

threading.Thread(target=run).start()

bot.run(os.getenv("DISCORD_TOKEN"))
