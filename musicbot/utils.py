import httpx
import re
import time
from re import Match
from typing import Optional

YOUTUBE_PLAYLIST_REGEX = re.compile(r'(?:http?s?://)?(?:www\.|m\.)?(?:music.)?youtu\.?be(?:\.com)?'
                                    r'(?:\w*.?://)?\w*.?\w*-?.?\w*(?:playlist|list|embed|.*/)?\??'
                                    r'(?:feature=\w*\.?\w*)?&?(?:list=|/)(?P<playlist_id>[\w-]{34})(?:\S+)?')

YOUTUBE_WATCH_REGEX = re.compile(r'(?:http?s?://)?(?:www\.|m\.)?(?:music.)?youtu\.?be(?:\.com)?'
                                 r'(?:\w*.?://)?\w*.?\w*-?.?\w*(?:embed|e|v|watch|shorts|.*/)?\??'
                                 r'(?:feature=\w*\.?\w*)?&?(?:\?v=|/)(?P<youtube_id>[\w-]{11})(?:\S+)?')


def keyword_search(keyword: str) -> Optional[Match[str]]:
    search_query = {'search_query': keyword}
    html = httpx.get('https://www.youtube.com/results', params=search_query).text
    youtube_match = re.search(r'/(?:watch\?v=|shorts/)(?P<youtube_id>[\w-]{11})', html)

    return youtube_match


def time_format(secs: int) -> str:
    if secs < 3600:
        return time.strftime('%M:%S', time.gmtime(secs))
    else:
        return time.strftime('%H:%M:%S', time.gmtime(secs))
