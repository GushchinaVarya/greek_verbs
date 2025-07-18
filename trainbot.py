from config import TG_TOKEN_TRAIN, FUTURE_RULES_FILES, PAST_RULES_FILES, PRESENT_RULES_FILES, IMPERATIVE_RULES, ADMINS_IDS, UPDATE_TEXT
from db_functions import get_question, add_user, get_users

import logging
from typing import Any
import sqlite3
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from telegram.error import Forbidden


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    filename="log_trainig.log")
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# State definitions for top level conversation
SELECTING_ACTION, SELECTING_TABLE_TO_DOWNLOAD, SELECTING_TABLE_TO_TRAIN = map(chr, range(3))
PRESENT = "настоящее время"
FUTURE = "будущее время"
IMPERATIVE = "повелительное наклонение"
PAST = "прошедшее время"
# State definitions for second level conversation
DOWNLOAD_RULES = 'читать правила'
START_TRAINING = 'начать тренировку'
START_OVER, TYPING, CONFIRM, YES_ADD, YES_ADD_AND_DELETE, FINISH_TRAINING, AGAIN, STOPPING, NEW, TRAINING_STARTED, GET_QUESTION, BACK, ANNOUNCEMENT = map(chr, range(6, 19))
# State definitions for descriptions conversation
# Shortcut for ConversationHandler.END

MODE = 0
TABLE = 1
QUESTION = 2
ANSWER = 3
COMMENT = 4
END = ConversationHandler.END

