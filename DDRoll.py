import discord
from discord.ext import commands
import random





################################
################################
################################
TOKEN = ""
lang = "ja" # "en" or "ja"
################################
################################
################################




intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# メッセージIDの管理
message_id = None

# 情報の初期化
participants = set()
roll_results = {}
logs = []

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
    global message_id
    content = generate_message_content()
    if message_id:
        try:
            message = await channel.fetch_message(message_id)
            await message.edit(content=content)
        except discord.NotFound:
            message = await channel.send(content)
            message_id = message.id
    else:
        message = await channel.send(content)
        message_id = message.id

# ボタンのビューを定義
class DiceRollView(discord.ui.View):
    def __init__(self):
        super().__init__()

    button_label = []
    log_text = []
    if lang == "ja":
        button_label = ["ダイスロールに参加", "参加者リセット", "ダイスロール"]
        log_text = ["さんがダイスロールに参加しました。", "参加者リストをリセットしました。", "ダイスロールを実行しました。"]
    else:
        button_label = ["Join Roll", "Reset Participants", "Roll Dice"]
        log_text = ["Joined the dice roll.", "Reset the participants list.", "Executed the dice roll."]

    @discord.ui.button(label=button_label[0], style=discord.ButtonStyle.primary)
    async def join_roll(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        user_id = interaction.user.id
        if user_id not in participants:
            participants.add(user_id)
            logs.append(f"{interaction.user.name} {DiceRollView.log_text[0]}")
            await send_or_edit_message(interaction.channel)

    @discord.ui.button(label=button_label[1], style=discord.ButtonStyle.danger)
    async def reset_participants(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        participants.clear()
        logs.append(DiceRollView.log_text[1])
        await send_or_edit_message(interaction.channel)

    @discord.ui.button(label=button_label[2], style=discord.ButtonStyle.success)
    async def roll_dice(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        if not participants:
            return
        global roll_results
        roll_results = {user_id: random.randint(1, 100) for user_id in participants}
        logs.append(DiceRollView.log_text[2])
        await send_or_edit_message(interaction.channel)

    '''
    @discord.ui.button(label="全メッセージ削除", style=discord.ButtonStyle.secondary)
    async def delete_all_messages(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        global message_id
        if message_id:
            try:
                message = await interaction.channel.fetch_message(message_id)
                await message.delete()
            except discord.NotFound:
                pass
            message_id = None
        logs.append("全てのメッセージを削除しました。")
        flag = False
    '''


@bot.command(name="start", description="ダイスロールBotを開始します")
async def start_command(ctx):
    await start(ctx.channel)
    await ctx.message.delete()


@bot.tree.command(name="start", description="ダイスロールBotを開始します")
async def start_slash(interaction: discord.Interaction):
    await start(interaction.channel)
    await interaction.response.send_message("")

async def start(channel):
    global flag
    if not flag:
        view = DiceRollView()
        await channel.send("", view=view)
        await send_or_edit_message(channel)
        flag = True


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'Logged in as {bot.user}!')

bot.run(TOKEN)
