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

                video = YouTube(utils.get_url(song_id))
                await self._add_song(ctx, video)

        @self.command()
        async def queue(ctx):
            guild_id = ctx.guild.id
            channel = ctx.channel

            if self.song_queues[guild_id]:
                numbered_list = '\n'.join([f'**{i})** [{song.title}]({utils.get_url(song.video_id)}) '
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
        voice = ctx.voice_client
        guild_id = ctx.guild.id
        channel = ctx.channel

        desc = (f'**{playlist.length}** songs queued from playlist [{playlist.title}]({playlist.playlist_url}) '
                f'``{utils.time_format(sum(video.length for video in playlist.videos))}``')
        await utils.send_embed(channel=channel, title='Songs queued', description=desc)

        for video in playlist.videos:
            self._add_to_queue(voice, guild_id, video)

    async def _add_song(self, ctx, video):
        voice = ctx.voice_client
        guild_id = ctx.guild.id
        channel = ctx.channel

        desc = (f'[{video.title}]({utils.get_url(video.video_id)}) '
                f'``{utils.time_format(video.length)}``')
        await utils.send_embed(channel=channel, title='Song queued', description=desc)

        self._add_to_queue(voice, guild_id, video)

    def _add_to_queue(self, voice, guild_id, new_song):
        self.song_queues[guild_id].append(new_song)

        if not voice.is_playing():
            self._start_playing(voice, guild_id)

    def _start_playing(self, voice, guild_id):
        if self.song_queues[guild_id]:
            new_song = self.song_queues[guild_id].pop(0)
            utils.download_song(new_song, self.song_directory.name)
            song_path = f'{self.song_directory.name}/{new_song.video_id}.mp4'

            voice.play(FFmpegPCMAudio(song_path), after=lambda e: self._start_playing(voice, guild_id))

    async def close(self):
        self.song_directory.cleanup()
        await super().close()
