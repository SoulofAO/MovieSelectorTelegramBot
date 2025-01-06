from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import requst_library

# Фильмы для примера (замени на базу данных или API)
MOVIES = [
    {"title": "Inception", "genre": "Sci-Fi", "year": 2010, "rating": 8.8},
    {"title": "The Matrix", "genre": "Sci-Fi", "year": 1999, "rating": 8.7},
    {"title": "Interstellar", "genre": "Sci-Fi", "year": 2014, "rating": 8.6},
    {"title": "Parasite", "genre": "Drama", "year": 2019, "rating": 8.6},
    {"title": "The Dark Knight", "genre": "Action", "year": 2008, "rating": 9.0}
]

user_preferences = {}

def find_genre_by_name(all_genre_id, name):
    for item in all_genre_id:
        if item['name'] == name:
            return item

def find_genre_by_id(all_genre_id, id):
    for item in all_genre_id:
        if item['id'] == id:
            return item

async def send_message(update: Update, send_string):
    if update.callback_query:
        await update.callback_query.edit_message_text(send_string)
    else:
        await update.message.reply_text(send_string)


async def send_reply_markup(update: Update, start_string, reply_markup):
    if update.callback_query:
        await update.callback_query.reply_text(start_string, reply_markup=reply_markup)
    else:
        await update.message.reply_text(start_string, reply_markup=reply_markup)

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
    await send_message(update, "Привет! Я помогу подобрать фильм. Укажи жанр, год выпуска и рейтинг.")

    user_preferences[update.effective_user.id] = {}
    await ask_genre(update, context)


async def ask_genre(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = get_user_id(update)
    await send_message(update, "Выбераем жанр")
    all_genre_id = requst_library.get_all_genre_id()
    user_preferences[user_id]['all_genre_id'] = all_genre_id
    keyboard = []
    for item in user_preferences[user_id]['all_genre_id']:
        keyboard.append([InlineKeyboardButton(item['name'], callback_data=("genre:" + str(item['id'])+":"+item['name']))])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await send_reply_markup(update, "Выбери жанр", reply_markup)

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
        await send_message(update, f"Выбран жанр: {genre_name}. Теперь укажи год выпуска (например, 2000-2020):")

    elif data.startswith("year:"):
        year_range = tuple(map(int, data.split(":")[1].split("-")))
        user_preferences[user_id]['min_year'] = year_range[0]+"-01" + "-01"
        user_preferences[user_id]['max_year'] = year_range[1]+"-11" + "-29"
        await send_message(update, f"Год выпуска: {year_range}. Укажи рейтинг (например, 7-9):")

    elif data.startswith("rating:"):
        rating_range = tuple(map(float, data.split(":")[1].split("-")))
        user_preferences[user_id]['min_rating'] = rating_range[0]
        user_preferences[user_id]['max_rating'] = rating_range[0]

        prefs = user_preferences[user_id]
        results = requst_library.get_movies_by_genre_vote_average_and_release_date(str(user_preferences[user_id]['genre_id']),
                                                                                   user_preferences[user_id]['min_rating'],
                                                                                   user_preferences[user_id]['max_rating'],
                                                                                   user_preferences[user_id]['min_year'],
                                                                                   user_preferences[user_id]['max_year'])
        if results:
            movie_list = "\n".join([f"{movie['title']} ({movie['release_date']}) - {movie['vote_average']}" for movie in results])
            keyboard = [[InlineKeyboardButton("Предложить ещё", callback_data="repeat:yes")],
                        [InlineKeyboardButton("Начать заново", callback_data="restart")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await send_reply_markup(update, f"Рекомендованные фильмы:\n{movie_list}", reply_markup)
        else:
            await send_reply_markup(update, "Нет фильмов, соответствующих запросу. Начни заново.",
                                    InlineKeyboardMarkup(
                                        [[InlineKeyboardButton("Начать заново", callback_data="restart")]]))

    elif data == "restart":
        user_preferences[user_id] = {}
        await send_message(update, "Начнём заново. Укажи жанр.")
        await ask_genre(update, context)

    elif data == "repeat:yes":
        prefs = user_preferences[user_id]
        results = filter_movies(prefs['genre'], prefs['year_range'], prefs['rating_range'])
        movie_list = "\n".join([f"{movie['title']} ({movie['year']}) - {movie['rating']}" for movie in results])
        keyboard = [[InlineKeyboardButton("Предложить ещё", callback_data="repeat:yes")],
                    [InlineKeyboardButton("Начать заново", callback_data="restart")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await send_reply_markup(update, f"Рекомендованные фильмы:\n{movie_list}", reply_markup)


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    text = update.message.text

    if 'genre' not in user_preferences.get(user_id, {}):
        await ask_genre(update, context)
    elif 'year_range' not in user_preferences[user_id]:
        try:
            year_range = tuple(map(int, text.split("-")))
            user_preferences[user_id]['year_range'] = year_range
            await send_message(update, "Укажи рейтинг (например, 7-9):")
        except ValueError:
            await send_message(update, "Неправильный формат. Укажи год выпуска (например, 2000-2020):")
    elif 'rating_range' not in user_preferences[user_id]:
        try:
            rating_range = tuple(map(float, text.split("-")))
            user_preferences[user_id]['rating_range'] = rating_range
            prefs = user_preferences[user_id]
            results = filter_movies(prefs['genre'], prefs['year_range'], prefs['rating_range'])
            if results:
                movie_list = "\n".join([f"{movie['title']} ({movie['year']}) - {movie['rating']}" for movie in results])
                keyboard = [[InlineKeyboardButton("Предложить ещё", callback_data="repeat:yes")],
                            [InlineKeyboardButton("Начать заново", callback_data="restart")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await send_reply_markup(update, f"Рекомендованные фильмы:\n{movie_list}", reply_markup)
            else:
                await send_message(update, "Нет фильмов, соответствующих запросу. Начни заново.")
                await ask_genre(update, context)
        except ValueError:
            await send_message(update, "Неправильный формат. Укажи рейтинг (например, 7-9):")


if __name__ == "__main__":
    app = ApplicationBuilder().token("7712165249:AAELe4ZDnmAkFYIa74IRtp5ng-IsNSuVxng").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Бот запущен!")
    app.run_polling()
