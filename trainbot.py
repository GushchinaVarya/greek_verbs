from config import TG_TOKEN_TRAIN
from db_functions import get_question

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

#from db_functions import generate_csv, check_if_db_has_this, write_to_table

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# State definitions for top level conversation
SELECTING_ACTION, SELECTING_TABLE = map(chr, range(2))
PRESENT = "настоящее время"
FUTURE = "будущее время"
IMPERATIVE = "повелительное наклонение"
PAST = "прошедшее время"
# State definitions for second level conversation
DOWNLOAD_RULES = 'читать правила'
START_TRAINING = 'начать тренировку'
START_OVER, TYPING, CONFIRM, YES_ADD, YES_ADD_AND_DELETE, FINISH, AGAIN, STOPPING, NEW, TRAINING_STARTED, GET_QUESTION, BACK = map(chr, range(6, 18))
# State definitions for descriptions conversation
# Shortcut for ConversationHandler.END

MODE = 0
TABLE = 1
QUESTION = 2
ANSWER = 3
COMMENT = 4
END = ConversationHandler.END


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Select an action: Adding parent/child or show data."""
    text = (
        "Выберите действие "
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
        #await update.callback_query.answer()
        user = update.callback_query.from_user
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    else:
        await update.message.reply_text(
"""Привет! Я бот, который поможет запомнить как меняются глаголы в греческом языке.

Нажмите "Почитать правила" если хотите вспомнить как правильно спрягать глаголы в зависимости от рода и времени. Либо начинайте тренироваться! Я вам помогу! 

Закончить тренироваться - /stop. """
        )
        user = update.message.from_user
        await update.message.reply_text(text=text, reply_markup=keyboard)

    context.user_data[START_OVER] = False
    logger.info("User %s started conversation.", user.first_name)
    return SELECTING_ACTION


async def select_table(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Choose table."""
    text = "Выберите какие глаголы будем учить."
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

    return SELECTING_TABLE

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
            InlineKeyboardButton(text="Завершить", callback_data=str(FINISH)),
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
        filename = 'present_rules.pdf'
    if context.user_data[TABLE] == 'будущее время':
        filename = 'present_rules.pdf'
    if context.user_data[TABLE] == 'прошедшее время':
        filename = 'present_rules.pdf'
    if context.user_data[TABLE] == 'повелительное наклонение':
        filename = 'present_rules.pdf'
    text = f"Вот таблица {context.user_data[TABLE]} ⬆️"
    chat_id = update.callback_query.from_user.id
    await update.callback_query._bot.send_document(chat_id = chat_id, document=filename)
    ready_flag = 1
    buttons = [
        [
            InlineKeyboardButton(text="В начало", callback_data=str(AGAIN)),
        ],
    ]
    if ready_flag == 1:
        await update.callback_query._bot.send_message(chat_id = chat_id, text=text,
                                                  reply_markup=InlineKeyboardMarkup(buttons))
    context.user_data[START_OVER] = True
    return END




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
            InlineKeyboardButton(text="В начало", callback_data=str(AGAIN)),
        ],
    ]
    chat_id = update.callback_query.from_user.id
    await update.callback_query._bot.send_message(chat_id = chat_id, text="Вы завершили тренировку!", reply_markup=InlineKeyboardMarkup(buttons))
    context.user_data[START_OVER] = True
    return END

def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TG_TOKEN_TRAIN).build()



    # Set up second level ConversationHandler (adding a person)
    choose_table_to_train_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(select_table, pattern=f"^{START_TRAINING}$", )],
        states={
            SELECTING_TABLE: [
                CallbackQueryHandler(training_starting, pattern=f"^{PRESENT}$|^{IMPERATIVE}$|^{PAST}$|^{FUTURE}$"),
            ],
            TRAINING_STARTED: [CallbackQueryHandler(send_question, pattern=f"^{GET_QUESTION}$"),
                               CallbackQueryHandler(select_table, pattern=f"^{START_TRAINING}$")],
        },
        fallbacks=[
            CommandHandler("stop", stop),
            CallbackQueryHandler(finish_training, pattern="^" + str(FINISH) + "$"),
        ],
        map_to_parent={
            # After showing data return to top level menu
            #SHOWING: SHOWING,
            # Return to top level menu
            BACK: SELECTING_TABLE,
            END: NEW,
            # End conversation altogether
        },
    )

    choose_rule_to_download_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(select_table, pattern=f"^{DOWNLOAD_RULES}$")],
        states={
            SELECTING_TABLE: [
                CallbackQueryHandler(download_rule, pattern=f"^{PRESENT}$|^{IMPERATIVE}$|^{PAST}$|^{FUTURE}$")
            ],
        },
        fallbacks=[
            CommandHandler("stop", stop),
            CallbackQueryHandler(start, pattern="^" + str(FINISH) + "$"),
        ],
        map_to_parent={
            # After showing data return to top level menu
            # SHOWING: SHOWING,
            # Return to top level menu
            END: NEW,
            # End conversation altogether
            #NEW: END,
        },
    )

    # Set up top level ConversationHandler (selecting action)
    # Because the states of the third level conversation map to the ones of the second level
    # conversation, we need to make sure the top level conversation can also handle them
    selection_table_handlers = [
        choose_table_to_train_conv,
        choose_rule_to_download_conv,
        CallbackQueryHandler(start, pattern="^" + str(END) + "$"),
    ]
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start), CallbackQueryHandler(start, pattern="^" + str(AGAIN) + "$")],
        states={
            SELECTING_ACTION: selection_table_handlers,  # type: ignore[dict-item]
            SELECTING_TABLE: selection_table_handlers,  # type: ignore[dict-item]
            STOPPING: [CommandHandler("start", start)],
            NEW: [CallbackQueryHandler(start, pattern="^" + str(AGAIN) + "$")],
        },
        fallbacks=[
            CommandHandler("stop", stop),
            CallbackQueryHandler(start, pattern="^" + str(FINISH) + "$"),
        ],
        map_to_parent={
            END: SELECTING_ACTION
        }
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()