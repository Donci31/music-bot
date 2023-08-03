from os import environ
from dotenv import load_dotenv

from musicbot import MusicBot


def main() -> None:
    load_dotenv()
    prefix = environ['BOT_PREFIX']
    token = environ['BOT_TOKEN']

    bot = MusicBot(prefix)
    bot.run(token)


if __name__ == '__main__':
    main()

