from os import environ
from dotenv import load_dotenv

from MusicBot import MusicBot


def main():
    load_dotenv()
    token = environ['BOT_TOKEN']
    bot = MusicBot()
    bot.run(token)


if __name__ == '__main__':
    main()
