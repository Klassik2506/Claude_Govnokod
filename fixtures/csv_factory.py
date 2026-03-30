"""
Генератор тестовых CSV-файлов.

Создаёт валидные и невалидные CSV-файлы для приёмочного тестирования
технической валидации импорта в систему «Мастер обзоров».
"""
import csv
import io
import os
import tempfile
from pathlib import Path

from config import (
    FIELD_SEPARATOR, FILE_ENCODING, HEADERS, LINE_SEPARATOR,
)


def _valid_row() -> list[str]:
    """Одна корректная строка данных (25 полей)."""
    return [
        "РФ",                          # ГруппаГ
        "ЦФО",                         # Округ
        "Московская область",          # Регион
        "г. Подольск",                 # Район
        "пгт. Володарское",           # Город
        "1",                           # Кол-во
        "763855",                      # Номер
        "01.09.2025",                  # Дата
        "0005.0005.0056.1153",         # Код
        "Перебои в электроснабжении", # Наименование
        "311 просьба гражданина*",    # Тип
        "ФОИВ",                        # Комп
        "РФ",                          # ПВ
        "Росздравнадзор",             # Орган
        "Министерство",               # Группа
        "1",                           # ОЖ
        "0",                           # Контр
        "Иванов И.И.",                # Сотрудник
        "интернет",                    # Вид письма
        "Росздравнадзор",             # ОрганССТУ
        "Федеральные службы России",  # ГруппаССТУ
        "по компетенции",             # Цель напр.
        "Национальный проект",        # Событие
        "0",                           # Повторность
        "УРОГ",                        # Приемная
    ]


def build_csv(
    rows: list[list[str]] | None = None,
    headers: list[str] | None = None,
    encoding: str = FILE_ENCODING,
    separator: str = FIELD_SEPARATOR,
    line_ending: str = LINE_SEPARATOR,
    row_count: int = 3,
) -> bytes:
    """
    Собирает CSV-файл в виде bytes.

    Parameters
    ----------
    rows : list[list[str]] | None
        Строки данных. Если None — генерируются row_count валидных строк.
    headers : list[str] | None
        Заголовки. Если None — берутся из HEADERS.
    encoding : str
        Кодировка (по умолчанию UTF-8-BOM).
    separator : str
        Разделитель полей.
    line_ending : str
        Разделитель строк.
    row_count : int
        Количество авто-генерируемых строк, если rows=None.
    """
    if headers is None:
        headers = HEADERS
    if rows is None:
        rows = [_valid_row() for _ in range(row_count)]

    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=separator, lineterminator=line_ending,
                        quoting=csv.QUOTE_MINIMAL, quotechar='"')
    writer.writerow(headers)
    for r in rows:
        writer.writerow(r)

    return buf.getvalue().encode(encoding)


def write_csv_file(content: bytes, suffix: str = ".csv") -> Path:
    """Записывает bytes во временный файл и возвращает путь."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.write(fd, content)
    os.close(fd)
    return Path(path)


# --- Быстрые фабрики для типичных сценариев ---

def valid_csv_file(row_count: int = 5) -> Path:
    return write_csv_file(build_csv(row_count=row_count))


def empty_csv_file() -> Path:
    return write_csv_file(b"")


def wrong_format_file() -> Path:
    """Файл .xlsx (фейковый, но с расширением)."""
    return write_csv_file(b"PK\x03\x04fake-xlsx-content", suffix=".xlsx")


def wrong_encoding_csv(encoding: str = "cp1251") -> Path:
    return write_csv_file(build_csv(encoding=encoding))


def headers_only_csv() -> Path:
    return write_csv_file(build_csv(rows=[]))


def csv_with_wrong_header_count(count: int = 20) -> Path:
    if count <= len(HEADERS):
        h = HEADERS[:count]
    else:
        h = list(HEADERS) + [f"Extra{i}" for i in range(count - len(HEADERS))]
    return write_csv_file(build_csv(headers=h))


def csv_with_missing_header(missing: str = "Номер") -> Path:
    h = [x if x != missing else "XXXXXX" for x in HEADERS]
    return write_csv_file(build_csv(headers=h))


def csv_with_duplicate_header(dup: str = "Регион") -> Path:
    h = list(HEADERS)
    idx = h.index(dup)
    h[idx + 1] = dup  # заменяем следующий заголовок дубликатом
    return write_csv_file(build_csv(headers=h))


def csv_with_modified_row(field_index: int, value: str, row_count: int = 3) -> Path:
    """CSV с одной модифицированной строкой (field_index 0-based)."""
    rows = [_valid_row() for _ in range(row_count)]
    rows[1][field_index] = value  # модифицируем вторую строку
    return write_csv_file(build_csv(rows=rows))


def csv_with_wrong_field_count(count: int = 20) -> Path:
    rows = [_valid_row() for _ in range(3)]
    if count < len(rows[1]):
        rows[1] = rows[1][:count]
    else:
        rows[1] = rows[1] + ["extra"] * (count - len(rows[1]))
    return write_csv_file(build_csv(rows=rows))


def csv_with_forbidden_char(char: str) -> Path:
    rows = [_valid_row() for _ in range(3)]
    rows[1][9] = f"Текст{char}со спецсимволом"
    return write_csv_file(build_csv(rows=rows))


def csv_with_duplicate_rows() -> Path:
    row = _valid_row()
    return write_csv_file(build_csv(rows=[row, row, _valid_row()]))


def csv_with_escaped_quotes() -> Path:
    """Поле содержит кавычки — проверка экранирования."""
    rows = [_valid_row() for _ in range(3)]
    rows[0][9] = '"интернет"'  # csv.writer сам экранирует
    return write_csv_file(build_csv(rows=rows))


def csv_with_semicolon_in_field() -> Path:
    """Поле содержит точку с запятой — проверка экранирования."""
    rows = [_valid_row() for _ in range(3)]
    rows[0][22] = "Правопорядок; Анонимные обращения"
    return write_csv_file(build_csv(rows=rows))


def oversized_csv_stub() -> Path:
    """Заглушка >2 Гб (создаём маленький файл, но тест проверяет логику)."""
    content = build_csv(row_count=1)
    return write_csv_file(content)
