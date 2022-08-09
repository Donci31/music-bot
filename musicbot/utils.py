import re
import requests
import time


YOUTUBE_PLAYLIST_REGEX = re.compile(r'(?:http?s?://)?(?:www\.|m\.)?(?:music.)?youtu\.?be(?:\.com)?'
                                    r'(?:\w*.?://)?\w*.?\w*-?.?\w*(?:playlist|list|embed|.*/)?\??'
                                    r'(?:feature=\w*\.?\w*)?&?(?:list=|/)([\w-]{34})(?:\S+)?')


YOUTUBE_WATCH_REGEX = re.compile(r'(?:http?s?://)?(?:www\.|m\.)?(?:music.)?youtu\.?be(?:\.com)?'
                                 r'(?:\w*.?://)?\w*.?\w*-?.?\w*(?:embed|e|v|watch|shorts|.*/)?\??'
                                 r'(?:feature=\w*\.?\w*)?&?(?:\?v=|/)([\w-]{11})(?:\S+)?')


def keyword_search(keyword):
    search_query = {'search_query': keyword}
    html = requests.get('https://www.youtube.com/results', params=search_query).text
    song_id = re.search(r'/(?:watch\?v=|shorts/)([\w-]{11})', html).group(1)

    return song_id


def time_format(secs):
    if secs < 3600:
        return time.strftime('%M:%S', time.gmtime(secs))
    else:
        return time.strftime('%H:%M:%S', time.gmtime(secs))


def index_check(index, array_size):
    return index.isnumeric() and int(index) in range(1, array_size + 1)
