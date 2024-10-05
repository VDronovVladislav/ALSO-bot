"""Бот для рассылки отложенных постов в Telegram."""
import os
import time
import pytz
from datetime import datetime as dt
from threading import Thread, Timer
from dotenv import load_dotenv


from telegram import (Bot, ReplyKeyboardMarkup, InlineKeyboardButton,
                      InputMediaPhoto,  InputMediaVideo, InlineKeyboardMarkup)
from telegram.ext import (CommandHandler, MessageHandler, CallbackQueryHandler,
                          Updater, Filters)

from constants import date_format, RETRY_TIME, TIMER_DELAY
from utils import validate_pub_time, reset_timer, send_message


load_dotenv()
TOKEN = os.getenv('TOKEN')

# Глобальные переменные
media = []
posts = []
timer = None


def save_post(update, context):
    """Функция сохранения поста."""
    global timer, posts, media
    chat = update.effective_chat
    message = update.message
    text = update.message.text

    if text == '/newpost':
        context.bot.send_message(
            chat_id=chat.id,
            text='Пришлите свой пост. Он будет отправлен во все группы!'
        )

    elif text is not None:
        if media:
            if validate_pub_time(text, chat.id, context, posts):
                post = {'id': message.message_id,
                        'date': update.message.text,
                        'media': media.copy()}
                posts.append(post)
                posts = sorted(
                    posts, key=lambda x: dt.strptime(x['date'], date_format)
                )
                media.clear()
        else:
            context.bot.send_message(
                chat_id=chat.id,
                text='Нет поста для отправки!'
            )

    else:
        if message.media_group_id:
            if message.photo:
                media.append(InputMediaPhoto(message.photo[-1].file_id))
            if message.video:
                media.append(InputMediaVideo(message.video.file_id))
            if message.caption and len(media) == 1:
                media[0].caption = message.caption
        elif message.photo or message.video:
            if message.photo:
                media.append(InputMediaPhoto(message.photo[-1].file_id))
            if message.video:
                media.append(InputMediaVideo(message.video.file_id))
            media[0].caption = message.caption

        if timer:
            timer.cancel()
        timer = Timer(TIMER_DELAY, reset_timer, [chat.id, context, timer])
        timer.start()


def post_list(update, context):
    """Показывает список постов."""
    global posts
    chat = update.effective_chat
    if posts:
        for post in posts:
            text = f'ID поста: {post['id']}, Время отправки: {post['date']}'
            keyboard = [
                [
                    InlineKeyboardButton(
                        "Показать пост", callback_data=f"show_{post['id']}"
                    ),
                    InlineKeyboardButton(
                        "Удалить пост", callback_data=f"delete_{post['id']}"
                    )
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            context.bot.send_message(
                    chat_id=chat.id,
                    text=text,
                    reply_markup=reply_markup
                )
    else:
        context.bot.send_message(
                    chat_id=chat.id,
                    text='На данный момент нет отложенных постов.',
                )


def show_post(chat_id, post_id, context):
    """Отправляет пост для предварительного просмотра по нажатию кнопки."""
    global posts
    for post in posts:
        if post['id'] == post_id:
            context.bot.send_media_group(chat_id=chat_id, media=post['media'])
            break


def delete_post(chat_id, post_id, context):
    """Удаляет пост по нажатию кнопки."""
    global posts
    for post in posts:
        if post['id'] == post_id:
            posts.remove(post)
            context.bot.send_message(
                chat_id=chat_id,
                text=f'Пост {post_id} удален!'
            )
            break


def button_handler(update, context):
    """Функция управления нажатием кнопок удаления/отправки постов."""
    callback_data = update.callback_query.data
    post_id = int(callback_data.split('_')[1])
    chat_id = update.effective_chat.id

    if callback_data.startswith('show_'):
        show_post(chat_id, post_id, context)

    elif callback_data.startswith('delete_'):
        delete_post(chat_id, post_id, context)


def wake_up(update, context):
    """Функция приветствия и вывода кнопок."""
    chat = update.effective_chat
    name = update.message.chat.first_name
    buttons = ReplyKeyboardMarkup(
        [['/newpost'], ['/postlist']],
        resize_keyboard=True
    )
    context.bot.send_message(
        chat_id=chat.id,
        text=f'''Привет, {name}!
Создание поста для рассылки - /newpost
Список текущих запланированных постов (их удаление и просмотр) - /postlist''',
        reply_markup=buttons
    )


def main_sender(bot):
    """Функция проверки времени и отправки сообщений для отдельного потока."""
    global posts
    while True:
        dt_moscow = dt.now(pytz.timezone('Europe/Moscow'))
        for post in posts:
            post_date = dt.strptime(
                post['date'], date_format
            ).replace(year=dt.today().year)
            if str(post_date)[:16] == str(dt_moscow)[:16]:
                send_message(bot, post)
                posts.remove(post)
                break
        time.sleep(RETRY_TIME)


def main():
    """Основная логика работы бота."""
    updater = Updater(token=TOKEN)
    bot = Bot(token=TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', wake_up))
    dp.add_handler(CommandHandler('newpost', save_post))
    dp.add_handler(CommandHandler('postlist', post_list))
    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_handler(MessageHandler(Filters.all, save_post))

    thread = Thread(target=main_sender, args=(bot,))
    thread.start()

    updater.start_polling(poll_interval=5.0)
    updater.idle()


if __name__ == '__main__':
    main()
