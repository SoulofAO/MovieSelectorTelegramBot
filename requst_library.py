import requests

api_key = "91ff54962f942374432143809e1da2ad"

def get_movies_by_genre_vote_average_and_release_date(genre_id, vote_average_min, vote_average_max, release_date_start, release_date_end):
    url = "https://api.themoviedb.org/3/discover/movie"

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

    response = requests.get(url, params=params)

    answer = []

    if response.status_code == 200:
        movies = response.json().get("results", [])
        for movie in movies:
            answer.append({'title':movie['title'], 'vote_average':movie['vote_average'],'release_date': movie['release_date']})
    else:
        print(f"Ошибка: {response.status_code}, {response.text}")

    return answer

def get_all_genre_id():
    url = f"https://api.themoviedb.org/3/genre/movie/list"

    # Параметры запроса
    params = {
        "api_key": api_key,
        "language": "en-US"  # Язык результатов (например, "ru-RU" для русского)
    }

    # Выполнение запроса
    response = requests.get(url, params=params)

    answer = []

    # Проверка ответа
    if response.status_code == 200:
        genres = response.json().get("genres", [])
        for genre in genres:
            answer.append({'id':genre['id'], 'name': genre['name']})
    else:
        print(f"Ошибка: {response.status_code}, {response.text}")

    return answer
