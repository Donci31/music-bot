import random
import time

import discord
from discord.ext import commands
from discord.ext.commands import Context
from pytubefix import YouTube, Playlist, Search

from musicbot import utils, MusicBot
from musicbot.utils import YOUTUBE_WATCH_REGEX, YOUTUBE_PLAYLIST_REGEX, make_embed


class MusicCommands(commands.Cog):
    def __init__(self, bot: MusicBot):
        self.bot = bot

    @commands.hybrid_command(description="Play a song or playlist from YouTube")
    @discord.app_commands.describe(song="The YouTube link or search query")
    async def play(self, ctx: Context, *, song: str) -> None:
        if ctx.author.voice is None:
            await ctx.reply(embed=make_embed(ctx, "**Join a voice channel!**"))
            return

        if ctx.voice_client is None or not ctx.voice_client.is_connected():
            await ctx.author.voice.channel.connect()

        guild_id = ctx.guild.id
        voice = ctx.voice_client

        await ctx.defer()

        if match := YOUTUBE_PLAYLIST_REGEX.fullmatch(song):
            playlist_id = match.group('playlist_id')
            playlist = Playlist(f'https://www.youtube.com/playlist?list={playlist_id}')
            await self.bot.add_playlist(ctx, playlist)
        else:
            if not (link_match := YOUTUBE_WATCH_REGEX.fullmatch(song)):
                youtube_song = Search(song).videos[0]
            else:
                song_id = link_match.group('youtube_id')
                youtube_song = YouTube(f'https://www.youtube.com/watch?v={song_id}')
            await self.bot.add_song(ctx, youtube_song)

        if not voice.is_playing():
            self.bot.start_playing(guild_id, voice)

    @commands.hybrid_command(description="Show the current music queue with page selector")
    @discord.app_commands.describe(page="The page number to view")
    async def queue(self, ctx: Context, page: int = 1) -> None:
        await ctx.defer()

        guild_id = ctx.guild.id
        queue = self.bot.song_queues[guild_id]
        now_playing = next(iter(self.bot.cur_songs[guild_id] or []), None)

        if not queue and now_playing is None:
            await ctx.reply(embed=make_embed(ctx, "❌ No songs currently playing."))
            return

        per_page = 10
        total_pages = max((len(queue) - 1) // per_page + 1, 1)
        page = max(1, min(page, total_pages))
        start_index = (page - 1) * per_page
        queue_slice = queue[start_index:start_index + per_page]

        embed = make_embed(ctx, "🎶 Chungus Queue")

        if now_playing:
            embed.add_field(
                name="Now Playing",
                value=f"▶️ [{now_playing.title}]({now_playing.watch_url}) "
                      f"`{utils.time_format(now_playing.length)}`",
                inline=False
            ).set_thumbnail(url=now_playing.thumbnail_url)

        if queue_slice:
            queue_text = ""
            for i, song in enumerate(queue_slice, start=start_index + 1):
                queue_text += f"**{i})** [{song.title}]({song.watch_url}) " \
                              f"`{utils.time_format(song.length)}`\n"
            embed.add_field(name=f"Queue Page {page}/{total_pages}", value=queue_text, inline=False)

        await ctx.reply(embed=embed)

    @commands.hybrid_command(description="Skip the current song")
    async def skip(self, ctx: Context) -> None:
        if ctx.voice_client:
            ctx.voice_client.stop()
        await ctx.reply(embed=make_embed(ctx, "👌 Skipped"))

    @commands.hybrid_command(description="Clear the queue")
    async def clear(self, ctx: Context) -> None:
        guild_id = ctx.guild.id
        self.bot.song_queues[guild_id].clear()
        self.bot.song_indexes[guild_id] = 0
        await ctx.reply(embed=make_embed(ctx, "👌 Queue cleared"))

    @commands.hybrid_command(description="Jump to a specific song in the queue")
    @discord.app_commands.describe(song_number="The position of the song in the queue")
    async def jump(self, ctx: Context, *, song_number: str) -> None:
        guild_id = ctx.guild.id
        try:
            index = int(song_number) - 1
            song = self.bot.song_queues[guild_id][index]
            self.bot.song_indexes[guild_id] = index

            if ctx.voice_client:
                ctx.voice_client.stop()

            desc = f'Jumped to [{song.title}]({song.watch_url})'
            await ctx.reply(embed=make_embed(ctx, desc))
        except ValueError:
            await ctx.reply(embed=make_embed(ctx, "**Provide the song index!**"))
        except IndexError:
            await ctx.reply(embed=make_embed(ctx, "**Index out of bounds!**"))

    @commands.hybrid_command(description="Loop the queue")
    async def loop(self, ctx: Context) -> None:
        guild_id = ctx.guild.id
        self.bot.loop_queue[guild_id] = True
        await ctx.reply(embed=make_embed(ctx, "Now looping the **queue**"))

    @commands.hybrid_command(description="Disable queue looping")
    async def unloop(self, ctx: Context) -> None:
        guild_id = ctx.guild.id
        self.bot.loop_queue[guild_id] = False
        await ctx.reply(embed=make_embed(ctx, "Looping is now **disabled**"))

    @commands.hybrid_command(description="Pause the current song")
    async def pause(self, ctx: Context) -> None:
        if ctx.voice_client:
            ctx.voice_client.pause()
        await ctx.reply(embed=make_embed(ctx, "⏸️ Paused"))

    @commands.hybrid_command(description="Resume the current song")
    async def unpause(self, ctx: Context) -> None:
        if ctx.voice_client:
            ctx.voice_client.resume()
        await ctx.reply(embed=make_embed(ctx, "▶️ Resumed"))

    @commands.hybrid_command(description="Remove a song from the queue")
    @discord.app_commands.describe(song_number="The position of the song in the queue")
    async def remove(self, ctx: Context, *, song_number: str) -> None:
        guild_id = ctx.guild.id
        try:
            index = int(song_number) - 1
            song = self.bot.song_queues[guild_id][index]
            self.bot.song_queues[guild_id].pop(index)
            desc = f'Removed [{song.title}]({song.watch_url})'
            await ctx.reply(embed=make_embed(ctx, desc))
        except ValueError:
            await ctx.reply(embed=make_embed(ctx, "**Provide the song index!**"))
        except IndexError:
            await ctx.reply(embed=make_embed(ctx, "**Index out of bounds!**"))

    @commands.hybrid_command(description="Shuffle the queue")
    async def shuffle(self, ctx: Context) -> None:
        guild_id = ctx.guild.id
        random.shuffle(self.bot.song_queues[guild_id])
        await ctx.reply(embed=make_embed(ctx, "🔀 Queue shuffled"))

    @commands.hybrid_command(description="Stop playing and clear the queue")
    async def stop(self, ctx: Context) -> None:
        guild_id = ctx.guild.id
        self.bot.song_queues[guild_id].clear()
        self.bot.song_indexes[guild_id] = 0
        if ctx.voice_client:
            ctx.voice_client.stop()
        await ctx.reply(embed=make_embed(ctx, "🛑 Stopped and cleared queue"))

    @commands.hybrid_command(description="Move a song to another position in the queue")
    @discord.app_commands.describe(first_number="The current position of the song")
    @discord.app_commands.describe(second_number="The new position in the queue")
    async def move(self, ctx: Context, first_number: str, *, second_number: str) -> None:
        guild_id = ctx.guild.id
        song_queue = self.bot.song_queues[guild_id]
        try:
            first_index = int(first_number) - 1
            second_index = int(second_number) - 1
            song = song_queue[first_index]
            song_queue.insert(second_index, song_queue.pop(first_index))
            desc = f'Moved [{song.title}]({song.watch_url}) to position **{second_index + 1}**'
            await ctx.reply(embed=make_embed(ctx, desc))
        except ValueError:
            await ctx.reply(embed=make_embed(ctx, "**Provide the songs index!**"))
        except IndexError:
            await ctx.reply(embed=make_embed(ctx, "**Index out of bounds!**"))

    @commands.hybrid_command(description="Show detailed info about the current song")
    async def info(self, ctx: Context) -> None:
        guild_id = ctx.guild.id
        now_playing = next(iter(self.bot.cur_songs[guild_id] or []), None)

        if now_playing is None:
            await ctx.reply(embed=make_embed(ctx, "❌ There is no song playing!"))
            return

        song, start_time = self.bot.cur_songs[guild_id]
        progress = round(time.time()) - start_time
        total_length = song.length

        bar_length = 20
        filled_length = int(progress / total_length * bar_length) if total_length else 0
        bar = '█' * filled_length + '─' * (bar_length - filled_length)

        loop_status = "🔁 Queue Looping" if self.bot.loop_queue.get(guild_id, False) else "No Loop"

        try:
            queue_pos = self.bot.song_queues[guild_id].index(song) + 1
        except ValueError:
            queue_pos = 1

        embed = (
            discord.Embed(
                title=song.title,
                url=song.watch_url,
                color=discord.Color.blurple(),
                description=(
                    f"**Uploader:** {song.author}\n"
                    f"**Queue Position:** {queue_pos}\n"
                    f"**Duration:** `{utils.time_format(progress)} / {utils.time_format(total_length)}`\n"
                    f"**Progress:** `{bar}`\n"
                    f"**Loop Status:** {loop_status}"
                )
            )
            .set_thumbnail(url=song.thumbnail_url)
            .set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar)
            .set_footer(text="Powered by Chungus", icon_url=utils.CHUNGUS_ICON)
        )

        await ctx.reply(embed=embed)
