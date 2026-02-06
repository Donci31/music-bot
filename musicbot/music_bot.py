import asyncio
import time
from asyncio import Task
from collections import defaultdict

import discord
from discord import VoiceClient
from discord.ext.commands import Bot, Context
from pytubefix import Playlist, YouTube

import musicbot.music_commands as mc
import musicbot.utils as mu


class MusicBot(Bot):
    def __init__(self, prefix: str) -> None:
        intents = discord.Intents(
            guilds=True,
            guild_messages=True,
            message_content=True,
            voice_states=True,
        )
        super().__init__(command_prefix=prefix, intents=intents)

        self.song_queues = defaultdict[int, list[YouTube]](list)
        self.song_indexes = defaultdict[int, int](lambda: -1)
        self.cur_songs = defaultdict[int, YouTube | None](lambda: None)

        self.progress_time = defaultdict[int, float](float)
        self.pause_time = defaultdict[int, float](float)

        self.loop_queue = defaultdict[int, bool](bool)
        self.idle_checkers = defaultdict[int, Task[None] | None](lambda: None)

        self.timeout_second = 5 * 60

    async def setup_hook(self) -> None:
        await self.add_cog(mc.MusicCommands(self))
        await self.tree.sync()

    async def add_playlist(self, ctx: Context, playlist: Playlist) -> None:
        self.song_queues[mu.get_guild_id(ctx)].extend(playlist.videos)

        await ctx.send(
            embed=mu.make_embed(
                ctx=ctx,
                title=f"🎶 Playlist Queued: {playlist.title}",
                description=f"**{playlist.length} songs added**",
                embed_url=playlist.playlist_url,
                thumbnail_url=playlist.thumbnail_url,
            ),
        )

    async def add_song(self, ctx: Context, song: YouTube) -> None:
        guild_id = mu.get_guild_id(ctx)
        self.song_queues[guild_id].append(song)

        await ctx.send(
            embed=mu.make_embed(
                ctx=ctx,
                title=f"🎵 Queued - at position #{len(self.song_queues[guild_id])}",
                description=f"[{song.title}]({song.watch_url}) by "
                f"[{song.author}]({song.channel_url}) "
                f"`{mu.time_format(song.length)}`",
                thumbnail_url=song.thumbnail_url,
            ),
        )

    async def idle_checker(self, guild_id: int, voice: VoiceClient) -> None:
        await asyncio.sleep(self.timeout_second)
        if self.cur_songs[guild_id] is None and not voice.is_playing():
            await voice.disconnect()

    def start_playing(self, guild_id: int, voice: VoiceClient) -> None:
        cur_queue = self.song_queues[guild_id]

        if self.song_indexes[guild_id] + 1 >= len(cur_queue):
            if not self.loop_queue[guild_id]:
                self.cur_songs[guild_id] = None

                prev_task = self.idle_checkers[guild_id]
                if prev_task and not prev_task.done():
                    prev_task.cancel()

                self.idle_checkers[guild_id] = self.loop.create_task(
                    self.idle_checker(guild_id, voice),
                )
                return

            self.song_indexes[guild_id] = -1

        self.song_indexes[guild_id] += 1

        cur_song = cur_queue[self.song_indexes[guild_id]]

        self.cur_songs[guild_id] = cur_song
        self.progress_time[guild_id] = time.monotonic()
        self.pause_time[guild_id] = 0.0
        song_streams = cur_song.streams

        if song_audio := song_streams.get_audio_only(subtype="webm"):
            codec = "copy"
        else:
            song_audio = song_streams.get_audio_only(subtype="mp4")
            codec = "libopus"

        if not song_audio:
            self.start_playing(guild_id, voice)
            return

        voice.play(
            source=discord.FFmpegOpusAudio(
                source=song_audio.url,
                bitrate=voice.channel.bitrate // 1000,
                codec=codec,
                before_options="-reconnect 1 -reconnect_streamed 1 "
                "-reconnect_delay_max 5 -nostdin",
                options="-vn -sn -dn",
            ),
            after=lambda _: self.start_playing(guild_id, voice),
        )
