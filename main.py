import http.server
import json
import os
import random
import threading
import discord
from discord.ext import commands


# --- 1. เซิร์ฟเวอร์จำลองสำหรับ Render Web Service ---
class SimpleHandler(http.server.BaseHTTPRequestHandler):

  def do_GET(self):
    self.send_response(200)
    self.end_headers()
    self.wfile.write(b"Bot is alive!")


def run_server():
  port = int(os.environ.get("PORT", 10000))
  server = http.server.HTTPServer(("0.0.0.0", port), SimpleHandler)
  server.serve_forever()


threading.Thread(target=run_server, daemon=True).start()

# --- 2. โค้ดตั้งค่าบอท Discord ---
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# --- 3. ระบบจัดการชิป (Economy System) ---
DATA_FILE = "economy.json"


def load_data():
  if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
      return json.load(f)
  return {}


def save_data(data):
  with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4)


def get_chips(user_id):
  data = load_data()
  str_id = str(user_id)
  if str_id not in data:
    data[str_id] = 1000  # แจกชิปเริ่มต้น 1,000 ชิป
    save_data(data)
  return data[str_id]


def add_chips(user_id, amount):
  data = load_data()
  str_id = str(user_id)
  if str_id not in data:
    data[str_id] = 1000
  data[str_id] += amount
  save_data(data)


# --- 4. รันบอทด้วย Token ---
TOKEN = "DISCORD_TOKEN"
bot.run(TOKEN)


import json
import os
import random
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================= ระบบจัดการชิป (Economy System) =================
DATA_FILE = "economy.json"


def load_data():
  if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
      return json.load(f)
  return {}


def save_data(data):
  with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4)


def get_chips(user_id):
  data = load_data()
  str_id = str(user_id)
  if str_id not in data:
    data[str_id] = 1000  # แจกชิปเริ่มต้นให้ผู้เล่นใหม่ 1,000 ชิป
    save_data(data)
  return data[str_id]


def add_chips(user_id, amount):
  data = load_data()
  str_id = str(user_id)
  if str_id not in data:
    data[str_id] = 1000
  data[str_id] += amount
  save_data(data)


# ================= โครงสร้างและกฎเกมแบล็กแจ็ก =================
SUITS = ["♠️", "♥️", "♦️", "♣️"]
RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]


def create_deck():
  deck = [(rank, suit) for suit in SUITS for rank in RANKS]
  random.shuffle(deck)
  return deck


def calculate_score(hand):
  score = 0
  aces = 0
  for rank, _ in hand:
    if rank in ["J", "Q", "K"]:
      score += 10
    elif rank == "A":
      aces += 1
      score += 11
    else:
      score += int(rank)

  while score > 21 and aces > 0:
    score -= 10
    aces -= 1

  return score


def format_hand(hand):
  return " ".join([f"[{rank}{suit}]" for rank, suit in hand])


