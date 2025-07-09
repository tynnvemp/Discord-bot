import discord
from discord import app_commands
from discord.ext import commands
import random, json, os, threading, asyncio
from flask import Flask
from datetime import datetime, timedelta

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "users.json"

# Load dữ liệu coin từ file
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'r') as f:
        user_data = json.load(f)
else:
    user_data = {}

def save_data():
    with open(DATA_FILE, 'w') as f:
        json.dump(user_data, f)

def get_coins(user_id):
    return user_data.get(str(user_id), {}).get("coins", 100)

def set_coins(user_id, amount):
    uid = str(user_id)
    if uid not in user_data:
        user_data[uid] = {}
    user_data[uid]["coins"] = amount
    save_data()

def can_claim_daily(user_id):
    uid = str(user_id)
    now = datetime.utcnow()
    last = user_data.get(uid, {}).get("last_daily")
    if last:
        last_time = datetime.fromisoformat(last)
        return now - last_time >= timedelta(hours=24)
    return True

def update_daily_time(user_id):
    uid = str(user_id)
    if uid not in user_data:
        user_data[uid] = {}
    user_data[uid]["last_daily"] = datetime.utcnow().isoformat()
    save_data()

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot đã sẵn sàng: {bot.user}")

from chess_game import setup_chess_commands
setup_chess_commands(bot)

bot.tree.command(name="wallet", description="Xem số coin hiện tại")
async def wallet(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True, ephemeral=True)
    coins = get_coins(interaction.user.id)
    await interaction.followup.send(f"💼 Bạn hiện có **{coins}** coins.")

@bot.tree.command(name="daily", description="Nhận 50 coin mỗi ngày")
async def daily(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True, ephemeral=True)
    uid = interaction.user.id
    if can_claim_daily(uid):
        new_amount = get_coins(uid) + 50
        set_coins(uid, new_amount)
        update_daily_time(uid)
        await interaction.followup.send("🎁 Bạn đã nhận được **50** coin hôm nay!")
    else:
        await interaction.followup.send("⏳ Bạn đã nhận hôm nay rồi. Hãy quay lại sau 24 giờ!")

@bot.tree.command(name="topcoin", description="Xem top 10 người giàu nhất")
async def topcoin(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    sorted_users = sorted(user_data.items(), key=lambda x: x[1].get("coins", 0), reverse=True)
    embed = discord.Embed(title="🏆 Top 10 Người Giàu", color=0xf1c40f)
    for i, (uid, info) in enumerate(sorted_users[:10]):
        try:
            user = await bot.fetch_user(int(uid))
            embed.add_field(name=f"#{i+1} - {user.name}", value=f"💰 {info.get('coins', 0)} coins", inline=False)
        except:
            continue
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="dice", description="Tung xúc xắc")
async def dice(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True, ephemeral=True)
    roll = random.randint(1, 6)
    embed = discord.Embed(title="🎲 Xúc Xắc", description=f"Bạn tung ra: **{roll}**", color=0x00ff00)
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="lwheel", description="Cược coins vào vòng quay đỏ/đen")
@app_commands.describe(
    amount="Số coin muốn cược",
    color="Màu bạn muốn cược: do hoặc den"
)
async def lwheel(interaction: discord.Interaction, amount: int, color: str):
    await interaction.response.defer(thinking=True, ephemeral=True)
    user_id = interaction.user.id
    current = get_coins(user_id)

    if amount > current:
        await interaction.followup.send("❌ Bạn không đủ coin để cược!")
        return

    if color.lower() not in ["do", "den"]:
        await interaction.followup.send("⚠️ Chỉ được cược vào `do` hoặc `den`.")
        return

    mau_nguoi = color.lower()
    ket_qua = random.choice(["do", "den"] * 5)

    # Hiệu ứng quay vòng
    spin_embed = discord.Embed(title="🎡 Đang quay vòng...", description="⏳ Vui lòng chờ...", color=0xaaaaaa)
    message = await interaction.followup.send(embed=spin_embed)

    pattern = [["🔴", "⚫"], ["⚫", "🔴"], ["🔴", "🔴", "⚫"], ["⚫", "⚫", "🔴"], ["🔴", "⚫", "🔴"]]
    for i in range(6):
        row = " ".join(random.choice(pattern))
        temp_embed = discord.Embed(title="🎡 Đang quay vòng...", description=row, color=0xaaaaaa)
        await message.edit(embed=temp_embed)
        await asyncio.sleep(0.5)

    # Kết quả
    final_color = 0xff0000 if ket_qua == "do" else 0x000000
    result_embed = discord.Embed(
        title="🎯 Kết Quả Vòng Quay",
        description=f"Bạn chọn: **{mau_nguoi.upper()}**\nKết quả: **{ket_qua.upper()}**",
        color=final_color
    )

    if ket_qua == mau_nguoi:
        set_coins(user_id, current + amount)
        result_embed.add_field(name="🎉 Chúc mừng!", value=f"Bạn thắng **{amount}** coins!", inline=False)
    else:
        set_coins(user_id, current - amount)
        result_embed.add_field(name="💸 Rất tiếc!", value=f"Bạn thua **{amount}** coins.", inline=False)

    result_embed.set_footer(text=f"💼 Số coin còn lại: {get_coins(user_id)}")
    await message.edit(embed=result_embed)

# Flask giữ bot sống trên Render
app = Flask('')

@app.route('/')
def home():
    return "Bot đang hoạt động!"

def run():
    app.run(host='0.0.0.0', port=8080)

threading.Thread(target=run).start()

# Chạy bot với token từ biến môi trường
bot.run(os.getenv("DISCORD_TOKEN"))
    
