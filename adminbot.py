from config import TG_TOKEN_ADMIN

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

from db_functions import generate_csv, check_if_db_has_this, write_to_table

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# State definitions for top level conversation
#SELECTING_ACTION, SELECTING_TABLE, PRESENT, FUTURE, IMPERATIVE, PAST = map(chr, range(6))
SELECTING_ACTION, SELECTING_TABLE = map(chr, range(2))
PRESENT = "настоящее время"
FUTURE = "будущее время"
IMPERATIVE = "повелительное наклонение"
PAST = "прошедшее время"
# State definitions for second level conversation
DOWNLOAD_TABLE = 'скачать'
ADD_TO_TABLE = 'добавить в таблицу'
START_OVER, TYPING, CONFIRM, YES_ADD, YES_ADD_AND_DELETE, FINISH, AGAIN, STOPPING, NEW = map(chr, range(6, 15))
# State definitions for descriptions conversation
# Shortcut for ConversationHandler.END

MODE = 0
TABLE = 1
QUESTION = 2
ANSWER = 3
COMMENT = 4
HINT = 5
END = ConversationHandler.END


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Select an action: Adding parent/child or show data."""
    text = (
        "Выберите действие "
    )
    buttons = [
        [
            InlineKeyboardButton(text="Скачать таблицу глаголов", callback_data=str(DOWNLOAD_TABLE)),
            InlineKeyboardButton(text="Дополнить таблицу глаголов", callback_data=str(ADD_TO_TABLE)),
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
            "Это бот для работы с базой данных. Чтобы закончить работу с ботом введите /stop."
        )
        user = update.message.from_user
        await update.message.reply_text(text=text, reply_markup=keyboard)

    context.user_data[START_OVER] = False
    logger.info("User %s started conversation.", user.first_name)
    return SELECTING_ACTION


async def select_table(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Choose table."""
    text = "Выберите таблицу."
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

async def ask_for_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Prompt user to input data for selected feature."""
    context.user_data[TABLE] = update.callback_query.data
    logger.info(f"User {update.callback_query.from_user.first_name} selected table {context.user_data[TABLE]}, and the mode is {context.user_data[MODE]}")
    text = f"""Вы выбрали {context.user_data[TABLE]}\.
    
Напишите строку для данной таблицы в формате

*глагол по русски, глагол по гречески, комментарий, подсказка*

_Например:_

он покупает, αυτός αγοράζει, правильный глагол мужской род, используйте глагол αγοράζω"""
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=text, parse_mode='MarkdownV2')

    return TYPING

async def download_table(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Prompt user to input data for selected feature."""
    context.user_data[TABLE] = update.callback_query.data
    logger.info(f"User {update.callback_query.from_user.first_name} selected table {context.user_data[TABLE]}, and the mode is {context.user_data[MODE]}")
    ready_flag = 0
    filename, ready_flag = generate_csv(context.user_data[TABLE])
    text = f"Вот таблица {context.user_data[TABLE]} ⬆️"
    chat_id = update.callback_query.from_user.id
    await update.callback_query._bot.send_document(chat_id = chat_id, document=filename)
    buttons = [
        [
            InlineKeyboardButton(text="Сделать что-нибудь еще", callback_data=str(AGAIN)),
        ],
    ]
    if ready_flag == 1:
        await update.callback_query._bot.send_message(chat_id = chat_id, text=text,
                                                  reply_markup=InlineKeyboardMarkup(buttons))
    context.user_data[START_OVER] = True
    return END


async def save_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Save input for feature and return to feature selection."""
    user_data = context.user_data
    user_data[QUESTION] = update.message.text.split(',')[0].strip().lower()
    user_data[ANSWER] = update.message.text.split(',')[1].strip().lower()
    user_data[COMMENT] = update.message.text.split(',')[2].strip().lower()
    user_data[HINT] = update.message.text.split(',')[3].strip().lower()
    buttons_add = [
        [
            InlineKeyboardButton(text="Добавить в базу", callback_data=str(YES_ADD)),
        ],
        [
            InlineKeyboardButton(text="Ввести заново", callback_data=str(context.user_data[TABLE])),
        ],
    ]
    buttons_add_and_del = [
        [
            InlineKeyboardButton(text="Добавить и удалить старую запись", callback_data=str(YES_ADD)),
        ],
        [
            InlineKeyboardButton(text="Ввести заново", callback_data=str(context.user_data[TABLE])),
        ],
    ]
    text = f"""
_Вы ввели_:
    