# ================= ปุ่มกด Interactive (Discord UI) =================
class BlackjackView(discord.ui.View):

  def __init__(self, author, deck, player_hand, dealer_hand, bet):
    super().__init__(timeout=60)
    self.author = author
    self.deck = deck
    self.player_hand = player_hand
    self.dealer_hand = dealer_hand
    self.bet = bet

  async def interaction_check(self, interaction: discord.Interaction) -> bool:
    if interaction.user != self.author:
      await interaction.response.send_message(
          "❌ นี่ไม่ใช่กระดานของคุณ! พิมพ์ !bj เพื่อเริ่มเล่นเองได้เลย",
          ephemeral=True,
      )
      return False
    return True

  @discord.ui.button(
      label="จั่วไพ่ (Hit) 🃏", style=discord.ButtonStyle.primary
  )
  async def hit_button(
      self, interaction: discord.Interaction, button: discord.ui.Button
  ):
    self.player_hand.append(self.deck.pop())
    player_score = calculate_score(self.player_hand)

    if player_score > 21:
      for child in self.children:
        child.disabled = True

      add_chips(self.author.id, -self.bet)
      current_chips = get_chips(self.author.id)

      embed = discord.Embed(
          title=f"💥 แต้มเกิน 21! คุณแพ้แล้ว (เสีย {self.bet:,} ชิป)",
          color=discord.Color.red(),
      )
      embed.add_field(
          name="ไพ่ของคุณ",
          value=f"{format_hand(self.player_hand)}\n**แต้มรวม:** {player_score}",
          inline=False,
      )
      embed.add_field(
          name="ไพ่ของเจ้ามือ",
          value=f"{format_hand(self.dealer_hand)}\n**แต้มรวม:** {calculate_score(self.dealer_hand)}",
          inline=False,
      )
      embed.set_footer(text=f"💰 ชิปคงเหลือของคุณ: {current_chips:,} ชิป")
      await interaction.response.edit_message(embed=embed, view=self)
      self.stop()
    else:
      embed = discord.Embed(
          title=f"🃏 เกมแบล็กแจ็ก (เดิมพัน: {self.bet:,} ชิป)",
          color=discord.Color.blue(),
      )
      embed.add_field(
          name="ไพ่ของคุณ",
          value=f"{format_hand(self.player_hand)}\n**แต้มรวม:** {player_score}",
          inline=False,
      )
      embed.add_field(
          name="ไพ่ของเจ้ามือ",
          value=f"[{self.dealer_hand[0][0]}{self.dealer_hand[0][1]}] [❓]",
          inline=False,
      )
      await interaction.response.edit_message(embed=embed, view=self)

  @discord.ui.button(
      label="พอแล้ว (Stand) ✋", style=discord.ButtonStyle.success
  )
  async def stand_button(
      self, interaction: discord.Interaction, button: discord.ui.Button
  ):
    for child in self.children:
      child.disabled = True

    player_score = calculate_score(self.player_hand)
    dealer_score = calculate_score(self.dealer_hand)

    while dealer_score < 17:
      self.dealer_hand.append(self.deck.pop())
      dealer_score = calculate_score(self.dealer_hand)

    if dealer_score > 21 or player_score > dealer_score:
      add_chips(self.author.id, self.bet)
      result = f"🎉 **คุณชนะ!** (ได้รับ +{self.bet:,} ชิป)"
      color = discord.Color.green()
    elif player_score < dealer_score:
      add_chips(self.author.id, -self.bet)
      result = f"❌ **คุณแพ้!** (เสีย -{self.bet:,} ชิป)"
      color = discord.Color.red()
    else:
      result = "🤝 **เสมอกัน!** (คืนเงินเดิมพัน)"
      color = discord.Color.gold()

    current_chips = get_chips(self.author.id)

    embed = discord.Embed(title=f"สรุปผล: {result}", color=color)
    embed.add_field(
        name="ไพ่ของคุณ",
        value=f"{format_hand(self.player_hand)}\n**แต้มรวม:** {player_score}",
        inline=False,
    )
    embed.add_field(
        name="ไพ่ของเจ้ามือ",
        value=f"{format_hand(self.dealer_hand)}\n**แต้มรวม:** {dealer_score}",
        inline=False,
    )
    embed.set_footer(text=f"💰 ชิปคงเหลือของคุณ: {current_chips:,} ชิป")

    await interaction.response.edit_message(embed=embed, view=self)
    self.stop()


# ================= คำสั่งบอท (Commands) =================


# 1. เช็กยอดชิป
@bot.command(name="money", aliases=["ชิป", "chips", "bal"])
async def money(ctx):
  chips = get_chips(ctx.author.id)
  await ctx.send(f"💰 คุณ {ctx.author.mention} มีชิปทั้งหมด **{chips:,}** ชิป")


# 2. รับชิปฟรีประจำวัน
@bot.command(name="daily", aliases=["แจกเงิน"])
async def daily(ctx):
  add_chips(ctx.author.id, 1000)
  chips = get_chips(ctx.author.id)
  await ctx.send(
      f"🎁 คุณ {ctx.author.mention} ได้รับชิปฟรี **1,000** ชิป!\n💰"
      f" ยอดปัจจุบัน: **{chips:,}** ชิป"
  )


