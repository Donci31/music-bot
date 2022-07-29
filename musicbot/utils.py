import re
import requests


YOUTUBE_PLAYLIST_REGEX = re.compile(r'(?:http?s?://)?(?:www\.|m\.)?(?:music.)?youtu\.?be(?:\.com)?'
                                    r'(?:\w*.?://)?\w*.?\w*-?.?\w*(?:playlist|list|embed|.*/)?\??'
                                    r'(?:feature=\w*\.?\w*)?&?(?:list=|/)([\w-]{34})(?:\S+)?')

YOUTUBE_WATCH_REGEX = re.compile(r'(?:http?s?://)?(?:www\.|m\.)?(?:music.)?youtu\.?be(?:\.com)?'
                                 r'(?:\w*.?://)?\w*.?\w*-?.?\w*(?:embed|e|v|watch|shorts|.*/)?\??'
                                 r'(?:feature=\w*\.?\w*)?&?(?:\?v=|/)([\w-]{11})(?:\S+)?')


def get_link(song_id):
    return f'https://www.youtube.com/watch?v={song_id}'


def download_song(video, path):
    song = video.streams.filter(only_audio=True).first()
    song.download(output_path=f'{path}', filename=f'{video.video_id}.mp4')


def keyword_search(keyword):
    search_query = {'search_query': keyword}
    html = requests.get('https://www.youtube.com/results', params=search_query).text
    song_id = re.search(r'/(?:watch\?v=|shorts/)([^"]+)', html).group(1)

    return song_id
