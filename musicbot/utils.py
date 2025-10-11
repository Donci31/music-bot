import functools
import re
import time
from typing import TYPE_CHECKING, cast

import discord

if TYPE_CHECKING:
    from collections.abc import Callable

    from discord.ext.commands import Context

    from .music_commands import MusicCommands

YOUTUBE_PLAYLIST_REGEX = re.compile(
    r"(?:http?s?://)?(?:www\.|m\.)?(?:music.)?youtu\.?be(?:\.com)?"
    r"(?:\w*.?://)?\w*.?\w*-?.?\w*(?:playlist|list|embed|.*/)?\??"
    r"(?:feature=\w*\.?\w*)?&?(?:list=|/)(?P<playlist_id>[\w-]{34,})(?:\S+)?",
)

YOUTUBE_WATCH_REGEX = re.compile(
    r"(?:http?s?://)?(?:www\.|m\.)?(?:music.)?youtu\.?be(?:\.com)?"
    r"(?:\w*.?://)?\w*.?\w*-?.?\w*(?:embed|e|v|watch|shorts|.*/)?\??"
    r"(?:feature=\w*\.?\w*)?&?(?:\?v=|/)(?P<youtube_id>[\w-]{11})(?:\S+)?",
)

CHUNGUS_ICON = (
    "https://www.pngall.com/wp-content/uploads/15/Big-Chungus-PNG-Picture.png"
)


def time_format(secs: int) -> str:
    t = time.gmtime(secs)
    if t.tm_hour:
        return time.strftime("%H:%M:%S", t)
    return time.strftime("%M:%S", t)


def create_progress_bar(progress: int, total_length: int, bar_length: int = 20) -> str:
    filled_length = int(progress / total_length * bar_length) if total_length else 0
    return "█" * filled_length + "─" * (bar_length - filled_length)


def get_queue_page(
    queue: list,
    current_index: int,
    page_number: int | None = None,
    max_items: int = 10,
) -> tuple[int, int, str]:
    embed_field_value_limit = 1024

    lines = [
        f"**{i})** [{s.title}]({s.watch_url}) `{time_format(s.length)}`"
        for i, s in enumerate(queue, start=1)
    ]

    pages: list[list[str]] = []
    current_page: list[str] = []
    current_sum = 0

    for line in lines:
        line_length = len(line)
        if (
            len(current_page) >= max_items
            or current_sum + line_length > embed_field_value_limit
        ):
            pages.append(current_page)
            current_page = []
            current_sum = 0

        current_page.append(line)
        current_sum += line_length

    if current_page:
        pages.append(current_page)

    if page_number is None:
        cur_page_number, cur_page = next(
            (idx, page)
            for idx, page in enumerate(pages, start=1)
            if lines[current_index] in page
        )
    else:
        cur_page_number = page_number
        cur_page = pages[page_number - 1]

    return cur_page_number, len(pages), "\n".join(cur_page)


def make_embed(
    ctx: Context,
    title: str,
    description: str | None = None,
    embed_url: str | None = None,
    thumbnail_url: str | None = None,
) -> discord.Embed:
    return (
        discord.Embed(
            title=title,
            url=embed_url,
            description=description,
            color=discord.Color.blurple(),
        )
        .set_thumbnail(url=thumbnail_url)
        .set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar)
        .set_footer(text="Powered by Chungus", icon_url=CHUNGUS_ICON)
    )


def handle_index_errors(
    func: Callable,
) -> Callable:
    @functools.wraps(func)
    async def wrapper(
        music_commands: MusicCommands,
        ctx: Context,
        *args: str,
        **kwargs: str,
    ) -> None:
        try:
            await func(music_commands, ctx, *args, **kwargs)
        except ValueError:
            await ctx.send(
                embed=make_embed(
                    ctx=ctx,
                    title="❌ Provide a number!",
                ),
            )
        except IndexError:
            await ctx.send(
                embed=make_embed(
                    ctx=ctx,
                    title="❌ Number is out of range!",
                ),
            )

    return wrapper


def handle_voice_channel_join(
    func: Callable,
) -> Callable:
    @functools.wraps(func)
    async def wrapper(
        music_commands: MusicCommands,
        ctx: Context,
        *args: str,
        **kwargs: str,
    ) -> None:
        if ctx.author.voice is None:
            await ctx.send(
                embed=make_embed(
                    ctx=ctx,
                    title="🔊 Join a voice channel!",
                ),
            )
            return

        voice = cast("discord.VoiceClient", ctx.voice_client)

        if voice is None or not voice.is_connected():
            voice = await ctx.author.voice.channel.connect()

        await func(music_commands, ctx, *args, **kwargs)

        if not voice.is_playing():
            music_commands.bot.start_playing(ctx.guild.id, voice)

    return wrapper
