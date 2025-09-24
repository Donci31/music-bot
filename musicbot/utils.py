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
) -> discord.Embed:
    return (
        discord.Embed(title=title, color=discord.Color.blurple())
        .set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar)
        .set_footer(text="Powered by Chungus", icon_url=CHUNGUS_ICON)
    )


def time_format(secs: int) -> str:
    t = time.gmtime(secs)
    if t.tm_hour:
        return time.strftime("%-H:%M:%S", t)
    return time.strftime("%-M:%S", t)
