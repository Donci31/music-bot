import discord
import random
import os
from discord.ext import commands
from collections import defaultdict
from tempfile import TemporaryDirectory
from pytube import YouTube, Playlist

from musicbot import utils
from musicbot.utils import YOUTUBE_WATCH_REGEX, YOUTUBE_PLAYLIST_REGEX


class MusicBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='-')
        self.song_queues = defaultdict(list)
        self.song_indexes = defaultdict(int)
        self.song_directory = TemporaryDirectory()
        self.loop_queue = False

        @self.command()
        async def play(ctx, *, keyword):
            if ctx.author.voice is None:
                embed_message = discord.Embed(description='**Join a voice channel!**')
                await ctx.channel.send(embed=embed_message)
                return

            if ctx.voice_client is None or not ctx.voice_client.is_connected():
                voice_channel = ctx.author.voice.channel
                await voice_channel.connect()

            voice = ctx.voice_client
            guild_id = ctx.guild.id

            youtube_playlist_match = YOUTUBE_PLAYLIST_REGEX.fullmatch(keyword)

            if youtube_playlist_match:
                playlist_id = youtube_playlist_match.group(1)

                playlist = Playlist(f'https://www.youtube.com/playlist?list={playlist_id}')
                await self._add_playlist(ctx, playlist)
            else:
                youtube_link_match = YOUTUBE_WATCH_REGEX.fullmatch(keyword)

                if youtube_link_match:
                    song_id = youtube_link_match.group(1)
                else:
                    song_id = utils.keyword_search(keyword)

                song = YouTube(f'https://www.youtube.com/watch?v={song_id}')
                await self._add_song(ctx, song)

            if not voice.is_playing():
                self._start_playing(voice, guild_id)

        @self.command()
        async def queue(ctx):
            guild_id = ctx.guild.id
            channel = ctx.channel
            index = self.song_indexes[guild_id]
            song_queue_slice = self.song_queues[guild_id][index:index + 10]

            if self.song_queues[guild_id]:
                numbered_list = '\n'.join(f'**{i})** [{song.title}]({song.watch_url}) '
                                          f'``{utils.time_format(song.length)}``'
                                          for i, song in enumerate(song_queue_slice, 1))
                embed_message = discord.Embed(description=numbered_list)
                await channel.send(embed=embed_message)

        @self.command()
        async def skip(ctx):
            voice = ctx.voice_client
            message = ctx.message

            if voice is not None:
                voice.stop()

            await message.add_reaction('\U0001F44C')

        @self.command()
        async def clear(ctx):
            guild_id = ctx.guild.id
            message = ctx.message

            self.song_queues[guild_id].clear()
            self.song_indexes[guild_id] = 0

            await message.add_reaction('\U0001F44C')

        @self.command()
        async def jump(ctx, *, jump_number):
            guild_id = ctx.guild.id
            voice = ctx.voice_client
            channel = ctx.channel
            queue_length = len(self.song_queues[guild_id])

            if utils.index_check(jump_number, queue_length):
                index = int(jump_number) - 1
                song = self.song_queues[guild_id][index]

                self.song_indexes[guild_id] = index
                if voice is not None:
                    voice.stop()

                desc = f'Jumped to [{song.title}]({song.watch_url})'
                embed_message = discord.Embed(description=desc)
                await channel.send(embed=embed_message)

        @self.command()
        async def loop(ctx):
            channel = ctx.channel

            self.loop_queue = True

            desc = 'Now looping the **queue**'
            embed_message = discord.Embed(description=desc)
            await channel.send(embed=embed_message)

        @self.command()
        async def unloop(ctx):
            channel = ctx.channel

            self.loop_queue = False

            desc = 'Looping is now **disabled**'
            embed_message = discord.Embed(description=desc)
            await channel.send(embed=embed_message)

        @self.command()
        async def pause(ctx):
            voice = ctx.voice_client
            message = ctx.message

            if voice is not None:
                voice.pause()

            await message.add_reaction('\U000023F8')

        @self.command()
        async def unpause(ctx):
            voice = ctx.voice_client
            message = ctx.message

            if voice is not None:
                voice.resume()

            await message.add_reaction('\U000025B6')

        @self.command()
        async def remove(ctx, *, remove_number):
            guild_id = ctx.guild.id
            channel = ctx.channel
            queue_length = len(self.song_queues[guild_id])

            if utils.index_check(remove_number, queue_length):
                index = int(remove_number) - 1
                song = self.song_queues[guild_id][index]

                self.song_queues[guild_id].pop(index)

                desc = f'Removed [{song.title}]({song.watch_url})'
                embed_message = discord.Embed(description=desc)
                await channel.send(embed=embed_message)

        @self.command()
        async def shuffle(ctx):
            guild_id = ctx.guild.id
            message = ctx.message

            random.shuffle(self.song_queues[guild_id])

            await message.add_reaction('\U0001F500')

        @self.command()
        async def stop(ctx):
            guild_id = ctx.guild.id
            voice = ctx.voice_client
            message = ctx.message

            self.song_queues[guild_id].clear()
            self.song_indexes[guild_id] = 0
            if voice is not None:
                voice.stop()

            await message.add_reaction('\U0001F6D1')

        @self.command()
        async def move(ctx, first_number, *, second_number):
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

    async def _add_playlist(self, ctx, playlist):
        channel = ctx.channel
        guild_id = ctx.guild.id

        self.song_queues[guild_id].extend(playlist.videos)

        desc = f'Queued [{playlist.title}]({playlist.playlist_url}) | **{len(playlist)}** songs'
        embed_message = discord.Embed(description=desc)
        await channel.send(embed=embed_message)

    async def _add_song(self, ctx, song):
        channel = ctx.channel
        guild_id = ctx.guild.id

        self.song_queues[guild_id].append(song)

        desc = f'Queued [{song.title}]({song.watch_url}) ``{utils.time_format(song.length)}``'
        embed_message = discord.Embed(description=desc)
        await channel.send(embed=embed_message)

    def _download_song(self, video):
        song = video.streams.filter(only_audio=True).first()
        song.download(output_path=self.song_directory.name, filename=f'{video.video_id}.mp4')
        return os.path.join(self.song_directory.name, f'{video.video_id}.mp4')

    def _start_playing(self, voice, guild_id):
        if self.song_indexes[guild_id] < len(self.song_queues[guild_id]):
            new_song_index = self.song_indexes[guild_id]
            new_song = self.song_queues[guild_id][new_song_index]
            song_path = self._download_song(new_song)

            voice.play(discord.FFmpegPCMAudio(song_path), after=lambda e: self._start_playing(voice, guild_id))

            self.song_indexes[guild_id] += 1
        elif self.loop_queue:
            self.song_indexes[guild_id] = 0
            self._start_playing(voice, guild_id)

    async def close(self):
        self.song_directory.cleanup()
        await super().close()
