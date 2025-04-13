import discord
import json

# config.json ファイルから設定を読み込む
with open('config.json', 'r') as f:
    config = json.load(f)
    TOKEN = config.get('token')
    NOTIFICATION_CHANNEL_NAME = config.get('notification_channel_name')

# intentsの設定（Voice State Updateイベントを購読するために必要）
intents = discord.Intents.default()
intents.voice_states = True
intents.members = True  # メンバー情報も必要に応じて取得

client = discord.Client(intents=intents)

async def send_notification(guild, member, voice_channel, event_type):
    """指定されたテキストチャンネルに通知を送信する関数"""
    notification_channel = discord.utils.get(guild.text_channels, name=NOTIFICATION_CHANNEL_NAME)
    if notification_channel:
        if event_type == 'join':
            await notification_channel.send(f'📢 {member.display_name} がボイスチャンネル「{voice_channel.name}」に参加しました。')
        elif event_type == 'leave':
            await notification_channel.send(f'🔇 {member.display_name} がボイスチャンネル「{voice_channel.name}」から退出しました。')

@client.event
async def on_voice_state_update(member, before, after):
    """ボイスチャンネルの状態が更新された際に呼び出されるイベント"""
    if member.bot:
        return

    guild = member.guild

    # 参加時の処理
    if before.channel is None and after.channel is not None:
        await send_notification(guild, member, after.channel, 'join')

    # 退出時の処理
    elif before.channel is not None and after.channel is None:
        await send_notification(guild, member, before.channel, 'leave')

    # チャンネル移動時の処理 (必要であれば)
    elif before.channel != after.channel and after.channel is not None:
        await send_notification(guild, member, after.channel, 'join') # 移動先への参加通知
        await send_notification(guild, member, before.channel, 'leave') # 移動元からの退出通知

@client.event
async def on_ready():
    print(f'{client.user} としてログインしました')

client.run(TOKEN)