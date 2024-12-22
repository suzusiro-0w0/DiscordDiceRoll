import discord
from discord.ext import commands
import random
import atexit

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# 参加者リストの初期化
participants = set()

# メッセージIDの管理
message_ids = {
    'buttons': None,
    'participants': None,
    'results': None
}

# ボタンのビューを定義
class DiceRollView(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="ダイスロールに参加", style=discord.ButtonStyle.primary)
    async def join_roll(self, button: discord.ui.Button, interaction: discord.Interaction):
        user_id = interaction.user.id
        if user_id not in participants:
            participants.add(user_id)
            await update_participants_message(interaction.channel)
            await interaction.response.send_message(f"{interaction.user.name} さんがダイスロールに参加しました。", ephemeral=True)
        else:
            await interaction.response.send_message(f"{interaction.user.name} さんは既に参加しています。", ephemeral=True)

    @discord.ui.button(label="参加リセット", style=discord.ButtonStyle.danger)
    async def reset_participants(self, button: discord.ui.Button, interaction: discord.Interaction):
        participants.clear()
        await update_participants_message(interaction.channel)
        await interaction.response.send_message("参加者リストをリセットしました。", ephemeral=True)

    @discord.ui.button(label="ダイスロール", style=discord.ButtonStyle.success)
    async def roll_dice(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not participants:
            await interaction.response.send_message("参加者がいません。", ephemeral=True)
            return

        roll_results = {user_id: random.randint(1, 100) for user_id in participants}
        await update_results_message(interaction.channel, roll_results)
        await interaction.response.send_message("ダイスロールを実行しました。", ephemeral=True)

    @discord.ui.button(label="全メッセージ削除", style=discord.ButtonStyle.secondary)
    async def delete_all_messages(self, button: discord.ui.Button, interaction: discord.Interaction):
        await delete_all_managed_messages(interaction.channel)
        await interaction.response.send_message("全てのメッセージを削除しました。", ephemeral=True)

# メッセージの更新関数
async def update_participants_message(channel):
    content = "参加者一覧:\n" + "\n".join([f"<@{user_id}>" for user_id in participants]) if participants else "参加者はいません。"
    await send_or_edit_message(channel, 'participants', content)

async def update_results_message(channel, roll_results):
    content = "ダイスロールの結果:\n" + "\n".join([f"<@{user_id}>: {roll}" for user_id, roll in roll_results.items()])
    await send_or_edit_message(channel, 'results', content)

# メッセージの送信または編集
async def send_or_edit_message(channel, message_type, content):
    message_id = message_ids.get(message_type)
    if message_id:
        try:
            message = await channel.fetch_message(message_id)
            await message.edit(content=content)
        except discord.NotFound:
            message = await channel.send(content)
            message_ids[message_type] = message.id
    else:
        message = await channel.send(content)
        message_ids[message_type] = message.id

# 全メッセージの削除
async def delete_all_managed_messages(channel):
    for key, message_id in message_ids.items():
        if message_id:
            try:
                message = await channel.fetch_message(message_id)
                await message.delete()
            except discord.NotFound:
                pass
            message_ids[key] = None

# コマンドで初期化
@bot.command()
async def start(ctx):
    view = DiceRollView()
    buttons_message = await ctx.send("操作ボタン:", view=view)
    message_ids['buttons'] = buttons_message.id
    await update_participants_message(ctx.channel)
    await update_results_message(ctx.channel, {})

# プログラム終了時に全メッセージを削除
def on_exit():
    loop = bot.loop
    if loop.is_running():
        loop.create_task(delete_all_managed_messages(bot.get_channel(CHANNEL_ID)))

atexit.register(on_exit)

bot.run('YOUR_BOT_TOKEN')
