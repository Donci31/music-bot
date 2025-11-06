# 🎵 Discord Music Bot

This bot is designed to play music in Discord voice channels.
With this bot, users can enjoy their favorite music tracks
 with friends in their Discord server.
The bot supports various commands to control playback, queue songs,
 and provide an enhanced music listening experience.

## ✨ Features

* **🎶 Play Music:** Users can command the bot to play music from YouTube.
* **🎮 Control Playback:** Users have control over playback commands like
 play, pause, resume, stop, skip.
* **📋 Queue Management:** The bot maintains a queue of songs,
 allowing users to add songs, remove songs, and view the current queue.
* **🔄 Looping and Shuffle:** The bot provides options to loop
 the entire queue. Users can also shuffle the order of the songs.
* **💬 User-friendly Commands:** The bot has intuitive commands with clear syntax.
* **⚠️ Error Handling:** The bot gracefully handles errors,
 providing informative messages to users when issues occur.

## 📦 Installation

1. You need to have
 [git](https://git-scm.com/install/windows),
 [uv](https://docs.astral.sh/uv/getting-started/installation/)
 and [FFmpeg](https://ffmpeg.org/download.html) installed:
 `winget install --id=FFmpeg.FFmpeg --id=astral-sh.uv --id=Git.Git`
2. Clone and enter the repository:
 `git clone https://github.com/Donci31/music-bot/ && cd music-bot`
3. Obtain a bot token by creating a bot account on the [Discord Developer Portal](https://discord.com/developers/applications)
 and invite the bot to your Discord server using the invite link.
4. Create a .env file with same context as .env.example and insert
 the token, and the bot prefix there.
5. Run the main script: `uv run main.py`.
