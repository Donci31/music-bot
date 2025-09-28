import random
import time
from typing import cast

import discord
from discord.ext import commands
from discord.ext.commands import Context
from pytubefix import Playlist, Search, YouTube

import musicbot
from musicbot import utils
from musicbot.utils import (
    YOUTUBE_PLAYLIST_REGEX,
    YOUTUBE_WATCH_REGEX,
    make_embed,
    split_to_pages,
    time_format,
)


class MusicCommands(commands.Cog):
    def __init__(self, bot: musicbot.MusicBot) -> None:
        self.bot = bot

    @commands.hybrid_command(description="Play a song or playlist from YouTube")
    @discord.app_commands.describe(song="The YouTube link or search query")
    async def play(self, ctx: Context, *, song: str) -> None:
        guild_id = ctx.guild.id
        voice = cast("discord.VoiceClient", ctx.voice_client)

        if ctx.author.voice is None:
            await ctx.send(embed=make_embed(ctx, "**Join a voice channel!**"))
            return

        if voice is None or not voice.is_connected():
            voice = await ctx.author.voice.channel.connect()

        await ctx.defer()

        match song:
            case s if playlist_match := YOUTUBE_PLAYLIST_REGEX.fullmatch(s):
                playlist_id = playlist_match.group("playlist_id")
                playlist = Playlist(
                    f"https://www.youtube.com/playlist?list={playlist_id}",
                )
                await self.bot.add_playlist(ctx, playlist)

            case s if youtube_match := YOUTUBE_WATCH_REGEX.fullmatch(s):
                song_id = youtube_match.group("youtube_id")
                youtube_song = YouTube(f"https://www.youtube.com/watch?v={song_id}")
                await self.bot.add_song(ctx, youtube_song)

            case _:
                youtube_song = Search(song).videos[0]
                await self.bot.add_song(ctx, youtube_song)

        if not voice.is_playing():
            self.bot.start_playing(guild_id, voice)

    @commands.hybrid_command(
        description="Show the current music queue with page selector",
    )
    @discord.app_commands.describe(page_number="The page number to view")
    async def queue(self, ctx: Context, page_number: int | None = None) -> None:
        default_per_page = 10

        await ctx.defer()

        queue = self.bot.song_queues[ctx.guild.id]

        now_playing = (
            self.bot.cur_songs[ctx.guild.id][0]
            if self.bot.cur_songs[ctx.guild.id]
            else None
        )

        if not queue and now_playing is None:
            await ctx.send(embed=make_embed(ctx, "❌ No songs currently playing."))
            return

        embed = make_embed(ctx, "🎶 Chungus Queue")

        if now_playing:
            now_playing_text = (
                f"▶️ [{now_playing.title}]({now_playing.watch_url}) "
                f"`{utils.time_format(now_playing.length)}`"
            )
            embed.add_field(
                name="Now Playing",
                value=now_playing_text,
                inline=False,
            ).set_thumbnail(url=now_playing.thumbnail_url)

            start_index = queue.index(now_playing)
        else:
            start_index = -1

        lines = [
            f"**{i})** [{s.title}]({s.watch_url}) `{time_format(s.length)}`\n"
            for i, s in enumerate(queue, start=1)
        ]

        pages = split_to_pages(lines)

        if page_number is None:
            cur_page_number, cur_page = next(
                (page_index, page)
                for page_index, page in enumerate(pages, start=1)
                if lines[start_index] in page
            )
        else:
            cur_page_number, cur_page = page_number, pages[page_number - 1]

        if cur_page[: min(len(cur_page), default_per_page)]:
            number_of_pages = len(pages)
            embed.add_field(
                name=f"Queue Page {cur_page_number}/{number_of_pages}",
                value="".join(cur_page),
                inline=False,
            )

        await ctx.send(embed=embed)

    @commands.hybrid_command(description="Skip the current song")
    async def skip(self, ctx: Context) -> None:
        if voice := cast("discord.VoiceClient", ctx.voice_client):
            voice.stop()
        await ctx.send(embed=make_embed(ctx, "👌 Skipped"))

    @commands.hybrid_command(description="Clear the queue")
    async def clear(self, ctx: Context) -> None:
        self.bot.song_queues[ctx.guild.id].clear()
        self.bot.song_indexes[ctx.guild.id] = 0
        await ctx.send(embed=make_embed(ctx, "👌 Queue cleared"))

    @commands.hybrid_command(description="Jump to a specific song in the queue")
    @discord.app_commands.describe(song_number="The position of the song in the queue")
    async def jump(self, ctx: Context, *, song_number: str) -> None:
        try:
            index = int(song_number) - 1
            song = self.bot.song_queues[ctx.guild.id][index]
            self.bot.song_indexes[ctx.guild.id] = index

            if voice := cast("discord.VoiceClient", ctx.voice_client):
                voice.stop()

            title = f"Jumped to song #{song_number}"
            desc = f"[{song.title}]({song.watch_url})"
            await ctx.send(embed=make_embed(ctx, title, desc))
        except ValueError:
            await ctx.send(embed=make_embed(ctx, "**Provide the song index!**"))
        except IndexError:
            await ctx.send(embed=make_embed(ctx, "**Index out of bounds!**"))

    @commands.hybrid_command(description="Loop the queue")
    async def loop(self, ctx: Context) -> None:
        guild_id = ctx.guild.id
        self.bot.loop_queue[guild_id] = True
        await ctx.send(embed=make_embed(ctx, "Now looping the **queue**"))

    @commands.hybrid_command(description="Disable queue looping")
    async def unloop(self, ctx: Context) -> None:
        guild_id = ctx.guild.id
        self.bot.loop_queue[guild_id] = False
        await ctx.send(embed=make_embed(ctx, "Looping is now **disabled**"))

    @commands.hybrid_command(description="Pause the current song")
    async def pause(self, ctx: Context) -> None:
        if voice := cast("discord.VoiceClient", ctx.voice_client):
            voice.pause()
        await ctx.send(embed=make_embed(ctx, "⏸️ Paused"))

    @commands.hybrid_command(description="Resume the current song")
    async def unpause(self, ctx: Context) -> None:
        if voice := cast("discord.VoiceClient", ctx.voice_client):
            voice.resume()
        await ctx.send(embed=make_embed(ctx, "▶️ Resumed"))

    @commands.hybrid_command(description="Remove a song from the queue")
    @discord.app_commands.describe(song_number="The position of the song in the queue")
    async def remove(self, ctx: Context, *, song_number: str) -> None:
        try:
            song = self.bot.song_queues[ctx.guild.id].pop(int(song_number) - 1)
            title = f"Removed song #{song_number}"
            desc = f"[{song.title}]({song.watch_url})"
            await ctx.send(embed=make_embed(ctx, title, desc))
        except ValueError:
            await ctx.send(embed=make_embed(ctx, "**Provide the song index!**"))
        except IndexError:
            await ctx.send(embed=make_embed(ctx, "**Index out of bounds!**"))

    @commands.hybrid_command(description="Shuffle the queue")
    async def shuffle(self, ctx: Context) -> None:
        random.shuffle(self.bot.song_queues[ctx.guild.id])
        await ctx.send(embed=make_embed(ctx, "🔀 Queue shuffled"))

    @commands.hybrid_command(description="Stop playing and clear the queue")
    async def stop(self, ctx: Context) -> None:
        self.bot.song_queues[ctx.guild.id].clear()
        self.bot.song_indexes[ctx.guild.id] = 0
        if voice := cast("discord.VoiceClient", ctx.voice_client):
            voice.stop()
        await ctx.send(embed=make_embed(ctx, "🛑 Stopped and cleared queue"))

    @commands.hybrid_command(description="Move a song to another position in the queue")
    @discord.app_commands.describe(first_number="The current position of the song")
    @discord.app_commands.describe(second_number="The new position in the queue")
    async def move(
        self,
        ctx: Context,
        first_number: str,
        *,
        second_number: str,
    ) -> None:
        try:
            first_index = int(first_number) - 1
            second_index = int(second_number) - 1
            song = self.bot.song_queues[ctx.guild.id][first_index]
            self.bot.song_queues[ctx.guild.id].insert(
                second_index,
                self.bot.song_queues[ctx.guild.id].pop(first_index),
            )
            title = f"Moved song #{first_number} to #{second_number}"

            desc = f"[{song.title}]({song.watch_url})"
            await ctx.send(embed=make_embed(ctx, title, desc))
        except ValueError:
            await ctx.send(embed=make_embed(ctx, "**Provide the songs index!**"))
        except IndexError:
            await ctx.send(embed=make_embed(ctx, "**Index out of bounds!**"))

    @commands.hybrid_command(description="Show detailed info about the current song")
    async def info(self, ctx: Context) -> None:
        now_playing = (
            self.bot.cur_songs[ctx.guild.id][0]
            if self.bot.cur_songs[ctx.guild.id]
            else None
        )

        if now_playing is None:
            await ctx.send(embed=make_embed(ctx, "❌ There is no song playing!"))
            return

        song, start_time = self.bot.cur_songs[ctx.guild.id]
        progress = round(time.time()) - start_time
        total_length = song.length

        bar_length = 20
        filled_length = int(progress / total_length * bar_length) if total_length else 0
        bar = "█" * filled_length + "─" * (bar_length - filled_length)

        loop_status = (
            "🔁 Queue Looping"
            if self.bot.loop_queue.get(ctx.guild.id, False)
            else "No Loop"
        )

        try:
            queue_pos = self.bot.song_queues[ctx.guild.id].index(song) + 1
        except ValueError:
            queue_pos = 1

        duration_string = (
            f"{utils.time_format(progress)} / {utils.time_format(total_length)}"
        )

        await ctx.send(
            embed=make_embed(
                ctx,
                song.title,
                description=(
                    f"**Uploader:** {song.author}\n"
                    f"**Queue Position:** {queue_pos}\n"
                    f"**Duration:** `{duration_string}`\n"
                    f"**Progress:** `{bar}`\n"
                    f"**Loop Status:** {loop_status}"
                ),
                embed_url=song.watch_url,
                thumbnail_url=song.thumbnail_url,
            ),
        )
