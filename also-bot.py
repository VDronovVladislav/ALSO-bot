import re
from datetime import datetime
from threading import Timer

from telegram import (Bot, ReplyKeyboardMarkup, InputMediaPhoto,
                      InlineKeyboardButton, InlineKeyboardMarkup)
from telegram.ext import (CommandHandler, MessageHandler, CallbackQueryHandler,
                          Updater, Filters)

media = []
posts = []
date_format = "%d.%m %H:%M"
timer = None
TIMER_DELAY = 1
TIME_PATTERN = r'(0[1-9]|[1-2][0-9]|3[0-1])\.(0[1-9]|1[0-2]) ([0-1][0-9]|2[0-3])\:([0-5][0-9])'
TELEGRAM_CHAT_IDs = [1111]


def send_message(bot, message, post):
    """Отправляет сообщения в Telegram."""
    for chat_id in TELEGRAM_CHAT_IDs:
        bot.send_media_group(chat_id=chat_id, media=post['media'])


def validate_pub_time(date, chat_id, context):
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
            text=f'Рассылка начнется {message[0]}.2024 в {message[1]}'
        )
        return True
    if media:
        context.bot.send_message(
                chat_id=chat_id,
                text='Неверный формат даты или времени!'
            )
    return False


def reset_timer(chat_id, context, message):
    """Функция обновления таймера и отправки сообщения с установкой времени."""
    global timer
    if media:
        context.bot.send_message(
            chat_id=chat_id,
            text='Отправьте время отправки в формате 31.12 13:30'
        )
    timer = None


def save_post(update, context):
    """Функция сохранения поста."""
    global timer, posts
    chat = update.effective_chat
    message = update.message
    text = update.message.text

    if text == '/newpost':
        context.bot.send_message(
            chat_id=chat.id,
            text='Пришлите свой пост. Он будет отправлен во все группы!'
        )

    elif text is not None and validate_pub_time(text, chat.id, context):
        post = {'id': message.message_id,
                'date': update.message.text,
                'media': media.copy()}
        posts.append(post)
        posts = sorted(
            posts, key=lambda x: datetime.strptime(x['date'], date_format)
        )
        media.clear()

    else:
        if message.media_group_id:
            media.append(InputMediaPhoto(message.photo[-1].file_id))
            if message.caption and len(media) == 1:
                media[0].caption = message.caption
        else:
            media.append(InputMediaPhoto(message.photo[-1].file_id))
            print(message)
            message.caption = message.caption

        if timer:
            timer.cancel()
        timer = Timer(TIMER_DELAY, reset_timer, [chat.id, context, message])
        timer.start()


def post_list(update, context):
    """Показывает список постов."""
    chat = update.effective_chat
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


def show_post(chat_id, post_id, context):
    """Отправляет пост по нажатию кнопки."""
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
            context.bot.send_message(chat_id=chat_id, text='Пост удален!')
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
        [['/newpost'], ['/postlist'], ['/deletepost']],
        resize_keyboard=True
    )
    context.bot.send_message(
        chat_id=chat.id,
        text=f'''Привет, {name}
        Чтобы отправить пост воспользуйтесь командой /newpost
        Отменить пост можно командой /deletepost
        Список текущих запланированных постов - /postlist''',
        reply_markup=buttons
    )


def main():
    """Основная логика работы бота."""
    bot = Bot(token='xxx')
    updater = Updater(token='xxx')
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', wake_up))
    dp.add_handler(CommandHandler('newpost', save_post))
    dp.add_handler(CommandHandler('postlist', post_list))
    dp.add_handler(CommandHandler('give', show_post))
    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_handler(MessageHandler(Filters.all, save_post))

    updater.start_polling(poll_interval=5.0)
    updater.idle()


if __name__ == '__main__':
    main()
