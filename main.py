import discord
from discord.ext import commands
import tempfile
import requests
import yt_dlp
import re

client = commands.Bot(command_prefix='-')

queues = {}


def start_playing(ctx):
    guild_id = ctx.guild.id

    if len(queues[guild_id]) > 0:
        voice = ctx.guild.voice_client
        source = queues[guild_id].pop(0)

        client.loop.create_task(ctx.channel.send(f'Now playing: \U0001F3B5 **{source[1]}**'))
        voice.play(discord.FFmpegPCMAudio(source[0]), after=lambda e: start_playing(ctx))


@client.command()
async def play(ctx, *, keyword):
    if ctx.author.voice is None:
        await ctx.channel.send('Join a voice channel!')
        return

    voice_channel = ctx.author.voice.channel

    if ctx.voice_client is None:
        await voice_channel.connect()
    elif ctx.voice_client.channel != voice_channel:
        ctx.voice_client.disconnect()
        await voice_channel.connect()

    voice = ctx.guild.voice_client
    guild_id = ctx.guild.id

    search_keyword = keyword.replace(' ', '+')
    html = requests.get(f'https://www.youtube.com/results?search_query={search_keyword}').text
    video_id = re.search(r'watch\?v=(\S{11})', html).group(1)

    template_name = f'{tempdirname}/{video_id}.m4a'

    ydl_opts = {
        'format': 'm4a/bestaudio/best',
        'outtmpl': template_name
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(f'https://www.youtube.com/watch?v={video_id}')
        video_title = info_dict.get('title')

    if guild_id in queues:
        queues[guild_id].append((template_name, video_title))
    else:
        queues[guild_id] = [(template_name, video_title)]

    if not voice.is_playing():
        start_playing(ctx)


@client.command()
async def skip(ctx):
    voice = ctx.guild.voice_client
    voice.stop()


@client.command()
async def clear(ctx):
    queues[ctx.guild.id].clear()


with tempfile.TemporaryDirectory() as tempdirname:
    client.run(INSERT_TOKEN_HERE)
