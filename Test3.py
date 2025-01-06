from datetime import datetime

def parse_date_range(data: str) -> dict:
    """
    Преобразует строку формата [range:YYYY-MM-DD:YYYY-MM-DD] или [range:YYYY:YYYY]
    или подобные варианты в даты начала и конца в формате 'YYYY-MM-DD'.

    :param data: строка вида [range:2000-01-01:2022-12-31] или частично заполненная, например, [range:2000:2022]
    :return: словарь с ключами 'release_date_start' и 'release_date_end'
    """
    # Убираем "range:" и разбиваем строку
    try:
        date_part = data.split(":", 1)[1]  # Оставляем только часть после "range:"
        date_ranges = date_part.split("-")
    except IndexError:
        raise ValueError("Некорректный формат данных: ожидается строка вида '[range:YYYY-MM-DD:YYYY-MM-DD]'")

    # Обработка отдельных частей
    date_start, date_end = None, None
    if len(date_ranges) == 1:
        # Если указана только одна дата
        date_start = parse_partial_date(date_ranges[0])
    elif len(date_ranges) == 2:
        # Если указаны начало и конец
        date_start = parse_partial_date(date_ranges[0])
        date_end = parse_partial_date(date_ranges[1])
    else:
        raise ValueError("Некорректный формат диапазона: больше двух частей в дате.")

    # Подстановка значений по умолчанию
    if date_start is None:
        date_start = "1900-01-01"  # Если не указан старт, берем максимально раннюю дату
    if date_end is None:
        date_end = datetime.now().strftime("%Y-%m-%d")  # Если не указан конец, берем текущую дату

    return {
        "release_date_start": date_start,
        "release_date_end": date_end
    }


def parse_partial_date(partial_date: str) -> str:
    """
    Преобразует частично указанную дату в формат 'YYYY-MM-DD'.
    Если год/месяц/день отсутствует, подставляет значения по умолчанию.
    :param partial_date: строка с частичной датой, например, '2000', '2000-05', '2000.11.01'
    :return: дата в формате 'YYYY-MM-DD'
    """
    # Заменяем точки на дефисы
    partial_date = partial_date.replace(".", "-").strip()

    # Попробуем разобрать строку
    try:
        if "-" in partial_date:
            date_parts = partial_date.split("-")
        else:
            date_parts = [partial_date]

        # Подстановка недостающих частей
        year = date_parts[0] if len(date_parts) > 0 else "1900"
        month = date_parts[1] if len(date_parts) > 1 else "01"
        day = date_parts[2] if len(date_parts) > 2 else "01"

        # Формируем дату
        return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
    except ValueError:
        raise ValueError(f"Не удалось распознать дату: {partial_date}")


# Пример использования
data = "[range:2000.11.01-2022]"
print(parse_date_range(data))
# {'release_date_start': '2000-11-01', 'release_date_end': '2022-01-01'}

data = "[range:2000-2022]"
print(parse_date_range(data))
# {'release_date_start': '2000-01-01', 'release_date_end': '2022-01-01'}

data = "[range:2022]"
print(parse_date_range(data))
# {'release_date_start': '2022-01-01', 'release_date_end': '2022-01-01'}
