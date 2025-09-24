import time
from collections import defaultdict

import discord
from discord import VoiceClient
from discord.ext import commands
from discord.ext.commands import Context
from pytubefix import Playlist, YouTube

import musicbot
from musicbot import utils


class MusicBot(commands.Bot):
    def __init__(self, prefix: str) -> None:
        intents = discord.Intents(
            guilds=True,
            guild_messages=True,
            message_content=True,
            voice_states=True,
        )
        super().__init__(command_prefix=prefix, intents=intents)

        self.song_queues = defaultdict[int, list[YouTube]](list)
        self.song_indexes = defaultdict[int, int](int)
        self.cur_songs = defaultdict[int, tuple[YouTube, int] | None](lambda: None)
        self.loop_queue = defaultdict[int, bool](bool)

    async def setup_hook(self) -> None:
        await self.add_cog(musicbot.MusicCommands(self))
        await self.tree.sync()

    async def add_playlist(self, ctx: Context, playlist: Playlist) -> None:
        guild_id = ctx.guild.id

        self.song_queues[guild_id].extend(playlist.videos)
        total_length = sum(video.length for video in playlist.videos)

        embed = (
            discord.Embed(
                title=f"📚 Playlist Queued: {playlist.title}",
                url=playlist.playlist_url,
                color=discord.Color.blurple(),
                description=(
                    f"**{len(playlist)} songs added**\n"
                    f"**Total Duration:** `{utils.time_format(total_length)}`"
                ),
            )
            .set_thumbnail(url=playlist.thumbnail_url)
            .set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar)
            .set_footer(text="Powered by Chungus", icon_url=utils.CHUNGUS_ICON)
        )

        await ctx.send(embed=embed)

    async def add_song(self, ctx: Context, song: YouTube) -> None:
        guild_id = ctx.guild.id
        self.song_queues[guild_id].append(song)

        embed = (
            discord.Embed(
                title=f"🎵 Queued - at position #{len(self.song_queues[guild_id])}",
                color=discord.Color.blurple(),
                description=f"[{song.title}]({song.watch_url}) by "
                f"[{song.author}]({song.channel_url}) "
                f"`{utils.time_format(song.length)}`",
            )
            .set_thumbnail(url=song.thumbnail_url)
            .set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar)
            .set_footer(text="Powered by Chungus", icon_url=utils.CHUNGUS_ICON)
        )

        await ctx.reply(embed=embed)

    def start_playing(self, guild_id: int, voice: VoiceClient) -> None:
        cur_index = self.song_indexes[guild_id]
        cur_queue = self.song_queues[guild_id]

        if cur_index < len(cur_queue):
            stream_url = cur_queue[cur_index].streams.get_audio_only(subtype="webm").url
            self.song_indexes[guild_id] += 1
            self.cur_songs[guild_id] = (cur_queue[cur_index], round(time.time()))

            before_options = (
                "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -nostdin"
            )

            after_options = "-vn -sn -dn -bufsize 64k"

            ffmpeg_options = {
                "codec": "copy",
                "before_options": before_options,
                "options": after_options,
            }

            voice.play(
                discord.FFmpegOpusAudio(stream_url, **ffmpeg_options),
                after=lambda _: self.start_playing(guild_id, voice),
            )
        elif self.loop_queue[guild_id]:
            self.song_indexes[guild_id] = 0
            self.start_playing(guild_id, voice)
        else:
            self.cur_songs[guild_id] = None