ВОПРОС: {user_data[QUESTION]} 
ОТВЕТ: {user_data[ANSWER]} 
КОММЕНТАРИЙ: {user_data[COMMENT]}
ПОДСКАЗКА: {user_data[HINT]}"""

    text_to_add, delete_option, = check_if_db_has_this(context.user_data[TABLE], user_data[QUESTION])
    if delete_option==0:
        keyboard = InlineKeyboardMarkup(buttons_add)
    if delete_option==1:
        keyboard = InlineKeyboardMarkup(buttons_add_and_del)
    logger.info(
        f"User {update.message.from_user.first_name} selected table {context.user_data[TABLE]} and wrote {user_data[QUESTION]}, {user_data[ANSWER]}, {user_data[COMMENT]}, {user_data[HINT]}, delete option = {delete_option}")
    await update.message.reply_text(text=text_to_add+text, parse_mode='MarkdownV2', reply_markup=keyboard)
    return CONFIRM

async def write_to_db(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Save input for feature and return to feature selection."""
    user_data = context.user_data


    buttons = [
        [
            InlineKeyboardButton(text="Добавить eще", callback_data=str(context.user_data[TABLE])),
            InlineKeyboardButton(text="Завершить ввод", callback_data=str(FINISH)),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    deleted = write_to_table(user_data[TABLE], user_data[QUESTION], user_data[ANSWER], user_data[COMMENT], user_data[HINT])
    if deleted:
        logger.info(f"User {update.callback_query.from_user.first_name} wrote {user_data[QUESTION]}, {user_data[ANSWER]}, {user_data[COMMENT]}, {user_data[HINT]} to table {context.user_data[TABLE]} DB , old item deleted")
    else:
        logger.info(f"User {update.callback_query.from_user.first_name} wrote {user_data[QUESTION]}, {user_data[ANSWER]}, {user_data[COMMENT]}, {user_data[HINT]} to table {context.user_data[TABLE]} DB")
    await update.callback_query.edit_message_text(text="записано в базу", reply_markup=keyboard)
    return SELECTING_TABLE

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """End Conversation by command."""
    logger.info(
        f"User {update.callback_query.from_user.first_name} finished. ")
    await update.message.reply_text("Вы завершили ввод. Чтобы начать сначала введите /start")
    #await update.callback_query.edit_message_text(text="Ok")
    #context.user_data[START_OVER] = True

    return END

async def finish_adding(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """End Conversation by command."""
    buttons = [
        [
            InlineKeyboardButton(text="Сделать что-нибудь еще", callback_data=str(AGAIN)),
        ],
    ]
    await update.callback_query.edit_message_text(text="Вы дополнили таблицу", reply_markup=InlineKeyboardMarkup(buttons))
    context.user_data[START_OVER] = True
    return END

def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TG_TOKEN_ADMIN).build()



    # Set up second level ConversationHandler (adding a person)
    choose_table_to_add_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(select_table, pattern=f"^{ADD_TO_TABLE}$", )],
        states={
            SELECTING_TABLE: [
                CallbackQueryHandler(ask_for_input, pattern=f"^{PRESENT}$|^{IMPERATIVE}$|^{PAST}$|^{FUTURE}$")
            ],
            TYPING: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_input)],
            CONFIRM: [
                CallbackQueryHandler(write_to_db, pattern="^" + str(YES_ADD) + "$"),
                CallbackQueryHandler(ask_for_input, pattern=f"^{PRESENT}$|^{IMPERATIVE}$|^{PAST}$|^{FUTURE}$")
            ],
            NEW: [CallbackQueryHandler(start, pattern="^" + str(AGAIN) + "$")],
        },
        fallbacks=[
            CommandHandler("stop", stop),
            CallbackQueryHandler(finish_adding, pattern="^" + str(FINISH) + "$"),
        ],
        map_to_parent={
            # After showing data return to top level menu
            #SHOWING: SHOWING,
            # Return to top level menu
            END: NEW,
            # End conversation altogether
        },
    )

    choose_table_to_download_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(select_table, pattern=f"^{DOWNLOAD_TABLE}$")],
        states={
            SELECTING_TABLE: [
                CallbackQueryHandler(download_table, pattern=f"^{PRESENT}$|^{IMPERATIVE}$|^{PAST}$|^{FUTURE}$")
            ],
            NEW: [CallbackQueryHandler(start, pattern="^" + str(AGAIN) + "$")],
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
        choose_table_to_add_conv,
        choose_table_to_download_conv,
        #CallbackQueryHandler(download_table, pattern="^" + str(SHOWING) + "$"),
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
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()