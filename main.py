import discord
from discord.ext import commands
from collections import defaultdict
import tempfile
import requests
import yt_dlp
import re

client = commands.Bot(command_prefix='-')

song_queues = defaultdict(lambda: [])


def start_playing(ctx):
    guild_id = ctx.guild.id

    if len(song_queues[guild_id]) > 0:
        voice = ctx.voice_client
        music = song_queues[guild_id].pop(0)

        voice.play(discord.FFmpegPCMAudio(music), after=lambda e: start_playing(ctx))


@client.command()
async def play(ctx, *, keyword):
    if ctx.author.voice is None:
        join_message = discord.Embed(description='**Join a voice channel!**')
        await ctx.channel.send(embed=join_message)
        return

    if ctx.voice_client is None:
        voice_channel = ctx.author.voice.channel
        await voice_channel.connect()

    voice = ctx.voice_client
    guild_id = ctx.guild.id

    search_query = {'search_query': keyword}
    html = requests.get(f'https://www.youtube.com/results', params=search_query).text
    video_id = re.search(r'watch\?v=(\S{11})', html).group(1)

    song_path = f'{tempdirname}/{video_id}.m4a'

    ydl_opts = {
        'format': 'm4a/bestaudio/best',
        'outtmpl': song_path
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(f'https://www.youtube.com/watch?v={video_id}')
        video_title = info_dict.get('title')

    song_queues[guild_id].append(song_path)

    desc = f'[{video_title}](https://www.youtube.com/watch?v={video_id})'
    queued_message = discord.Embed(title='Song queued', description=desc)
    await ctx.channel.send(embed=queued_message)

    if not voice.is_playing():
        start_playing(ctx)


@client.command()
async def queue(ctx):
    guild_id = ctx.guild.id

    if len(song_queues[guild_id]) > 0:
        numbered_list = '\n'.join([f'**{i + 1})** [{song[1]}](https://www.youtube.com/watch?v={song[0]})'
                                   for i, song in (enumerate(song_queues[guild_id]))])
        queue_message = discord.Embed(title='Queue', description=numbered_list)
        await ctx.channel.send(embed=queue_message)
    else:
        queue_message = discord.Embed(description='**There is nothing playing on this server**')
        await ctx.channel.send(embed=queue_message)


@client.command()
async def skip(ctx):
    voice = ctx.voice_client

    if voice is not None:
        voice.stop()


@client.command()
async def clear(ctx):
    guild_id = ctx.guild.id

    song_queues[guild_id].clear()


with tempfile.TemporaryDirectory() as tempdirname:
    client.run(INSERT_TOKEN_HERE)
