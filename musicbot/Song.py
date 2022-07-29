from discord import VoiceClient
from dataclasses import dataclass


@dataclass
class Song:
    voice: VoiceClient
    song_id: str
    song_title: str
    song_length: int
