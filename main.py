import chat_gpt_integration
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import requst_library
from telegram.ext import CallbackContext
from enum import Enum

user_preferences = {}

def find_genre_by_name(all_genre_id, name):
    for item in all_genre_id:
        if item['name'] == name:
            return item

def find_genre_by_id(all_genre_id, id):
    for item in all_genre_id:
        if item['id'] == id:
            return item


def format_movies_to_text(movies):
    if not movies:
        return "Список фильмов пуст."

    formatted_text ="\n"
    for index, movie in enumerate(movies, start=1):
        formatted_text += (
            f"{index}. Название: {movie['title']}\n"
            f"   Рейтинг: {movie['vote_average']}\n"
            f"   Дата выхода: {movie['release_date']}\n"
        )
    return formatted_text

def is_valid_rating_range(text):
    try:
        parts = text.split("-")
        if len(parts) != 2:
            return False

        min_rating, max_rating = map(float, parts)

        if 0.0 <= min_rating <= 10.0 and 0.0 <= max_rating <= 10.0 and min_rating <= max_rating:
            return True
        else:
            return False
    except ValueError:
        return False

def is_valid_year_range(text):
    try:
        parts = text.split("-")
        if len(parts) != 2:
            return False

        min_year, max_year= map(float, parts)

        if 1500 <= min_year <= 40000 and 1500  <= max_year <= 40000 and min_year <= max_year:
            return True
        else:
            return False
    except ValueError:
        return False

async def send_message(update: Update, context: CallbackContext, text: str, **kwargs):
    """
    Универсальная функция для отправки сообщений.
    """
    if update.callback_query:
        # Попытка редактировать сообщение, если это callback_query
        try:
            await update.callback_query.edit_message_text(text, **kwargs)
        except Exception as e:
            # Если редактирование не удается, отправляем новое сообщение
            await context.bot.send_message(
                chat_id=update.callback_query.message.chat_id,
                text=text,
                **kwargs
            )
    elif update.message:
        # Обычное сообщение
        await update.message.reply_text(text, **kwargs)
    else:
        # Если ни callback_query, ни message нет, используем context.bot
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text, **kwargs)


async def send_reply_markup(update: Update, context: CallbackContext, text: str, reply_markup=None, **kwargs):
    """
    Универсальная функция для отправки сообщений с клавиатурой.
    """
    if update.callback_query:
        # Попытка отправить новое сообщение с клавиатурой
        await context.bot.send_message(
            chat_id=update.callback_query.message.chat_id,
            text=text,
            reply_markup=reply_markup,
            **kwargs
        )
    elif update.message:
        # Обычное сообщение с клавиатурой
        await update.message.reply_text(text, reply_markup=reply_markup, **kwargs)
    else:
        # Если ни callback_query, ни message нет, используем context.bot
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=reply_markup,
            **kwargs
        )
def get_user_id(update: Update):
    if update.effective_user:
        return update.effective_user.id
    elif update.callback_query and update.callback_query.from_user:
        return update.callback_query.from_user.id
    elif update.inline_query and update.inline_query.from_user:
        return update.inline_query.from_user.id
    else:
        raise ValueError("Не удалось определить user_id")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_message(update,context, "Привет! Я помогу подобрать фильм. Укажи жанр, год выпуска и рейтинг.")
    await set_commands(app)
    user_preferences[update.effective_user.id] = {}
    await ask_genre(update, context)

