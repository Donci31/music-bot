import discord
from discord.ext import commands
from collections import defaultdict
import tempfile
import requests
import yt_dlp
import re


class MusicBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='-')
        self.song_queues = defaultdict(lambda: [])
        self.song_directory = tempfile.TemporaryDirectory()
        youtube_prefix = 'https://www.youtube.com/watch?v='

        @self.command()
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
            html = requests.get('https://www.youtube.com/results', params=search_query).text
            song_id = re.search(r'/(?:watch\?v=|shorts/)(\S{11})', html).group(1)

            ydl_opts = {
                'format': 'm4a/bestaudio/best',
                'outtmpl': f'{self.song_directory.name}/{song_id}.m4a'
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(f'{youtube_prefix}{song_id}')
                song_title = info_dict.get('title')

            self.song_queues[guild_id].append((song_id, song_title))

            desc = f'[{song_title}]({youtube_prefix}{song_id})'
            queued_message = discord.Embed(title='Song queued', description=desc)
            await ctx.channel.send(embed=queued_message)

            if not voice.is_playing():
                self.__start_playing(ctx)

        @self.command()
        async def queue(ctx):
            guild_id = ctx.guild.id

            if self.song_queues[guild_id]:
                numbered_list = '\n'.join([f'**{i})** [{song_title}]({youtube_prefix}{song_id})'
                                           for i, (song_id, song_title) in enumerate(self.song_queues[guild_id], 1)])
                queue_message = discord.Embed(title='Queue', description=numbered_list)
                await ctx.channel.send(embed=queue_message)

        @self.command()
        async def skip(ctx):
            voice = ctx.voice_client

            if voice is not None:
                voice.stop()

        @self.command()
        async def clear(ctx):
            guild_id = ctx.guild.id

            self.song_queues[guild_id].clear()

    def __start_playing(self, ctx):
        guild_id = ctx.guild.id

        if self.song_queues[guild_id]:
            voice = ctx.voice_client
            song_id, _ = self.song_queues[guild_id].pop(0)
            song_path = f'{self.song_directory.name}/{song_id}.m4a'

            voice.play(discord.FFmpegPCMAudio(song_path), after=lambda e: self.__start_playing(ctx))

    async def close(self):
        self.song_directory.cleanup()
        await super().close()


def main():
    bot = MusicBot()
    bot.run(INSERT_TOKEN_HERE)


if __name__ == '__main__':
    main()
