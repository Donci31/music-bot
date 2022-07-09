import discord
from discord.ext import commands
from collections import defaultdict
import tempfile
import requests
import yt_dlp
import re


class Chungus(commands.Bot):

    def __init__(self):
        super().__init__(command_prefix='-')
        self.song_queues = defaultdict(lambda: [])
        self.songs_folder = tempfile.TemporaryDirectory()

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
            video_id = re.search(r'/(?:watch\?v=|shorts/)(\S{11})', html).group(1)

            song_path = f'{self.songs_folder}/{video_id}.m4a'

            ydl_opts = {
                'format': 'm4a/bestaudio/best',
                'outtmpl': song_path
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(f'{youtube_prefix}{video_id}')
                video_title = info_dict.get('title')

            self.song_queues[guild_id].append((song_path, video_title))

            desc = f'[{video_title}]({youtube_prefix}{video_id})'
            queued_message = discord.Embed(title='Song queued', description=desc)
            await ctx.channel.send(embed=queued_message)

            if not voice.is_playing():
                self.start_playing(ctx)

        @self.command()
        async def queue(ctx):
            guild_id = ctx.guild.id

            if self.song_queues[guild_id]:
                numbered_list = '\n'.join([f'**{i + 1})** [{song[1]}]({youtube_prefix}{song[0]})'
                                           for i, song in (enumerate(self.song_queues[guild_id]))])
                queue_message = discord.Embed(title='Queue', description=numbered_list)
                await ctx.channel.send(embed=queue_message)
            else:
                queue_message = discord.Embed(description='**There is nothing playing on this server**')
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

    def start_playing(self, ctx):
        guild_id = ctx.guild.id

        if self.song_queues[guild_id]:
            voice = ctx.voice_client
            music = self.song_queues[guild_id].pop(0)

            voice.play(discord.FFmpegPCMAudio(music[0]), after=lambda e: self.start_playing(ctx))

    async def close(self):
        self.songs_folder.cleanup()
        await super().close()


def main():
    bot = Chungus()
    bot.run(INSERT_TOKEN_HERE)


if __name__ == '__main__':
    main()
