import requests

# Ваш API-ключ TMDb
api_key = "91ff54962f942374432143809e1da2ad"

# Параметры фильтрации
genre_id = 28  # Например, 28 — это жанр "Action"
vote_average_min = 7.0  # Минимальный рейтинг
vote_average_max = 9.0  # Максимальный рейтинг
release_date_start = "2020-01-01"  # Начало периода выпуска
release_date_end = "2022-12-31"  # Конец периода выпуска

# URL для запроса
url = "https://api.themoviedb.org/3/discover/movie"

# Параметры запроса
params = {
    "api_key": api_key,
    "language": "en-US",
    "sort_by": "popularity.desc",  # Сортировка по популярности
    "with_genres": genre_id,
    "vote_average.gte": vote_average_min,
    "vote_average.lte": vote_average_max,
    "primary_release_date.gte": release_date_start,
    "primary_release_date.lte": release_date_end,
    "page": 1  # Номер страницы (для пагинации)
}

# Выполнение запроса
response = requests.get(url, params=params)

# Проверка ответа
if response.status_code == 200:
    data = response.json()
    total_results = data.get("total_results", 0)  # Общее количество фильмов
    movies = data.get("results", [])

    print(f"Total Movies Found: {total_results}")  # Выводим общее количество фильмов

    for movie in movies:
        print(f"Title: {movie['title']}, Rating: {movie['vote_average']}, Release Date: {movie['release_date']}")
else:
    print(f"Ошибка: {response.status_code}, {response.text}")
