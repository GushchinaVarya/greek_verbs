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
    PicklePersistence,
    filters,
)
from telegram.error import Forbidden, BadRequest


LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_file_handler = logging.FileHandler("log_trainig.log", encoding="utf-8")
_file_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT))

_console_handler = logging.StreamHandler()
_console_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT))

logging.basicConfig(level=logging.INFO, handlers=[_file_handler, _console_handler])
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def _u(update: Update) -> str:
    """Короткая строка с именем и chat_id для логов."""
    if update.callback_query:
        user = update.callback_query.from_user
        chat_id = update.callback_query.message.chat.id
    elif update.message:
        user = update.message.from_user
        chat_id = update.message.chat.id
    else:
        return "unknown"
    name = user.first_name or ""
    if user.last_name:
        name += f" {user.last_name}"
    return f"{name} (id={chat_id})"

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
    if int(chat_id) not in ADMINS_IDS:
        logger.warning("[ANNOUNCEMENT] Unauthorized attempt — %s", _u(update))
        return ANNOUNCEMENT

    logger.info("[ANNOUNCEMENT] Admin %s triggered broadcast", _u(update))
    user_ids, user_names = get_users()
    logger.info("[ANNOUNCEMENT] Recipients: %d users", len(user_ids))

    # Проверяем текст на корректность MarkdownV2 одним тестовым запросом
    # (отправляем самому себе), чтобы не падать у каждого пользователя
    use_markdown = True
    try:
        await update.message._bot.send_message(
            chat_id=int(chat_id),
            text=UPDATE_TEXT,
            parse_mode='MarkdownV2'
        )
        logger.info("[ANNOUNCEMENT] MarkdownV2 test passed — sending with formatting")
    except BadRequest as e:
        use_markdown = False
        logger.warning(
            "[ANNOUNCEMENT] UPDATE_TEXT contains invalid MarkdownV2 — "
            "will send as plain text. Reason: %s", e
        )
        await update.message._bot.send_message(
            chat_id=int(chat_id),
            text=UPDATE_TEXT
        )

    ok, blocked, failed = 0, 0, 0
    for user_id in user_ids:
        if int(user_id) == int(chat_id):
            ok += 1
            continue  # себе уже отправили выше в тесте
        try:
            await update.message._bot.send_message(
                chat_id=int(user_id),
                text=UPDATE_TEXT,
                parse_mode='MarkdownV2' if use_markdown else None
            )
            ok += 1
            logger.info("[ANNOUNCEMENT] Sent to chat_id=%s", user_id)
        except Forbidden:
            blocked += 1
            logger.warning("[ANNOUNCEMENT] Blocked by user chat_id=%s", user_id)
        except Exception:
            failed += 1
            logger.exception("[ANNOUNCEMENT] Error sending to chat_id=%s", user_id)

    logger.info("[ANNOUNCEMENT] Done — ok=%d, blocked=%d, failed=%d", ok, blocked, failed)
    return ANNOUNCEMENT


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Select an action: Adding parent/child or show data."""
    text = (
        "Что вы хотите сделать?\nВыберите режим: правила или тренировка"
    )
    buttons = [
        [
            InlineKeyboardButton(text="📘 Правила", callback_data=str(DOWNLOAD_RULES)),
            InlineKeyboardButton(text="🧠 Тренировка", callback_data=str(START_TRAINING)),
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
"""Привет! Я помогу тренировать греческие глаголы.
Выберите: Правила — чтобы вспомнить спряжения, или Тренировка — чтобы практиковаться.
Остановить тренировку: /stop"""
        )
        user = update.message.from_user
        chat_id = update.message.chat.id
        isnew = add_user(chat_id, user.first_name)
        await update.message.reply_text(text=text, reply_markup=keyboard)

    context.user_data[START_OVER] = False
    if isnew:
        logger.info("[START] NEW user registered — %s", _u(update))
    else:
        logger.info("[START] Returning user — %s", _u(update))
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
    logger.info("[MENU] %s pressed button '%s'", _u(update), context.user_data[MODE])
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    if context.user_data[MODE] == "читать правила":
        return SELECTING_TABLE_TO_DOWNLOAD
    if context.user_data[MODE] == "начать тренировку":
        return SELECTING_TABLE_TO_TRAIN

async def training_starting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Prompt user to input data for selected feature."""
    context.user_data[TABLE] = update.callback_query.data
    logger.info("[TRAIN] %s selected table '%s' (mode='%s')",
                _u(update), context.user_data[TABLE], context.user_data.get(MODE, "?"))
    text = f"""*{context.user_data[TABLE]}*

Как тренироваться:

1\. 🗒 Приготовьте ручку и бумагу
2\. Я пришлю фразу по\-русски — переведите на греческий
3\. Не знаете глагол? 💡 Откройте подсказку
4\. Откройте ответ ✅ и проверьте себя

_Не присылайте ответ боту — вы сами лучший судья\._
_Не забывайте про ударения\!_
"""

    buttons = [
        [
            InlineKeyboardButton(text="▶️ Начать тренировку", callback_data=str(GET_QUESTION)),
            InlineKeyboardButton(text="↩️ Назад", callback_data=str(START_TRAINING)),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=text, parse_mode='MarkdownV2', reply_markup=keyboard)

    return TRAINING_STARTED


async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Prompt user to input data for selected feature."""
    table = context.user_data[TABLE]
    chat_id = update.callback_query.from_user.id
    logger.info("[QUESTION] %s requested next card — table='%s'", _u(update), table)
    await update.callback_query.answer()
    try:
        text_q, text_h, text_a = get_question(table)
    except Exception:
        logger.exception("[QUESTION] Failed to get question from DB — table='%s', %s", table, _u(update))
        await update.callback_query._bot.send_message(
            chat_id=chat_id,
            text="Не удалось загрузить вопрос. Попробуйте ещё раз или перезапустите /start"
        )
        return TRAINING_STARTED

    buttons = [
        [
            InlineKeyboardButton(text="Еще", callback_data=str(GET_QUESTION)),
            InlineKeyboardButton(text="Завершить", callback_data=str(FINISH_TRAINING)),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    try:
        await update.callback_query._bot.send_message(chat_id=chat_id, text=text_q, parse_mode='MarkdownV2')
        await update.callback_query._bot.send_message(chat_id=chat_id, text=text_h, parse_mode='MarkdownV2')
        await update.callback_query._bot.send_message(chat_id=chat_id, text=text_a, parse_mode='MarkdownV2', reply_markup=keyboard)
    except Exception:
        logger.exception("[QUESTION] Failed to send question messages — %s", _u(update))

    return TRAINING_STARTED

async def download_rule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Prompt user to input data for selected feature."""
    context.user_data[TABLE] = update.callback_query.data
    table = context.user_data[TABLE]
    logger.info("[RULES] %s requested rules — table='%s'", _u(update), table)

    if table == 'настоящее время':
        files = PRESENT_RULES_FILES
    elif table == 'будущее время':
        files = FUTURE_RULES_FILES
    elif table == 'прошедшее время':
        files = PAST_RULES_FILES
    elif table == 'повелительное наклонение':
        files = IMPERATIVE_RULES
    else:
        logger.error("[RULES] Unknown table '%s' — %s", table, _u(update))
        return SELECTING_ACTION

    text = f"\nВот правила {table} ⬆️ \n\nВыберите дальнейшее действие.\n"
    chat_id = update.callback_query.from_user.id
    ready_flag = 0
    for filename in files:
        try:
            await update.callback_query._bot.send_document(chat_id=chat_id, document=filename)
            logger.info("[RULES] Sent file '%s' to %s", filename, _u(update))
            ready_flag = 1
        except Exception:
            logger.exception("[RULES] Failed to send file '%s' to %s", filename, _u(update))

    buttons = [
        [InlineKeyboardButton(text="📘 Правила", callback_data=str(DOWNLOAD_RULES))],
        [InlineKeyboardButton(text="🧠 Тренировка", callback_data=str(START_TRAINING))],
    ]
    if ready_flag:
        await update.callback_query._bot.send_message(
            chat_id=chat_id, text=text, reply_markup=InlineKeyboardMarkup(buttons)
        )
    return SELECTING_ACTION




async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """End Conversation by command."""
    logger.info("[STOP] %s used /stop command", _u(update))
    await update.message.reply_text("Вы завершили тренировку. Чтобы начать сначала введите /start")
    return END

async def finish_training(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """End Conversation by command."""
    logger.info("[FINISH] %s pressed 'Завершить' — table='%s'",
                _u(update), context.user_data.get(TABLE, "?"))
    buttons = [
        [InlineKeyboardButton(text="📘 Правила", callback_data=str(DOWNLOAD_RULES))],
        [InlineKeyboardButton(text="🧠 Тренировка", callback_data=str(START_TRAINING))],
    ]
    chat_id = update.callback_query.from_user.id
    await update.callback_query._bot.send_message(
        chat_id=chat_id,
        text="Вы завершили тренировку! \nВыберите дальнейшее действие:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return AGAIN

def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    persistence = PicklePersistence(filepath="bot_persistence.pkl")
    application = Application.builder().token(TG_TOKEN_TRAIN).persistence(persistence).build()



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