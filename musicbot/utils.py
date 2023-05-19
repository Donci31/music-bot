import httpx
import re
import time
from re import Match

YOUTUBE_PLAYLIST_REGEX = re.compile(r'(?:http?s?://)?(?:www\.|m\.)?(?:music.)?youtu\.?be(?:\.com)?'
                                    r'(?:\w*.?://)?\w*.?\w*-?.?\w*(?:playlist|list|embed|.*/)?\??'
                                    r'(?:feature=\w*\.?\w*)?&?(?:list=|/)(?P<playlist_id>[\w-]{34})(?:\S+)?')

YOUTUBE_WATCH_REGEX = re.compile(r'(?:http?s?://)?(?:www\.|m\.)?(?:music.)?youtu\.?be(?:\.com)?'
                                 r'(?:\w*.?://)?\w*.?\w*-?.?\w*(?:embed|e|v|watch|shorts|.*/)?\??'
                                 r'(?:feature=\w*\.?\w*)?&?(?:\?v=|/)(?P<youtube_id>[\w-]{11})(?:\S+)?')


def keyword_search(keyword: str) -> Match[str] | None:
    search_query = {'search_query': keyword}
    response = httpx.get('https://www.youtube.com/results', params=search_query)
    youtube_match = re.search(r'/(?:watch\?v=|shorts/)(?P<youtube_id>[\w-]{11})', response.text)

    return youtube_match


def time_format(secs: int) -> str:
    if secs < 3600:
        return time.strftime('%M:%S', time.gmtime(secs))
    else:
        return time.strftime('%H:%M:%S', time.gmtime(secs))