async def ask_genre(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = get_user_id(update)
    if user_id not in user_preferences:
        user_preferences[user_id] = {}
    await send_message(update,context, "Выбераем жанр")
    all_genre_id = requst_library.get_all_genre_id()
    user_preferences[user_id]['all_genre_id'] = all_genre_id
    keyboard = []
    for item in user_preferences[user_id]['all_genre_id']:
        keyboard.append([InlineKeyboardButton(item['name'], callback_data=("genre:" + str(item['id'])+":"+item['name']))])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await send_reply_markup(update, context, "Выбери жанр", reply_markup)

class ERequestResultStatus(Enum):
    Sucsess = 0
    NoItem = 1


async def get_result(update, context):
    user_id = get_user_id(update)
    result= requst_library.get_movies_by_genre_vote_average_and_release_date(
        str(user_preferences[user_id]['genre_id']),
        user_preferences[user_id]['min_rating'],
        user_preferences[user_id]['max_rating'],
        user_preferences[user_id]['min_year'],
        user_preferences[user_id]['max_year'],
        user_preferences[user_id]['page'])
    if result:
        return {"status":ERequestResultStatus.Sucsess, "result": result}
    else:
        return {ERequestResultStatus.NoItem, []}

async def base_show_list_requst(update, context, result):
    user_id = get_user_id(update)
    user_preferences[user_id]['last_result_films'] = result["result"]["movies_on_page"]
    if (result["status"] == ERequestResultStatus.Sucsess):
        if (int(result["result"]["total_results_count"]) > 0 and int(result["result"]["total_results_count"]) < 20):
            keyboard = [[InlineKeyboardButton("Начать заново", callback_data="restart")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await send_reply_markup(update, context, "Всего найдено фильмов " + str(len(format_movies_to_text(result["result"]["movies_on_page"])))
                                                    +"\n"+"Вот предложенный список фильмов:" + format_movies_to_text(result["result"]["movies_on_page"]), reply_markup)

        elif (int(user_preferences[user_id]['page']) * 20 + 20 > int(result["result"]["total_results_count"])):
            keyboard = [[InlineKeyboardButton("На предыдущую страницу", callback_data="previus_page_result")],
                        [InlineKeyboardButton("На первую страницу", callback_data="on_first_page")],
                        [InlineKeyboardButton("Начать заново", callback_data="restart")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await send_reply_markup(update, context, "Всего найдено фильмов " + str(len(format_movies_to_text(result["result"]["movies_on_page"])))
                                                    +"\n"+"Вот предложенный список фильмов:" + format_movies_to_text(result["result"]["movies_on_page"]), reply_markup)

        elif (int(user_preferences[user_id]['page']) * 20 < 20):
            keyboard = [[InlineKeyboardButton("На следующую страницу", callback_data="next_page_result")],
                        [InlineKeyboardButton("Начать заново", callback_data="restart")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await send_reply_markup(update, context, "Всего найдено фильмов " + str(len(format_movies_to_text(result["result"]["movies_on_page"])))
                                                    +"\n"+"Вот предложенный список фильмов:" + format_movies_to_text(result["result"]["movies_on_page"]), reply_markup)

        elif (int(result["result"]["total_results_count"]) >= int(user_preferences[user_id]['page']) * 20 and int(
                user_preferences[user_id]['page']) * 20 >= 20):
            keyboard = [[InlineKeyboardButton("На следующую страницу", callback_data="next_page_result")],
                        [InlineKeyboardButton("На предыдущую страницу", callback_data="previus_page_result")],
                        [InlineKeyboardButton("Начать заново", callback_data="restart")]
                        ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await send_reply_markup(update, context, "Всего найдено фильмов " + str(len(format_movies_to_text(result["result"]["movies_on_page"])))
                                                    +"\n"+"Вот предложенный список фильмов:" + format_movies_to_text(result["result"]["movies_on_page"]), reply_markup)

    else:
        keyboard = [[InlineKeyboardButton("Начать заново", callback_data="restart")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await send_reply_markup(update, context, f"Нет элементов", reply_markup)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    if data.startswith("genre:"):
        genre_id = data.split(":")[1]
        genre_name = data.split(":")[2]
        user_preferences[user_id]['genre_id'] = int(genre_id)
        user_preferences[user_id]['genre_name'] = genre_name
        await send_message(update, context, f"Выбран жанр: {genre_name}. Теперь укажи год выпуска (например, 2000-2020):")

    elif data == "restart":
        user_preferences[user_id] = {}
        await send_message(update, context, "Начнём заново. Укажи жанр.")
        await ask_genre(update, context)

    elif data == "on_first_page_result":
        user_preferences[user_id]['page'] = "0"
        result = await get_result(update, context)
        await base_show_list_requst(update, context, result)

    elif data == "previous_page_result":
        user_preferences[user_id]['page'] = str(int(user_preferences[user_id]['page']) - 1)
        result = await get_result(update, context)
        await base_show_list_requst(update, context, result)

    elif data == "next_page_result":
        user_preferences[user_id]['page'] = str(int(user_preferences[user_id]['page']) + 1)
        result = await get_result(update, context)
        await base_show_list_requst(update, context, result)
    else:
        send_message("Неизвестная ошибка. Попробуйте позже")
async def command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = get_user_id(update)
    text = update.message.text
    if text.startswith("/resturt"):
        start(update, context)
    elif text.startswith("/chat_gpt_request"):
        if user_id not in user_preferences:
            user_preferences[user_id] = {}
        chat_gpt_requst_text = await chat_gpt_integration.GetChatGptRequest(text, user_preferences[user_id])
        if (chat_gpt_requst_text.startswith("Error")):
            await send_message(update, context, "Упс. Что то пошло не так. Попробуйте позже")
        else:
            await send_message(update, context, chat_gpt_requst_text)
    elif text.startswith("/continue"):
        await message_handler(update, context)

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = get_user_id(update)
    text = update.message.text
    if user_id not in user_preferences:
        user_preferences[user_id] = {}

    if 'genre_id' not in user_preferences.get(user_id, {}):
        await ask_genre(update, context)
    elif 'min_year' not in user_preferences[user_id] and 'max_year' not in user_preferences[user_id]:
        if(is_valid_year_range(text)):
            year_range = tuple(map(str, text.split("-")))
            user_preferences[user_id]['min_year'] = year_range[0] + "-01" + "-01"
            user_preferences[user_id]['max_year'] = year_range[1] + "-11" + "-29"
            await send_message(update,context, "Укажи рейтинг (например, 7-9):")
        else:
            chat_gpt_requst_text = await chat_gpt_integration.GetChatGptRequest(text, user_preferences[user_id])
            if (chat_gpt_requst_text.startswith("Error")):
                await send_message(update,context, "Неправильный формат. Укажи год выпуска (например, 2000-2020):")
            else:
                await send_message(update, context, chat_gpt_requst_text)
                await send_message(update, context, "Неправильный формат. Укажи год выпуска (например, 2000-2020):")
    elif 'min_rating' not in user_preferences[user_id] and 'max_rating' not in user_preferences[user_id]:
        if(is_valid_rating_range(text)):
            rating_range = tuple(map(float, text.split("-")))
            user_preferences[user_id]['min_rating'] = rating_range[0]
            user_preferences[user_id]['max_rating'] = rating_range[1]
            user_preferences[user_id]['page'] = "1"
            result = await get_result(update, context)
            await base_show_list_requst(update, context, result)
        else:
            chat_gpt_requst_text = await chat_gpt_integration.GetChatGptRequest(text, user_preferences[user_id])
            if (chat_gpt_requst_text.startswith("Error")):
                await send_message(update, context, "Неправильный формат. Укажи рейтинг (например, 7-9):")
            else:
                await send_message(update, context, chat_gpt_requst_text)
                await send_message(update, context, "Неправильный формат. Укажи рейтинг (например, 7-9):")
    else:
        chat_gpt_requst_text = await chat_gpt_integration.GetChatGptRequest(text, user_preferences[user_id])
        if (chat_gpt_requst_text.startswith("Error")):
            await send_message("Неизвестная ошибка. Попробуйте позже")
        else:
            await send_message(update, context, chat_gpt_requst_text)

async def set_commands(app):
    """Устанавливаем команды для бота"""
    commands = [
        BotCommand("start", "Запустить бота"),
        BotCommand("chat_gpt_request", "Задать специфичный вопрос"),
        BotCommand("continue", "Продолжить"),
        BotCommand("restart", "Перезапустить бота"),

    ]
    await app.bot.set_my_commands(commands)

if __name__ == "__main__":
    app = ApplicationBuilder().token("7712165249:AAELe4ZDnmAkFYIa74IRtp5ng-IsNSuVxng").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    app.add_handler(MessageHandler(filters.TEXT & filters.COMMAND, command_handler))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Бот запущен!")
    app.run_polling()
