import discord
import re
import requests
from discord.ext import commands
from collections import defaultdict
from os import environ
from dotenv import load_dotenv
from tempfile import TemporaryDirectory
from yt_dlp import YoutubeDL


YOUTUBE_WATCH = 'https://www.youtube.com/watch?v='


class MusicBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='-')
        self.song_queues = defaultdict(lambda: [])
        self.song_directory = TemporaryDirectory()

        @self.command()
        async def play(ctx, *, keyword):
            if ctx.author.voice is None:
                join_message = discord.Embed(description='**Join a voice channel!**')
                await ctx.channel.send(embed=join_message)
                return

            if ctx.voice_client is None:
                voice_channel = ctx.author.voice.channel
                await voice_channel.connect()

            search_query = {'search_query': keyword}
            html = requests.get('https://www.youtube.com/results', params=search_query).text
            song_id = re.search(r'/(?:watch\?v=|shorts/)([^"]+)', html).group(1)

            voice = ctx.voice_client
            guild_id = ctx.guild.id
            channel = ctx.channel

            ydl_opts = {
                'ignoreerrors': True,
                'format': 'm4a/bestaudio/best',
                'outtmpl': f'{self.song_directory.name}/{song_id}.m4a'
            }

            with YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(f'{YOUTUBE_WATCH}{song_id}')
                song_title = info_dict.get('title')

            self.song_queues[guild_id].append((song_id, song_title))

            desc = f'[{song_title}]({YOUTUBE_WATCH}{song_id})'
            queued_message = discord.Embed(title='Song queued', description=desc)
            await channel.send(embed=queued_message)

            if not voice.is_playing():
                self._start_playing(guild_id, voice)

        @self.command()
        async def queue(ctx):
            guild_id = ctx.guild.id
            channel = ctx.channel

            if self.song_queues[guild_id]:
                numbered_list = '\n'.join([f'**{i})** [{song_title}]({YOUTUBE_WATCH}{song_id})'
                                           for i, (song_id, song_title) in enumerate(self.song_queues[guild_id], 1)])
                queue_message = discord.Embed(title='Queue', description=numbered_list)
                await channel.send(embed=queue_message)

        @self.command()
        async def skip(ctx):
            voice = ctx.voice_client

            if voice is not None:
                voice.stop()

        @self.command()
        async def clear(ctx):
            guild_id = ctx.guild.id

            self.song_queues[guild_id].clear()

    def _start_playing(self, guild_id, voice):
        if self.song_queues[guild_id]:
            song_id, _ = self.song_queues[guild_id].pop(0)
            song_path = f'{self.song_directory.name}/{song_id}.m4a'

            voice.play(discord.FFmpegPCMAudio(song_path), after=lambda e: self._start_playing(guild_id, voice))

    async def close(self):
        self.song_directory.cleanup()
        await super().close()


def main():
    load_dotenv()
    token = environ['BOT_TOKEN']
    bot = MusicBot()
    bot.run(token)


if __name__ == '__main__':
    main()