async def announcement(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat.id
    print(int(chat_id) in ADMINS_IDS)
    if int(chat_id) in ADMINS_IDS:
        user_ids, user_names = get_users()
        print(user_ids)
        for user_id in user_ids:
            try:
                #context.bot.sendPhoto(
                #    chat_id=int(chat_id),
                #    photo=open(UPDATE_PHOTO, 'rb'),
                #)
                await update.message._bot.send_message(
                    chat_id=int(user_id),
                    text=UPDATE_TEXT,
                    parse_mode='MarkdownV2'
                )
                buttons = [
                    [
                        InlineKeyboardButton(text="Почитать правила", callback_data=str(DOWNLOAD_RULES)),
                        InlineKeyboardButton(text="Начать тренировку", callback_data=str(START_TRAINING)),
                    ],
                ]
                keyboard = InlineKeyboardMarkup(buttons)
                await update.message._bot.send_message(
                    chat_id=int(user_id),
                    text='Пожалуйста перезапустите меня, нажмите /start',
                    #parse_mode='MarkdownV2',
                    #reply_markup=keyboard
                )
                logger.info('notified chat_id: %s', user_id)
            except Forbidden:
                logger.info('Forbidden chat_id: %s', user_id)
            except:
                logger.info('Unknown ERROR chat_id: %s', user_id)
    else:
        logger.info('Unknown ERROR during announcement')
    return ANNOUNCEMENT


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Select an action: Adding parent/child or show data."""
    text = (
        "Выберите действие."
    )
    buttons = [
        [
            InlineKeyboardButton(text="Почитать правила", callback_data=str(DOWNLOAD_RULES)),
            InlineKeyboardButton(text="Начать тренировку", callback_data=str(START_TRAINING)),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    # If we're starting over we don't need to send a new message
    if context.user_data.get(START_OVER):
        user = update.callback_query.from_user
        chat_id = update.callback_query.message.chat.id
        isnew = add_user(chat_id, user.first_name)
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    else:
        await update.message.reply_text(
"""Привет! Я бот, который поможет запомнить как меняются глаголы в греческом языке.

Нажмите "Почитать правила" если хотите вспомнить как правильно спрягать глаголы в зависимости от рода и времени. Либо начинайте тренироваться! Я вам помогу! 

Закончить тренироваться - /stop. """
        )
        user = update.message.from_user
        chat_id = update.message.chat.id
        isnew = add_user(chat_id, user.first_name)
        await update.message.reply_text(text=text, reply_markup=keyboard)

    context.user_data[START_OVER] = False
    if isnew:
        logger.info("NEW user %s with chat_id %s started conversation.", user.first_name, chat_id)
    else:
        logger.info("User %s started conversation.", user.first_name)
    return SELECTING_ACTION


async def select_table(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Choose table."""
    text = "Выберите глаголы."
    buttons = [
        [
            InlineKeyboardButton(text="Настоящее время", callback_data=str(PRESENT)),
            InlineKeyboardButton(text="Повелительное наклонение", callback_data=str(IMPERATIVE)),
        ],
        [
            InlineKeyboardButton(text="Будущее время", callback_data=str(FUTURE)),
            InlineKeyboardButton(text="Прошедшее время", callback_data=str(PAST)),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    context.user_data[MODE] = update.callback_query.data
    logger.info(f"User {update.callback_query.from_user.first_name} selected mode {context.user_data[MODE]}")
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    if context.user_data[MODE] == "читать правила":
        return SELECTING_TABLE_TO_DOWNLOAD
    if context.user_data[MODE] == "начать тренировку":
        return SELECTING_TABLE_TO_TRAIN

async def training_starting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Prompt user to input data for selected feature."""
    context.user_data[TABLE] = update.callback_query.data
    logger.info(f"User {update.callback_query.from_user.first_name} selected table {context.user_data[TABLE]}, and the mode is {context.user_data[MODE]}")
    text = f"""Вы выбрали {context.user_data[TABLE]}\.
    
Как тренироваться:

1\. Приготовьте ручку и бумагу
2\. Я пришлю вам фразу на русском языке, вам нужно перевести ее на греческий
3\. Если вы не знаете сам глагол, но хотите отработать правило спряжения, \- откройте подсказку
4\. Проверьте себя, откройте ответ

НЕ ПРИСЫЛАЙТЕ ответ сообщением\. Мне, боту, будет сложно вас проверить лучше чем это сделаете вы сами\.

П\.С\. не забывайте про ударения\!
"""

    buttons = [
        [
            InlineKeyboardButton(text="Начать тренировку", callback_data=str(GET_QUESTION)),
            InlineKeyboardButton(text="Назад", callback_data=str(START_TRAINING)),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=text, parse_mode='MarkdownV2', reply_markup=keyboard)

    return TRAINING_STARTED


async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Prompt user to input data for selected feature."""
    table = context.user_data[TABLE]
    logger.info(
        f"User {update.callback_query.from_user.first_name} got question from table {context.user_data[TABLE]}")
    await update.callback_query.answer()
    text_q,text_h,text_a = get_question(table)
    buttons = [
        [
            InlineKeyboardButton(text="Еще", callback_data=str(GET_QUESTION)),
            InlineKeyboardButton(text="Завершить", callback_data=str(FINISH_TRAINING)),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    chat_id = update.callback_query.from_user.id
    await update.callback_query._bot.send_message(chat_id=chat_id, text=text_q, parse_mode='MarkdownV2')
    await update.callback_query._bot.send_message(chat_id=chat_id, text=text_h, parse_mode='MarkdownV2')
    await update.callback_query._bot.send_message(chat_id=chat_id, text=text_a, parse_mode='MarkdownV2',reply_markup=keyboard)

    return TRAINING_STARTED

async def download_rule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Prompt user to input data for selected feature."""
    context.user_data[TABLE] = update.callback_query.data
    logger.info(f"User {update.callback_query.from_user.first_name} selected table {context.user_data[TABLE]}, and the mode is {context.user_data[MODE]}")
    ready_flag = 0
    if context.user_data[TABLE] == 'настоящее время':
        files = PRESENT_RULES_FILES
    if context.user_data[TABLE] == 'будущее время':
        files = FUTURE_RULES_FILES
    if context.user_data[TABLE] == 'прошедшее время':
        files = PAST_RULES_FILES
    if context.user_data[TABLE] == 'повелительное наклонение':
        files = IMPERATIVE_RULES
    text = f"""
Вот правила {context.user_data[TABLE]} ⬆️ 

Выберите дальнейшее действие.
"""
    chat_id = update.callback_query.from_user.id
    for filename in files:
        await update.callback_query._bot.send_document(chat_id = chat_id, document=filename)
    ready_flag = 1
    buttons = [
        [
            InlineKeyboardButton(text="Почитать правила", callback_data=str(DOWNLOAD_RULES)),
        ],
        [
            InlineKeyboardButton(text="Начать тренировку", callback_data=str(START_TRAINING)),
        ],
    ]
    if ready_flag == 1:
        await update.callback_query._bot.send_message(chat_id = chat_id, text=text,
                                                  reply_markup=InlineKeyboardMarkup(buttons))
    return SELECTING_ACTION




async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """End Conversation by command."""
    logger.info(
        f"User {update.message.from_user.id} finished. ")
    await update.message.reply_text("Вы завершили тренировку. Чтобы начать сначала введите /start")

    return END

async def finish_training(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """End Conversation by command."""
    buttons = [
        [
            InlineKeyboardButton(text="Почитать правила", callback_data=str(DOWNLOAD_RULES)),
        ],
        [
            InlineKeyboardButton(text="Начать тренировку", callback_data=str(START_TRAINING)),
        ],
    ]
    chat_id = update.callback_query.from_user.id
    await update.callback_query._bot.send_message(chat_id = chat_id, text="Вы завершили тренировку! \nВыберите дальнейшее действие:", reply_markup=InlineKeyboardMarkup(buttons))
    return AGAIN

def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TG_TOKEN_TRAIN).build()



    # Set up second level ConversationHandler (adding a person)
    choose_table_to_train_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(select_table, pattern=f"^{START_TRAINING}$", )],
        states={
            SELECTING_TABLE_TO_TRAIN: [
                CallbackQueryHandler(training_starting, pattern=f"^{PRESENT}$|^{IMPERATIVE}$|^{PAST}$|^{FUTURE}$"),
            ],
            TRAINING_STARTED: [CallbackQueryHandler(send_question, pattern=f"^{GET_QUESTION}$"),
                               CallbackQueryHandler(select_table, pattern=f"^{START_TRAINING}$"),
                               CallbackQueryHandler(finish_training, pattern="^" + str(FINISH_TRAINING) + "$")],
        },
        fallbacks=[
            CommandHandler("stop", stop),
            CommandHandler("start", start),
            CommandHandler("announcement", announcement),
        ],
        map_to_parent={
            # After showing data return to top level menu
            #SHOWING: SHOWING,
            # Return to top level menu
            AGAIN:SELECTING_ACTION,
            BACK: SELECTING_TABLE_TO_TRAIN,
            END: NEW,
            ANNOUNCEMENT:SELECTING_ACTION
            # End conversation altogether
        },
    )

#    choose_rule_to_download_conv = ConversationHandler(
#        entry_points=[CallbackQueryHandler(select_table, pattern=f"^{DOWNLOAD_RULES}$")],
#        states={
#            SELECTING_TABLE_TO_DOWNLOAD: [
#                CallbackQueryHandler(download_rule, pattern=f"^{PRESENT}$|^{IMPERATIVE}$|^{PAST}$|^{FUTURE}$")
#            ],
#        },
#        fallbacks=[
#            CommandHandler("stop", stop),
#            CallbackQueryHandler(start, pattern="^" + str(FINISH) + "$"),
#        ],
#        map_to_parent={
#            # After showing data return to top level menu
#            # SHOWING: SHOWING,
#            # Return to top level menu
#            END: NEW,
#            # End conversation altogether
#            #NEW: END,
#        },
#    )

    # Set up top level ConversationHandler (selecting action)
    # Because the states of the third level conversation map to the ones of the second level
    # conversation, we need to make sure the top level conversation can also handle them
    selection_table_handlers = [
        choose_table_to_train_conv,
        CallbackQueryHandler(select_table, pattern=f"^{DOWNLOAD_RULES}$"),
        CallbackQueryHandler(start, pattern="^" + str(END) + "$"),
    ]
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start), CallbackQueryHandler(start, pattern="^" + str(AGAIN) + "$")],
        states={
            SELECTING_ACTION: selection_table_handlers,  # type: ignore[dict-item]
            AGAIN:selection_table_handlers,
            DOWNLOAD_RULES: [CallbackQueryHandler(select_table, pattern=f"^{DOWNLOAD_RULES}$")],
            SELECTING_TABLE_TO_DOWNLOAD: [CallbackQueryHandler(download_rule, pattern=f"^{PRESENT}$|^{IMPERATIVE}$|^{PAST}$|^{FUTURE}$")],
            SELECTING_TABLE_TO_TRAIN: [CallbackQueryHandler(training_starting, pattern=f"^{PRESENT}$|^{IMPERATIVE}$|^{PAST}$|^{FUTURE}$")],
            TRAINING_STARTED: [CallbackQueryHandler(send_question, pattern=f"^{GET_QUESTION}$"),
                               CallbackQueryHandler(select_table, pattern=f"^{START_TRAINING}$")],            # type: ignore[dict-item]
            STOPPING: [CommandHandler("start", start)],
            NEW: [CallbackQueryHandler(start, pattern="^" + str(AGAIN) + "$")],
        },
        fallbacks=[
            CommandHandler("stop", stop),
            CommandHandler("start", start),
            CommandHandler("announcement", announcement),
            #CallbackQueryHandler(start, pattern="^" + str(FINISH_TRAINING) + "$"),
        ],
        map_to_parent={
            END: SELECTING_ACTION,
            AGAIN:SELECTING_ACTION,
            ANNOUNCEMENT:SELECTING_ACTION
        }
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()