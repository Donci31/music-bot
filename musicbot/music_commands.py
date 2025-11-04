import math
import random
import time
from typing import TYPE_CHECKING, cast

import discord
from discord.ext import commands
from discord.ext.commands import Cog, Context
from pytubefix import Playlist, Search, YouTube

import musicbot.utils as mu

if TYPE_CHECKING:
    from .music_bot import MusicBot


class MusicCommands(Cog):
    def __init__(self, bot: MusicBot) -> None:
        self.bot = bot

    @commands.hybrid_command(description="Play a song or playlist from YouTube")
    @discord.app_commands.describe(song="The YouTube link or search query")
    @mu.handle_voice_channel_join
    async def play(self, ctx: Context, *, song: str) -> None:
        await ctx.defer()

        if playlist_match := mu.YOUTUBE_PLAYLIST_REGEX.fullmatch(song):
            playlist_id = playlist_match.group("playlist_id")
            playlist = Playlist(
                f"https://www.youtube.com/playlist?list={playlist_id}",
            )
            await self.bot.add_playlist(ctx, playlist)

        elif youtube_match := mu.YOUTUBE_WATCH_REGEX.fullmatch(song):
            song_id = youtube_match.group("youtube_id")
            youtube_song = YouTube(f"https://www.youtube.com/watch?v={song_id}")
            await self.bot.add_song(ctx, youtube_song)

        else:
            youtube_song = Search(song).videos[0]
            await self.bot.add_song(ctx, youtube_song)

    @commands.hybrid_command(
        description="Show the current music queue with page selector",
    )
    @discord.app_commands.describe(page_number="The page number to view")
    @mu.handle_index_errors
    async def queue(self, ctx: Context, page_number: int | None = None) -> None:
        await ctx.defer()

        guild_id = mu.get_guild_id(ctx)
        now_playing = self.bot.cur_songs[guild_id]
        queue = self.bot.song_queues[guild_id]

        if not now_playing and not queue:
            await ctx.send(
                embed=mu.make_embed(
                    ctx=ctx,
                    title="⚠️ No song is currently playing.",
                ),
            )
            return

        embed = mu.make_embed(
            ctx=ctx,
            title="🎶 Chungus Queue",
        )

        if now_playing:
            embed.add_field(
                name="Now Playing",
                value=(
                    f"▶️ [{now_playing.title}]({now_playing.watch_url}) "
                    f"`{mu.time_format(now_playing.length)}`"
                ),
                inline=False,
            ).set_thumbnail(url=now_playing.thumbnail_url)

        if queue:
            cur_page_number, len_pages, cur_page = mu.get_queue_page(
                queue=queue,
                current_index=self.bot.song_indexes[guild_id],
                page_number=page_number,
            )

            embed.add_field(
                name=f"Queue Page {cur_page_number}/{len_pages}",
                value=cur_page,
                inline=False,
            )

        await ctx.send(
            embed=embed,
        )

    @commands.hybrid_command(description="Skip the current song")
    async def skip(self, ctx: Context) -> None:
        if voice := cast("discord.VoiceClient", ctx.voice_client):
            voice.stop()

        await ctx.send(
            embed=mu.make_embed(
                ctx=ctx,
                title="👌 Skipped",
            ),
        )

    @commands.hybrid_command(description="Clear the queue")
    async def clear(self, ctx: Context) -> None:
        guild_id = mu.get_guild_id(ctx)

        self.bot.song_queues[guild_id].clear()
        self.bot.song_indexes[guild_id] = -1

        await ctx.send(
            embed=mu.make_embed(
                ctx=ctx,
                title="🧹 Queue cleared",
            ),
        )

    @commands.hybrid_command(description="Jump to a specific song in the queue")
    @discord.app_commands.describe(
        song_position="The position of the song in the queue",
    )
    @mu.handle_voice_channel_join
    @mu.handle_index_errors
    async def jump(self, ctx: Context, *, song_position: str) -> None:
        song_index = int(song_position) - 1
        guild_id = mu.get_guild_id(ctx)

        song = self.bot.song_queues[guild_id][song_index]
        self.bot.song_indexes[guild_id] = song_index - 1

        if voice := cast("discord.VoiceClient", ctx.voice_client):
            voice.stop()

        await ctx.send(
            embed=mu.make_embed(
                ctx=ctx,
                title=f"⏩ Jumped to song #{song_position}",
                description=f"[{song.title}]({song.watch_url})",
            ),
        )

    @commands.hybrid_command(description="Loop the queue")
    async def loop(self, ctx: Context) -> None:
        self.bot.loop_queue[mu.get_guild_id(ctx)] = True

        await ctx.send(
            embed=mu.make_embed(
                ctx=ctx,
                title="🔁 Now looping the queue",
            ),
        )

    @commands.hybrid_command(description="Disable queue looping")
    async def unloop(self, ctx: Context) -> None:
        self.bot.loop_queue[mu.get_guild_id(ctx)] = False

        await ctx.send(
            embed=mu.make_embed(
                ctx=ctx,
                title="🔁❌ Looping is now disabled",
            ),
        )

    @commands.hybrid_command(description="Pause the current song")
    async def pause(self, ctx: Context) -> None:
        if voice := cast("discord.VoiceClient", ctx.voice_client):
            voice.pause()

        guild_id = mu.get_guild_id(ctx)

        if not self.bot.pause_time[guild_id]:
            self.bot.pause_time[guild_id] = time.monotonic()

        await ctx.send(
            embed=mu.make_embed(
                ctx=ctx,
                title="⏸️ Paused",
            ),
        )

    @commands.hybrid_command(description="Resume the current song")
    async def unpause(self, ctx: Context) -> None:
        if voice := cast("discord.VoiceClient", ctx.voice_client):
            voice.resume()

        guild_id = mu.get_guild_id(ctx)

        self.bot.progress_time[guild_id] += (
            time.monotonic() - self.bot.pause_time[guild_id]
        )
        self.bot.pause_time[guild_id] = 0.0

        await ctx.send(
            embed=mu.make_embed(
                ctx=ctx,
                title="▶️ Resumed",
            ),
        )

    @commands.hybrid_command(description="Remove a song from the queue")
    @discord.app_commands.describe(
        song_position="The position of the song in the queue",
    )
    @mu.handle_index_errors
    async def remove(self, ctx: Context, *, song_position: str) -> None:
        song_index = int(song_position) - 1
        song = self.bot.song_queues[mu.get_guild_id(ctx)].pop(song_index)

        await ctx.send(
            embed=mu.make_embed(
                ctx=ctx,
                title=f"🗑️ Removed song #{song_position}",
                description=f"[{song.title}]({song.watch_url})",
            ),
        )

    @commands.hybrid_command(description="Shuffle the queue")
    async def shuffle(self, ctx: Context) -> None:
        random.shuffle(self.bot.song_queues[mu.get_guild_id(ctx)])

        await ctx.send(
            embed=mu.make_embed(
                ctx=ctx,
                title="🔀 Queue shuffled",
            ),
        )

    @commands.hybrid_command(description="Stop playing and clear the queue")
    async def stop(self, ctx: Context) -> None:
        guild_id = mu.get_guild_id(ctx)

        self.bot.song_queues[guild_id].clear()
        self.bot.song_indexes[guild_id] = -1
        if voice := cast("discord.VoiceClient", ctx.voice_client):
            voice.stop()

        await ctx.send(
            embed=mu.make_embed(
                ctx=ctx,
                title="🛑 Stopped and cleared queue",
            ),
        )

    @commands.hybrid_command(description="Move a song to another position in the queue")
    @discord.app_commands.describe(current_position="The current position of the song")
    @discord.app_commands.describe(new_position="The new position in the queue")
    @mu.handle_index_errors
    async def move(
        self,
        ctx: Context,
        current_position: str,
        *,
        new_position: str,
    ) -> None:
        first_index = int(current_position) - 1
        second_index = int(new_position) - 1
        song_queue = self.bot.song_queues[mu.get_guild_id(ctx)]

        song = song_queue.pop(first_index)
        song_queue.insert(second_index, song)

        await ctx.send(
            embed=mu.make_embed(
                ctx=ctx,
                title=f"↕️ Moved song #{current_position} to #{new_position}",
                description=f"[{song.title}]({song.watch_url})",
            ),
        )

    @commands.hybrid_command(description="Show detailed info about the current song")
    async def info(self, ctx: Context) -> None:
        guild_id = mu.get_guild_id(ctx)

        if not (now_playing := self.bot.cur_songs[guild_id]):
            await ctx.send(
                embed=mu.make_embed(
                    ctx=ctx,
                    title="⚠️ No song is currently playing.",
                ),
            )
            return

        progress = math.floor(
            time.monotonic()
            - self.bot.progress_time[guild_id]
            - (
                time.monotonic() - self.bot.pause_time[guild_id]
                if self.bot.pause_time[guild_id]
                else 0.0
            ),
        )
        total_length = now_playing.length or 0

        uploader = f"[{now_playing.author}]({now_playing.channel_url})"
        duration_string = f"{mu.time_format(progress)} / {mu.time_format(total_length)}"
        progress_bar = mu.create_progress_bar(
            progress=progress,
            total_length=total_length,
        )
        loop_status = "🔁 Queue Looping" if self.bot.loop_queue[guild_id] else "No Loop"

        await ctx.send(
            embed=mu.make_embed(
                ctx=ctx,
                title=now_playing.title,
                description=(
                    f"**Uploader:** {uploader}\n"
                    f"**Duration:** `{duration_string}`\n"
                    f"**Progress:** `{progress_bar}`\n"
                    f"**Loop Status:** {loop_status}"
                ),
                embed_url=f"{now_playing.watch_url}&t={progress}",
                thumbnail_url=now_playing.thumbnail_url,
            ),
        )