# 3. โอนชิปให้เพื่อน
@bot.command(name="pay", aliases=["โอน", "give", "transfer"])
async def pay(ctx, member: discord.Member, amount: int):
  if member == ctx.author:
    await ctx.send("❌ คุณไม่สามารถโอนชิปให้ตัวเองได้ครับ!")
    return
  if member.bot:
    await ctx.send("❌ คุณไม่สามารถโอนชิปให้บอทได้!")
    return
  if amount <= 0:
    await ctx.send("❌ จำนวนชิปที่ต้องการโอนต้องมากกว่า 0 ครับ!")
    return

  sender_chips = get_chips(ctx.author.id)
  if sender_chips < amount:
    await ctx.send(
        f"❌ ชิปของคุณไม่พอโอน! คุณมีอยู่ **{sender_chips:,}** ชิป"
    )
    return

  add_chips(ctx.author.id, -amount)
  add_chips(member.id, amount)
  remaining_chips = get_chips(ctx.author.id)

  await ctx.send(
      f"💸 คุณ {ctx.author.mention} ได้โอนชิปจำนวน **{amount:,}** ชิป"
      f" ให้กับ {member.mention} เรียบร้อยแล้ว!\n💰 ยอดชิปคงเหลือของคุณ:"
      f" **{remaining_chips:,}** ชิป"
  )


# 4. เล่นแบล็กแจ็ก (รองรับการระบุจำนวน หรือพิมพ์ all)
@bot.command(name="bj", aliases=["blackjack", "แบล็กแจ็ก"])
async def blackjack(ctx, bet_arg: str = "100"):
  player_chips = get_chips(ctx.author.id)

  if bet_arg.lower() in ["all", "allin", "หมดตัว"]:
    bet = player_chips
  else:
    try:
      bet = int(bet_arg)
    except ValueError:
      await ctx.send(
          "❌ กรุณากรอกจำนวนชิปให้ถูกต้อง เช่น `!bj 100` หรือ `!bj all`"
      )
      return

  if bet <= 0:
    await ctx.send("❌ จำนวนชิปเดิมพันต้องมากกว่า 0 ครับ!")
    return

  if bet > player_chips:
    await ctx.send(
        f"❌ ชิปของคุณไม่พอ! คุณมีอยู่ **{player_chips:,}** ชิป"
        " (พิมพ์ `!daily` เพื่อรับชิปฟรีได้นะ)"
    )
    return

  deck = create_deck()
  player_hand = [deck.pop(), deck.pop()]
  dealer_hand = [deck.pop(), deck.pop()]
  player_score = calculate_score(player_hand)

  all_in_text = " 🔥 [ALL-IN ทุ่มหมดหน้าตัก!]" if bet == player_chips else ""

  embed = discord.Embed(
      title=f"🃏 เริ่มเกมแบล็กแจ็ก (เดิมพัน: {bet:,} ชิป){all_in_text}",
      color=discord.Color.gold() if bet == player_chips else discord.Color.blue(),
  )
  embed.add_field(
      name="ไพ่ของคุณ",
      value=f"{format_hand(player_hand)}\n**แต้มรวม:** {player_score}",
      inline=False,
  )
  embed.add_field(
      name="ไพ่ของเจ้ามือ",
      value=f"[{dealer_hand[0][0]}{dealer_hand[0][1]}] [❓]",
      inline=False,
  )

  view = BlackjackView(ctx.author, deck, player_hand, dealer_hand, bet)
  await ctx.send(embed=embed, view=view)


@bot.event
async def on_ready():
  print(f"✅ บอทแบล็กแจ็กสมบูรณ์แบบ {bot.user} พร้อมทำงานแล้ว!")


# 🔑 ใส่ Token ของบอทคุณตรงนี้ (ครอบด้วยเครื่องหมายคำพูด "")
import os

bot.run(os.environ.get("DISCORD_TOKEN"))

