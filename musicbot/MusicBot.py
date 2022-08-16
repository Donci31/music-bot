import discord
import random
import os
from discord import VoiceClient
from discord.ext import commands
from discord.ext.commands import Context
from collections import defaultdict
from tempfile import TemporaryDirectory
from pytube import YouTube, Playlist

from musicbot import utils
from musicbot.utils import YOUTUBE_WATCH_REGEX, YOUTUBE_PLAYLIST_REGEX


class MusicBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix='-')
        self.song_queues = defaultdict[int, list[YouTube]](list)
        self.song_indexes = defaultdict[int, int](int)
        self.song_directory = TemporaryDirectory[str]()
        self.loop_queue = False

        @self.command()
        async def play(ctx: Context, *, keyword: str) -> None:
            if ctx.author.voice is None:
                embed_message = discord.Embed(description='**Join a voice channel!**')
                await ctx.channel.send(embed=embed_message)
                return

            if ctx.voice_client is None or not ctx.voice_client.is_connected():
                voice_channel = ctx.author.voice.channel
                await voice_channel.connect()

            voice = ctx.voice_client
            guild_id = ctx.guild.id

            if youtube_playlist_match := YOUTUBE_PLAYLIST_REGEX.fullmatch(keyword):
                playlist_id = youtube_playlist_match.group(1)

                playlist = Playlist(f'https://www.youtube.com/playlist?list={playlist_id}')
                await self._add_playlist(ctx, playlist)
            else:
                if youtube_link_match := YOUTUBE_WATCH_REGEX.fullmatch(keyword):
                    song_id = youtube_link_match.group(1)
                else:
                    song_id = utils.keyword_search(keyword)

                song = YouTube(f'https://www.youtube.com/watch?v={song_id}')
                await self._add_song(ctx, song)

            if not voice.is_playing():
                self._start_playing(guild_id, voice)

        @self.command()
        async def queue(ctx: Context) -> None:
            guild_id = ctx.guild.id
            channel = ctx.channel
            index_offset = round(self.song_indexes[guild_id] - 1, ndigits=-1)

            if song_queue_slice := self.song_queues[guild_id][index_offset:index_offset + 10]:
                numbered_list = '\n'.join(f'**{i})** [{song.title}]({song.watch_url}) '
                                          f'``{utils.time_format(song.length)}``'
                                          for i, song in enumerate(song_queue_slice, start=index_offset + 1))
                embed_message = discord.Embed(description=numbered_list)
                await channel.send(embed=embed_message)

        @self.command()
        async def skip(ctx: Context) -> None:
            voice = ctx.voice_client
            message = ctx.message

            if voice is not None:
                voice.stop()

            if message is not None:
                await message.add_reaction('\U0001F44C')

        @self.command()
        async def clear(ctx: Context) -> None:
            guild_id = ctx.guild.id
            message = ctx.message

            self.song_queues[guild_id].clear()
            self.song_indexes[guild_id] = 0

            if message is not None:
                await message.add_reaction('\U0001F44C')

        @self.command()
        async def jump(ctx: Context, *, jump_number: str) -> None:
            guild_id = ctx.guild.id
            voice = ctx.voice_client
            channel = ctx.channel

            if utils.index_check(jump_number, len(self.song_queues[guild_id])):
                index = int(jump_number) - 1
                song = self.song_queues[guild_id][index]

                self.song_indexes[guild_id] = index
                if voice is not None:
                    voice.stop()

                desc = f'Jumped to [{song.title}]({song.watch_url})'
                embed_message = discord.Embed(description=desc)
                await channel.send(embed=embed_message)

        @self.command()
        async def loop(ctx: Context) -> None:
            channel = ctx.channel

            self.loop_queue = True

            desc = 'Now looping the **queue**'
            embed_message = discord.Embed(description=desc)
            await channel.send(embed=embed_message)

        @self.command()
        async def unloop(ctx: Context) -> None:
            channel = ctx.channel

            self.loop_queue = False

            desc = 'Looping is now **disabled**'
            embed_message = discord.Embed(description=desc)
            await channel.send(embed=embed_message)

        @self.command()
        async def pause(ctx: Context) -> None:
            voice = ctx.voice_client
            message = ctx.message

            if voice is not None:
                voice.pause()

            if message is not None:
                await message.add_reaction('\U000023F8')

        @self.command()
        async def unpause(ctx: Context) -> None:
            voice = ctx.voice_client
            message = ctx.message

            if voice is not None:
                voice.resume()

            if message is not None:
                await message.add_reaction('\U000025B6')

        @self.command()
        async def remove(ctx: Context, *, remove_number: str) -> None:
            guild_id = ctx.guild.id
            channel = ctx.channel

            if utils.index_check(remove_number, len(self.song_queues[guild_id])):
                index = int(remove_number) - 1
                song = self.song_queues[guild_id][index]

                self.song_queues[guild_id].pop(index)

                desc = f'Removed [{song.title}]({song.watch_url})'
                embed_message = discord.Embed(description=desc)
                await channel.send(embed=embed_message)

        @self.command()
        async def shuffle(ctx: Context) -> None:
            guild_id = ctx.guild.id
            message = ctx.message

            random.shuffle(self.song_queues[guild_id])

            if message is not None:
                await message.add_reaction('\U0001F500')

        @self.command()
        async def stop(ctx: Context) -> None:
            guild_id = ctx.guild.id
            voice = ctx.voice_client
            message = ctx.message

            self.song_queues[guild_id].clear()
            self.song_indexes[guild_id] = 0
            if voice is not None:
                voice.stop()

            if message is not None:
                await message.add_reaction('\U0001F6D1')

        @self.command()
        async def move(ctx: Context, first_number: str, *, second_number: str) -> None:
            guild_id = ctx.guild.id
            channel = ctx.channel
            song_queue = self.song_queues[guild_id]
            queue_length = len(song_queue)

            if utils.index_check(first_number, queue_length) and utils.index_check(second_number, queue_length):
                first_index = int(first_number) - 1
                second_index = int(second_number) - 1
                song = song_queue[first_index]

                song_queue.insert(second_index, song_queue.pop(first_index))

                desc = f'Moved [{song.title}]({song.watch_url}) to position **{second_index}**'
                embed_message = discord.Embed(description=desc)
                await channel.send(embed=embed_message)

    async def _add_playlist(self, ctx: Context, playlist: Playlist) -> None:
        channel = ctx.channel
        guild_id = ctx.guild.id

        self.song_queues[guild_id].extend(playlist.videos)

        desc = f'Queued [{playlist.title}]({playlist.playlist_url}) | **{len(playlist)}** songs'
        embed_message = discord.Embed(description=desc)
        await channel.send(embed=embed_message)

    async def _add_song(self, ctx: Context, song: YouTube) -> None:
        channel = ctx.channel
        guild_id = ctx.guild.id

        self.song_queues[guild_id].append(song)

        desc = f'Queued [{song.title}]({song.watch_url}) ``{utils.time_format(song.length)}``'
        embed_message = discord.Embed(description=desc)
        await channel.send(embed=embed_message)

    def _download_song(self, video: YouTube) -> str:
        song = video.streams.filter(only_audio=True).first()
        song.download(output_path=self.song_directory.name, filename=f'{video.video_id}.mp4')
        return os.path.join(self.song_directory.name, f'{video.video_id}.mp4')

    def _start_playing(self, guild_id: int, voice: VoiceClient) -> None:
        if (cur_index := self.song_indexes[guild_id]) < len(cur_queue := self.song_queues[guild_id]):
            self.song_indexes[guild_id] += 1
            song_path = self._download_song(cur_queue[cur_index])

            voice.play(discord.FFmpegPCMAudio(song_path), after=lambda e: self._start_playing(guild_id, voice))
        elif self.loop_queue:
            self.song_indexes[guild_id] = 0
            self._start_playing(guild_id, voice)

    async def close(self) -> None:
        self.song_directory.cleanup()
        await super().close()
