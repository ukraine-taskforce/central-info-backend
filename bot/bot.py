import os
from local_providers.get_bot_token import get_bot_token

from telebot import TeleBot


__token = get_bot_token()


def init_bot():
    return TeleBot(__token)
