import os
from discord import FFmpegPCMAudio
from discord.ext import commands
from collections import defaultdict
from tempfile import TemporaryDirectory
from pytube import YouTube, Playlist

from musicbot import utils
from musicbot.utils import YOUTUBE_WATCH_REGEX, YOUTUBE_PLAYLIST_REGEX


class MusicBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='-')
        self.song_queues = defaultdict(lambda: [])
        self.song_directory = TemporaryDirectory()

        @self.command()
        async def play(ctx, *, keyword):
            if ctx.author.voice is None:
                await utils.send_embed(channel=ctx.channel, description='**Join a voice channel!**')
                return

            if ctx.voice_client is None or not ctx.voice_client.is_connected():
                voice_channel = ctx.author.voice.channel
                await voice_channel.connect()

            youtube_playlist_match = YOUTUBE_PLAYLIST_REGEX.fullmatch(keyword)

            if youtube_playlist_match:
                playlist = Playlist(youtube_playlist_match.group(0))
                await self._add_playlist(ctx, playlist)
            else:
                youtube_link_match = YOUTUBE_WATCH_REGEX.fullmatch(keyword)

                if youtube_link_match:
                    song_id = youtube_link_match.group(1)
                else:
                    song_id = utils.keyword_search(keyword)

                song = YouTube(utils.get_song_url(song_id))
                await self._add_song(ctx, song)

        @self.command()
        async def queue(ctx):
            guild_id = ctx.guild.id
            channel = ctx.channel

            if self.song_queues[guild_id]:
                numbered_list = '\n'.join([f'**{i})** [{song.title}]({utils.get_song_url(song.video_id)}) '
                                           f'``{utils.time_format(song.length)}``'
                                           for i, song in enumerate(self.song_queues[guild_id][:10], 1)])
                await utils.send_embed(channel=channel, title='Queue', description=numbered_list)

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
            guild_id = ctx.guild.id
            voice = ctx.voice_client

            self.song_queues[guild_id].clear()
            if voice is not None:
                voice.stop()

    async def _add_playlist(self, ctx, playlist):
        channel = ctx.channel
        guild_id = ctx.guild.id
        voice = ctx.voice_client

        desc = (f'[{playlist.title}]({playlist.playlist_url}) | queued **15** songs '
                f'``{utils.time_format(sum(video.length for video in playlist.videos))}``')
        await utils.send_embed(channel=channel, title='Playlist queued', description=desc)

        self.song_queues[guild_id].extend(playlist.videos)

        if not voice.is_playing():
            self._start_playing(voice, guild_id)

    async def _add_song(self, ctx, song):
        channel = ctx.channel
        guild_id = ctx.guild.id
        voice = ctx.voice_client

        desc = (f'[{song.title}]({utils.get_song_url(song.video_id)}) '
                f'``{utils.time_format(song.length)}``')
        await utils.send_embed(channel=channel, title='Song queued', description=desc)

        self.song_queues[guild_id].append(song)

        if not voice.is_playing():
            self._start_playing(voice, guild_id)

    def _download_song(self, video):
        song = video.streams.filter(only_audio=True).first()
        song.download(output_path=self.song_directory.name, filename=f'{video.video_id}.mp4')
        return os.path.join(self.song_directory.name, f'{video.video_id}.mp4')

    def _start_playing(self, voice, guild_id):
        if self.song_queues[guild_id]:
            new_song = self.song_queues[guild_id].pop(0)
            song_path = self._download_song(new_song)

            voice.play(FFmpegPCMAudio(song_path), after=lambda e: self._start_playing(voice, guild_id))

    async def close(self):
        self.song_directory.cleanup()
        await super().close()
