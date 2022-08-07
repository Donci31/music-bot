import discord
import re
import requests
from discord.embeds import EmptyEmbed
from datetime import datetime


YOUTUBE_PLAYLIST_REGEX = re.compile(r'(?:http?s?://)?(?:www\.|m\.)?(?:music.)?youtu\.?be(?:\.com)?'
                                    r'(?:\w*.?://)?\w*.?\w*-?.?\w*(?:playlist|list|embed|.*/)?\??'
                                    r'(?:feature=\w*\.?\w*)?&?(?:list=|/)([\w-]{34})(?:\S+)?')

YOUTUBE_WATCH_REGEX = re.compile(r'(?:http?s?://)?(?:www\.|m\.)?(?:music.)?youtu\.?be(?:\.com)?'
                                 r'(?:\w*.?://)?\w*.?\w*-?.?\w*(?:embed|e|v|watch|shorts|.*/)?\??'
                                 r'(?:feature=\w*\.?\w*)?&?(?:\?v=|/)([\w-]{11})(?:\S+)?')


def get_playlist_url(playlist_id):
    return f'https://www.youtube.com/playlist?list={playlist_id}'


def get_song_url(song_id):
    return f'https://www.youtube.com/watch?v={song_id}'


def keyword_search(keyword):
    search_query = {'search_query': keyword}
    html = requests.get('https://www.youtube.com/results', params=search_query).text
    song_id = re.search(r'/(?:watch\?v=|shorts/)([\w-]{11})', html).group(1)

    return song_id


def time_format(secs):
    if secs < 3600:
        return datetime.fromtimestamp(secs).strftime('%M:%S')
    else:
        return datetime.fromtimestamp(secs).strftime('%H:%M:%S')


async def send_embed(channel, title=EmptyEmbed, description=EmptyEmbed):
    queued_message = discord.Embed(title=title, description=description)
    await channel.send(embed=queued_message)
