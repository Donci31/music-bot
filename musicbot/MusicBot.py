import discord
import random
import time
from discord import VoiceClient
from discord.ext import commands
from discord.ext.commands import Context
from collections import defaultdict
from tempfile import TemporaryDirectory
from pytubefix import YouTube, Playlist

from musicbot import utils
from musicbot.utils import YOUTUBE_WATCH_REGEX, YOUTUBE_PLAYLIST_REGEX


class MusicBot(commands.Bot):
    def __init__(self, prefix: str) -> None:
        bot_intents = discord.Intents(guilds=True, guild_messages=True, message_content=True, voice_states=True)
        super().__init__(command_prefix=prefix, intents=bot_intents)

        self.song_queues = defaultdict[int, list[YouTube]](list)
        self.song_indexes = defaultdict[int, int](int)
        self.cur_songs = defaultdict[int, tuple[YouTube, int] | None](lambda: None)
        self.loop_queue = defaultdict[int, bool](bool)

        self.song_directory = TemporaryDirectory[str]()

        @self.command()
        async def play(ctx: Context, *, keyword: str) -> None:
            if ctx.author.voice is None:
                embed_message = discord.Embed(description='**Join a voice channel!**')
                await ctx.channel.send(embed=embed_message)
                return

            if ctx.voice_client is None or not ctx.voice_client.is_connected():
                voice_channel = ctx.author.voice.channel
                await voice_channel.connect()

            guild_id = ctx.guild.id
            voice = ctx.voice_client

            if youtube_playlist_match := YOUTUBE_PLAYLIST_REGEX.fullmatch(keyword):
                playlist_id = youtube_playlist_match.group('playlist_id')

                playlist = Playlist(f'https://www.youtube.com/playlist?list={playlist_id}')
                await self._add_playlist(ctx, playlist)
            else:
                if not (youtube_link_match := YOUTUBE_WATCH_REGEX.fullmatch(keyword)):
                    youtube_link_match = utils.keyword_search(keyword)
                song_id = youtube_link_match.group('youtube_id')

                song = YouTube(f'https://www.youtube.com/watch?v={song_id}', use_po_token=True)
                await self._add_song(ctx, song)

            if not voice.is_playing():
                self._start_playing(guild_id, voice)

        @self.command()
        async def queue(ctx: Context) -> None:
            guild_id = ctx.guild.id
            channel = ctx.channel

            queue_list = []
            index_offset = max(self.song_indexes[guild_id] - 1, 0) // 10 * 10
            now_playing = self.cur_songs[guild_id][0]

            if now_playing is not None:
                queue_list.append(f'**Now Playing:** [{now_playing.title}]({now_playing.watch_url}) '
                                  f'``{utils.time_format(now_playing.length)}``\n')

            if song_queue_slice := self.song_queues[guild_id][index_offset:index_offset + 10]:
                queue_list.extend(f'**{i})** [{song.title}]({song.watch_url}) '
                                  f'``{utils.time_format(song.length)}``'
                                  for i, song in enumerate(song_queue_slice, start=index_offset + 1))

                current_page = index_offset // 10 + 1
                pages = (len(self.song_queues[guild_id]) - 1) // 10 + 1
                queue_list.append(f'Page {current_page}/{pages}')

            if queue_list:
                desc = '\n'.join(queue_list)
                embed_message = discord.Embed(description=desc)
                await channel.send(embed=embed_message)

        @self.command()
        async def skip(ctx: Context) -> None:
            voice = ctx.voice_client
            message = ctx.message

            if voice is not None:
                voice.stop()

            await message.add_reaction('\U0001F44C')

        @self.command()
        async def clear(ctx: Context) -> None:
            guild_id = ctx.guild.id
            message = ctx.message

            self.song_queues[guild_id].clear()
            self.song_indexes[guild_id] = 0

            await message.add_reaction('\U0001F44C')

        @self.command()
        async def jump(ctx: Context, *, jump_number: str) -> None:
            guild_id = ctx.guild.id
            channel = ctx.channel
            voice = ctx.voice_client

            try:
                index = int(jump_number) - 1
                song = self.song_queues[guild_id][index]

                self.song_indexes[guild_id] = index
                if voice is not None:
                    voice.stop()

                desc = f'Jumped to [{song.title}]({song.watch_url})'
                embed_message = discord.Embed(description=desc)
                await channel.send(embed=embed_message)
            except ValueError:
                desc = '**Provide the songs index!**'
                embed_message = discord.Embed(description=desc)
                await channel.send(embed=embed_message)
            except IndexError:
                desc = '**Index out of bounds!**'
                embed_message = discord.Embed(description=desc)
                await channel.send(embed=embed_message)

        @self.command()
        async def loop(ctx: Context) -> None:
            guild_id = ctx.guild.id
            channel = ctx.channel

            self.loop_queue[guild_id] = True

            desc = 'Now looping the **queue**'
            embed_message = discord.Embed(description=desc)
            await channel.send(embed=embed_message)

        @self.command()
        async def unloop(ctx: Context) -> None:
            guild_id = ctx.guild.id
            channel = ctx.channel

            self.loop_queue[guild_id] = False

            desc = 'Looping is now **disabled**'
            embed_message = discord.Embed(description=desc)
            await channel.send(embed=embed_message)

        @self.command()
        async def pause(ctx: Context) -> None:
            voice = ctx.voice_client
            message = ctx.message

            if voice is not None:
                voice.pause()

            await message.add_reaction('\U000023F8')

        @self.command()
        async def unpause(ctx: Context) -> None:
            voice = ctx.voice_client
            message = ctx.message

            if voice is not None:
                voice.resume()

            await message.add_reaction('\U000025B6')

        @self.command()
        async def remove(ctx: Context, *, remove_number: str) -> None:
            guild_id = ctx.guild.id
            channel = ctx.channel

            try:
                index = int(remove_number) - 1
                song = self.song_queues[guild_id][index]

                self.song_queues[guild_id].pop(index)

                desc = f'Removed [{song.title}]({song.watch_url})'
                embed_message = discord.Embed(description=desc)
                await channel.send(embed=embed_message)
            except ValueError:
                desc = '**Provide the songs index!**'
                embed_message = discord.Embed(description=desc)
                await channel.send(embed=embed_message)
            except IndexError:
                desc = '**Index out of bounds!**'
                embed_message = discord.Embed(description=desc)
                await channel.send(embed=embed_message)

        @self.command()
        async def shuffle(ctx: Context) -> None:
            guild_id = ctx.guild.id
            message = ctx.message

            random.shuffle(self.song_queues[guild_id])

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

            await message.add_reaction('\U0001F6D1')

        @self.command()
        async def move(ctx: Context, first_number: str, *, second_number: str) -> None:
            guild_id = ctx.guild.id
            channel = ctx.channel
            song_queue = self.song_queues[guild_id]

            try:
                first_index = int(first_number) - 1
                second_index = int(second_number) - 1
                song = song_queue[first_index]

                song_queue.insert(second_index, song_queue.pop(first_index))

                desc = f'Moved [{song.title}]({song.watch_url}) to position **{second_index + 1}**'
                embed_message = discord.Embed(description=desc)
                await channel.send(embed=embed_message)
            except ValueError:
                desc = '**Provide the songs index!**'
                embed_message = discord.Embed(description=desc)
                await channel.send(embed=embed_message)
            except IndexError:
                desc = '**Index out of bounds!**'
                embed_message = discord.Embed(description=desc)
                await channel.send(embed=embed_message)

        @self.command()
        async def info(ctx: Context) -> None:
            guild_id = ctx.guild.id
            channel = ctx.channel

            if self.cur_songs[guild_id] is None:
                desc = '**There is no current song playing!**'
                embed_message = discord.Embed(description=desc)
                await channel.send(embed=embed_message)
                return

            song = self.cur_songs[guild_id][0]
            current_progress = round(time.time()) - self.cur_songs[guild_id][1]

            desc = '\n'.join(
                (
                    f'**Now playing:** [{song.title}]({song.watch_url})',
                    '',
                    f'**Progress:** ``[{utils.time_format(current_progress)} / {utils.time_format(song.length)}]``'
                )
            )
            embed_message = discord.Embed(description=desc)
            await channel.send(embed=embed_message)

    async def _add_playlist(self, ctx: Context, playlist: Playlist) -> None:
        guild_id = ctx.guild.id
        channel = ctx.channel

        self.song_queues[guild_id].extend(playlist.videos)

        desc = f'Queued [{playlist.title}]({playlist.playlist_url}) | **{len(playlist)}** songs'
        embed_message = discord.Embed(description=desc)
        await channel.send(embed=embed_message)

    async def _add_song(self, ctx: Context, song: YouTube) -> None:
        guild_id = ctx.guild.id
        channel = ctx.channel

        self.song_queues[guild_id].append(song)

        desc = f'Queued [{song.title}]({song.watch_url}) ``{utils.time_format(song.length)}``'
        embed_message = discord.Embed(description=desc)
        await channel.send(embed=embed_message)

    def _download_song(self, video: YouTube) -> str:
        song = video.streams.filter(only_audio=True).first()
        return song.download(output_path=self.song_directory.name, filename=f'{video.video_id}.mp4')

    def _start_playing(self, guild_id: int, voice: VoiceClient) -> None:
        if (cur_index := self.song_indexes[guild_id]) < len(cur_queue := self.song_queues[guild_id]):
            song_path = self._download_song(cur_queue[cur_index])
            self.song_indexes[guild_id] += 1
            self.cur_songs[guild_id] = (cur_queue[cur_index], round(time.time()))

            voice.play(discord.FFmpegPCMAudio(song_path), after=lambda e: self._start_playing(guild_id, voice))
        elif self.loop_queue[guild_id]:
            self.song_indexes[guild_id] = 0
            self._start_playing(guild_id, voice)
        else:
            self.cur_songs[guild_id] = None

    def __del__(self):
        self.song_directory.cleanup()
