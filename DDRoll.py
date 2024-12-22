import discord
from discord.ext import commands
import random
import json
import os

################################
################################
################################
TOKEN = ""
lang = "ja"  # "en" or "ja"
################################
################################
################################

# ファイル名
MESSAGE_DATA_FILE = "message_ids.json"

# ローカルにメッセージ ID を保存する関数
def save_message_ids(message_ids):
    try:
        with open(MESSAGE_DATA_FILE, "w") as file:
            json.dump(message_ids, file)
    except Exception as e:
        print(f"Failed to save message IDs: {e}")

# ローカルからメッセージ ID を読み込む関数
def load_message_ids():
    if os.path.exists(MESSAGE_DATA_FILE):
        try:
            with open(MESSAGE_DATA_FILE, "r") as file:
                return json.load(file)
        except Exception as e:
            print(f"Failed to load message IDs: {e}")
    return []

# 古いメッセージを削除する関数
async def delete_old_messages(channel, message_ids):
    for message_id in message_ids:
        try:
            message = await channel.fetch_message(message_id)
            await message.delete()
        except discord.NotFound:
            pass
    save_message_ids([])  # 削除後にファイルをクリア

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# メッセージ ID の管理
message_ids = []

# 情報の初期化
participants = set()
roll_results = {}
logs = []

# ボットの状態管理フラグ
flag = False

# 情報を集約してメッセージ内容を生成
def generate_message_content():
    if lang == "ja":
        participants_list = "\n".join([f"<@{user_id}>" for user_id in participants]) if participants else "参加者はいません。"
        results_list = "\n".join([f"<@{user_id}>: {roll}" for user_id, roll in roll_results.items()]) if roll_results else "まだ結果はありません。"
        logs_list = "\n".join(logs[-3:]) if logs else "ログはありません。"
        return f"**参加者一覧:**\n{participants_list}\n\n**ダイスロールの結果:**\n{results_list}\n\n**最新のログ:**\n{logs_list}"
    else:
        participants_list = "\n".join([f"<@{user_id}>" for user_id in participants]) if participants else "No participants."
        results_list = "\n".join([f"<@{user_id}>: {roll}" for user_id, roll in roll_results.items()]) if roll_results else "No results yet."
        logs_list = "\n".join(logs[-3:]) if logs else "No logs."
        return f"**Participants:**\n{participants_list}\n\n**Results of dice rolls:**\n{results_list}\n\n**Latest logs:**\n{logs_list}"

# メッセージの送信または編集
async def send_or_edit_message(channel):
    global message_ids
    content = generate_message_content()
    if len(message_ids) > 1:
        try:
            message = await channel.fetch_message(message_ids[1])
            await message.edit(content=content)
        except discord.NotFound:
            message = await channel.send(content)
            message_ids[1] = message.id
    else:
        message = await channel.send(content)
        message_ids.append(message.id)
    save_message_ids(message_ids)

# ボタンのビューを定義
class DiceRollView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        if lang == "ja":
            self.button_label = ["ダイスロールに参加", "参加者リセット", "ダイスロール"]
            self.log_text = ["さんがダイスロールに参加しました。", "参加者リストをリセットしました。", "ダイスロールを実行しました。"]
        else:
            self.button_label = ["Join Roll", "Reset Participants", "Roll Dice"]
            self.log_text = ["Joined the dice roll.", "Reset the participants list.", "Executed the dice roll."]

    @discord.ui.button(label="参加", style=discord.ButtonStyle.primary)
    async def join_roll(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        user_id = interaction.user.id
        if user_id not in participants:
            participants.add(user_id)
            logs.append(f"{interaction.user.name} {self.log_text[0]}")
            await send_or_edit_message(interaction.channel)

    @discord.ui.button(label="リセット", style=discord.ButtonStyle.danger)
    async def reset_participants(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        participants.clear()
        logs.append(self.log_text[1])
        await send_or_edit_message(interaction.channel)

    @discord.ui.button(label="ロール", style=discord.ButtonStyle.success)
    async def roll_dice(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        if not participants:
            return
        global roll_results
        roll_results = {user_id: random.randint(1, 100) for user_id in participants}
        logs.append(self.log_text[2])
        await send_or_edit_message(interaction.channel)

@bot.command(name="start", description="ダイスロールBotを開始します")
async def start_command(ctx):
    global flag
    global message_ids
    message_ids = load_message_ids()
    await delete_old_messages(ctx.channel, message_ids)
    if not flag:
        view = DiceRollView()
        button_message = await ctx.send("操作ボタン:", view=view)
        message_ids = [button_message.id]  # 操作ボタンメッセージを保存
        save_message_ids(message_ids)
        await send_or_edit_message(ctx.channel)
        flag = True
        await ctx.message.delete()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')
    global message_ids
    message_ids = load_message_ids()

bot.run(TOKEN)
