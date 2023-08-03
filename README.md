# Discord Music Bot
The Discord Music Bot is a bot designed to play music in Discord voice channels. With this bot, users can enjoy their favorite music tracks with friends in their Discord server. The bot supports various commands to control playback, queue songs, and provide an enhanced music listening experience.

## Features
* **Play Music:** Users can command the bot to play music Youtube.
* **Control Playback:** Users have control over playback commands like play, pause, resume, stop, skip.
* **Queue Management:** The bot maintains a queue of songs, allowing users to add songs, remove songs, and view the current queue.
* **Looping and Shuffle:** The bot provides options to loop the entire queue. Users can also shuffle the order of the songs.
* **User-friendly Commands:** The bot has intuitive commands with clear syntax.
* **Error Handling:** The bot gracefully handles errors, providing informative messages to users when issues occur.

## Installation
1. You need to have [FFmpeg](https://ffmpeg.org/download.html) installed and its bin folder added to your path.
2. Clone the repository: `git clone https://github.com/Donci31/music-bot`.
3. Install the required dependencies: `pip install -r requirements.txt`.
4. Obtain a bot token by creating a bot account on the [Discord Developer Portal](https://discord.com/developers/applications).
5. Create a .env file with same context as .env.example and instert token there.
6. Invite the bot to your Discord server using the invite link generated in the [Discord Developer Portal](https://discord.com/developers/applications).
7. Run the main script: `python main.py`.
