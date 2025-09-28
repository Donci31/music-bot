import re
import time

import discord
from discord.ext.commands import Context

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


def time_format(secs: int) -> str:
    t = time.gmtime(secs)
    if t.tm_hour:
        return time.strftime("%H:%M:%S", t)
    return time.strftime("%M:%S", t)


def split_to_pages(lines: list[str]) -> list[list[str]]:
    embed_field_value_length = 1024
    max_items = 10

    pages = []
    current_page = []
    current_sum = 0

    for line in lines:
        length = len(line)

        if (len(current_page) >= max_items) or (
            current_sum + length > embed_field_value_length
        ):
            pages.append(current_page)
            current_page = []
            current_sum = 0

        current_page.append(line)
        current_sum += length

    if current_page:
        pages.append(current_page)

    return pages
