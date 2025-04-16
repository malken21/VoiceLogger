import discord
from discord.ext import commands
import json

# config.json ファイルから設定を読み込む (TOKENのみ使用)
with open('config.json', 'r') as f:
    config = json.load(f)
    TOKEN = config.get('token')

# intentsの設定（Voice State Updateイベントとメッセージコンテンツの読み取りを購読するために必要）
intents = discord.Intents.default()
intents.voice_states = True
intents.members = True
intents.message_content = True  # スラッシュコマンドを使用するために必要

bot = commands.Bot(command_prefix="/", intents=intents)

# サーバーごとの設定を保存する辞書
server_config = {}

# 設定ファイルのパス
CONFIG_FILE = 'server_config.json'

# 設定ファイルの読み込み
def load_config():
    global server_config
    try:
        with open(CONFIG_FILE, 'r') as f:
            server_config = json.load(f)
    except FileNotFoundError:
        server_config = {}
    except json.JSONDecodeError:
        server_config = {}
        print(f"警告: {CONFIG_FILE} の読み込みに失敗しました。空の設定で開始します。")

# 設定ファイルの保存
def save_config():
    with open(CONFIG_FILE, 'w') as f:
        json.dump(server_config, f, indent=4)

async def send_notification(guild_id, member, voice_channel, event_type):
    """指定されたテキストチャンネルに通知を送信する関数"""
    if guild_id in server_config and 'notification_channel_id' in server_config[guild_id]:
        notification_channel_id = server_config[guild_id]['notification_channel_id']
        notification_channel = bot.get_channel(notification_channel_id)
        if notification_channel:
            if event_type == 'join':
                await notification_channel.send(f'📢 {member.display_name} がボイスチャンネル「{voice_channel.name}」に参加しました。')
            elif event_type == 'leave':
                await notification_channel.send(f'🔇 {member.display_name} がボイスチャンネル「{voice_channel.name}」から退出しました。')

@bot.event
async def on_voice_state_update(member, before, after):
    """ボイスチャンネルの状態が更新された際に呼び出されるイベント"""
    if member.bot:
        return

    guild_id = member.guild.id

    # 設定が存在しない場合は何もしない
    if guild_id not in server_config or 'voice_channel_id' not in server_config[guild_id]:
        return

    monitored_voice_channel_id = server_config[guild_id]['voice_channel_id']

    # 参加時の処理
    if before.channel is None and after.channel is not None and after.channel.id == monitored_voice_channel_id:
        await send_notification(guild_id, member, after.channel, 'join')

    # 退出時の処理
    elif before.channel is not None and before.channel.id == monitored_voice_channel_id and after.channel is None:
        await send_notification(guild_id, member, before.channel, 'leave')

    # チャンネル移動時の処理 (監視対象チャンネルへの移動と監視対象チャンネルからの移動)
    elif before.channel is not None and after.channel is not None and before.channel.id != after.channel.id:
        if after.channel.id == monitored_voice_channel_id:
            await send_notification(guild_id, member, after.channel, 'join') # 移動先への参加通知
        elif before.channel.id == monitored_voice_channel_id:
            await send_notification(guild_id, member, before.channel, 'leave') # 移動元からの退出通知

@bot.tree.command(name="link", description="ログを記録するボイスチャンネルとテキストチャンネルを設定します。")
@discord.app_commands.guild_only()
async def link_channels(interaction: discord.Interaction, voice_channel: discord.VoiceChannel, text_channel: discord.TextChannel):
    """ボイスチャンネルとテキストチャンネルをリンクするコマンド"""
    guild_id = interaction.guild.id
    server_config[guild_id] = {
        'voice_channel_id': voice_channel.id,
        'notification_channel_id': text_channel.id
    }
    save_config()
    await interaction.response.send_message(f"ボイスチャンネル {voice_channel.mention} のログをテキストチャンネル {text_channel.mention} に記録するように設定しました。", ephemeral=True)

@bot.event
async def on_ready():
    print(f'{bot.user} としてログインしました')
    load_config()
    await bot.tree.sync() # スラッシュコマンドを同期

bot.run(TOKEN)