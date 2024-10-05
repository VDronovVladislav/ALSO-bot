"""Вспомогательные функции для бота."""
import os
import re
from dotenv import load_dotenv
from copy import copy

from data_reader import DATA_DICT
from constants import TIME_PATTERN, year_now


load_dotenv()
TOKEN = os.getenv('TOKEN')


def validate_pub_time(date, chat_id, context, posts):
    """Функция проверки даты и времени отправки."""
    if re.match(TIME_PATTERN, date):
        if posts:
            for post in posts:
                if post['date'] == date:
                    context.bot.send_message(
                        chat_id=chat_id,
                        text='Данное время уже занято другим постом!'
                    )
                    return False
        message = date.split()
        context.bot.send_message(
            chat_id=chat_id,
            text=f'Рассылка начнется {message[0]}.{year_now} в {message[1]}'
        )
        return True
    context.bot.send_message(
            chat_id=chat_id,
            text='Неверный формат даты или времени!'
        )
    return False


def reset_timer(chat_id, context, timer):
    """Функция обновления таймера и отправки сообщения с установкой времени."""
    context.bot.send_message(
        chat_id=chat_id,
        text='Отправьте время отправки в формате 31.12 13:30'
    )
    return None


def send_message(bot, post):
    """Отправляет сообщения в Telegram с добавлением подписи."""
    for chat_id in DATA_DICT:
        suffix = DATA_DICT.get(chat_id, '')
        base_caption = copy(post['media'][0].caption)
        post['media'][0].caption += suffix
        bot.send_media_group(chat_id=chat_id, media=post['media'])
        post['media'][0].caption = base_caption
