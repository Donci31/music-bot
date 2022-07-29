import discord
from discord.ext import commands
from collections import defaultdict
from tempfile import TemporaryDirectory
from pytube import YouTube, Playlist

import utils
from utils import YOUTUBE_WATCH_REGEX, YOUTUBE_PLAYLIST_REGEX
from Song import Song


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

            voice = ctx.voice_client
            guild_id = ctx.guild.id
            channel = ctx.channel

            youtube_playlist_match = YOUTUBE_PLAYLIST_REGEX.match(keyword)

            if youtube_playlist_match:
                playlist = Playlist(youtube_playlist_match.group(0))
                await self._add_playlist(guild_id, voice, channel, playlist)
            else:
                youtube_link_match = YOUTUBE_WATCH_REGEX.match(keyword)

                if youtube_link_match:
                    song_id = youtube_link_match.group(1)
                else:
                    song_id = utils.keyword_search(keyword)

                video = YouTube(utils.get_link(song_id))
                await self._add_song(guild_id, voice, channel, video)

        @self.command()
        async def queue(ctx):
            guild_id = ctx.guild.id
            channel = ctx.channel

            if self.song_queues[guild_id]:
                numbered_list = '\n'.join([f'**{i})** [{song.song_title}]({utils.get_link(song.song_id)})'
                                           for i, song in enumerate(self.song_queues[guild_id], 1)])
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

        @self.command()
        async def stop(ctx):
            await clear(ctx)
            await skip(ctx)

    async def _add_playlist(self, guild_id, voice, channel, playlist):
        desc = f'**{playlist.length}** songs queued from playlist [{playlist.title}]({playlist.playlist_url})'
        queued_message = discord.Embed(title='Songs queued', description=desc)
        await channel.send(embed=queued_message)

        for video in playlist.videos:
            utils.download_song(video, path=self.song_directory.name)
            new_song = Song(voice, video.video_id, video.title)
            self._add_to_queue(guild_id, new_song)

    async def _add_song(self, guild_id, voice, channel, video):
        utils.download_song(video, path=self.song_directory.name)
        new_song = Song(voice, video.video_id, video.title)

        desc = f'[{new_song.song_title}]({utils.get_link(new_song.song_id)})'
        queued_message = discord.Embed(title='Song queued', description=desc)
        await channel.send(embed=queued_message)

        self._add_to_queue(guild_id, new_song)

    def _add_to_queue(self, guild_id, new_song):
        self.song_queues[guild_id].append(new_song)
        voice = new_song.voice

        if not voice.is_playing():
            self._start_playing(guild_id)

    def _start_playing(self, guild_id):
        if self.song_queues[guild_id]:
            new_song = self.song_queues[guild_id].pop(0)
            song_path = f'{self.song_directory.name}/{new_song.song_id}.mp4'
            voice = new_song.voice

            voice.play(discord.FFmpegPCMAudio(song_path), after=lambda e: self._start_playing(guild_id))

    async def close(self):
        self.song_directory.cleanup()
        await super().close()
