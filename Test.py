import requst_library


def requestV2():
    t = requst_library.get_movies_by_genre_vote_average_and_release_date("28", "7", "9", "2000-01-01", "2022-01-01", "2")
    print(t)


def request():
    t = requst_library.get_all_genre_id()
    print(t)

requestV2()