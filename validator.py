"""
Валидатор CSV-файлов для системы «Мастер обзоров».

Реализует три этапа технической валидации:
1. Проверки файла (формат, размер, кодировка, пустота)
2. Проверки заголовков (количество, наличие, дубликаты)
3. Построчная валидация (типы, длины, допустимые значения, спецсимволы)

Результат валидации — объект ValidationResult.
"""
import csv
import io
import re
from calendar import monthrange
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from config import (
    BOOLEAN_FIELDS, BOOLEAN_MAPPING, FIELD_SEPARATOR, FIELDS, FILE_ENCODING,
    FORBIDDEN_CHARS, HEADER_COUNT, HEADERS, MAX_FILE_SIZE_BYTES,
    REQUIRED_FIELDS,
)


@dataclass
class RowError:
    """Ошибка в конкретной строке."""
    row_number: int
    field_name: str | None
    message: str


@dataclass
class ValidationResult:
    """Результат валидации CSV-файла."""
    success: bool = True
    file_errors: list[str] = field(default_factory=list)
    header_errors: list[str] = field(default_factory=list)
    row_errors: list[RowError] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    loaded_count: int = 0

    @property
    def all_errors(self) -> list[str]:
        msgs = self.file_errors + self.header_errors
        msgs += [f"Строка {e.row_number}: {e.message}" for e in self.row_errors]
        return msgs

    def add_file_error(self, msg: str):
        self.success = False
        self.file_errors.append(msg)

    def add_header_error(self, msg: str):
        self.success = False
        self.header_errors.append(msg)

    def add_row_error(self, row: int, field_name: str | None, msg: str):
        self.success = False
        self.row_errors.append(RowError(row, field_name, msg))

    def add_warning(self, msg: str):
        self.warnings.append(msg)


class CSVValidator:
    """
    Валидатор CSV-файлов.

    Параметры:
        review_month: (year, month) — период обзора для проверки дат.
    """

    def __init__(self, review_month: tuple[int, int] | None = None):
        self.review_month = review_month
        self._fields_by_header = {f["header"]: f for f in FIELDS}

    def validate(self, file_path: str | Path) -> ValidationResult:
        path = Path(file_path)
        result = ValidationResult()

        # === ЭТАП 1: ПРОВЕРКИ ФАЙЛА ===
        if not self._check_file(path, result):
            return result

        raw = path.read_bytes()

        # Проверка кодировки (BOM)
        if not raw.startswith(b'\xef\xbb\xbf'):
            result.add_file_error(
                "В файле указана неверная кодировка. Ожидается: UTF-8"
            )
            return result

        text = raw.decode("utf-8-sig")
        lines = text.split("\r\n")
        # убираем пустую финальную строку
        if lines and lines[-1] == "":
            lines = lines[:-1]

        if not lines:
            result.add_file_error("Файл пустой")
            return result

        # === ЭТАП 2: ПРОВЕРКИ ЗАГОЛОВКОВ ===
        reader = csv.reader(io.StringIO(text), delimiter=FIELD_SEPARATOR,
                            quotechar='"')
        all_rows = list(reader)
        # Убираем пустые trailing строки
        while all_rows and all_rows[-1] == ['']:
            all_rows.pop()

        if not all_rows:
            result.add_file_error("Файл пустой")
            return result

        headers = all_rows[0]
        if not self._check_headers(headers, result):
            return result

        # === ЭТАП 3: ПОСТРОЧНАЯ ВАЛИДАЦИЯ ===
        data_rows = all_rows[1:]
        if not data_rows:
            result.add_file_error(
                "Файл содержит только заголовки, нет данных"
            )
            return result

        # Проверка спецсимволов во всём тексте (кроме заголовков)
        data_text = "\r\n".join(FIELD_SEPARATOR.join(r) for r in data_rows)
        self._check_forbidden_chars(data_text, result)
        if not result.success:
            return result

        # Построчная валидация
        seen_rows: set[tuple] = set()
        dup_count = 0
        for i, row in enumerate(data_rows, start=2):  # строка 2+ (1 = заголовки)
            self._validate_row(i, row, headers, result)
            row_tuple = tuple(row)
            if row_tuple in seen_rows:
                dup_count += 1
            else:
                seen_rows.add(row_tuple)

        if dup_count > 0:
            result.add_warning(
                f"Найдено полных дубликатов строк: {dup_count}"
            )

        if result.success:
            result.loaded_count = len(data_rows)

        return result

    # --- Этап 1 ---

    def _check_file(self, path: Path, result: ValidationResult) -> bool:
        if not path.exists():
            result.add_file_error("Файл не найден")
            return False

        if path.suffix.lower() != ".csv":
            result.add_file_error(
                "Для загрузки разрешены только файлы формата CSV"
            )
            return False

        size = path.stat().st_size
        if size == 0:
            result.add_file_error("Файл пустой")
            return False

        if size > MAX_FILE_SIZE_BYTES:
            result.add_file_error(
                "Файл превышает максимальный допустимый размер 2 Гб"
            )
            return False

        return True

    # --- Этап 2 ---

    def _check_headers(self, headers: list[str], result: ValidationResult) -> bool:
        ok = True

        if len(headers) != HEADER_COUNT:
            result.add_header_error(
                "Файл содержит неверное количество заголовков"
            )
            ok = False

        for expected in HEADERS:
            if expected not in headers:
                result.add_header_error(
                    f"В файле отсутствует заголовок {expected}"
                )
                ok = False

        # Дубликаты
        seen = set()
        dups = set()
        for h in headers:
            if h in seen:
                dups.add(h)
            seen.add(h)
        if dups:
            result.add_header_error(
                f"Файл содержит дублируемые заголовки: {', '.join(sorted(dups))}"
            )
            ok = False

        return ok

    # --- Этап 3 ---

    def _check_forbidden_chars(self, text: str, result: ValidationResult):
        for char, desc in FORBIDDEN_CHARS.items():
            if char in text:
                if char == "\x00":
                    result.add_file_error(
                        "Файл содержит недопустимый нулевой символ (Null) "
                        "и может быть повреждён или создан некорректно. "
                        "Пересоздайте файл и проверьте корректность экспорта"
                    )
                elif char == "\t":
                    result.add_file_error(
                        "Файл содержит символы табуляции (отступы)"
                    )
                elif char == "\x1a":
                    result.add_file_error(
                        "Файл содержит служебный символ конца файла (Ctrl+Z) "
                        "и может быть повреждён или создан некорректно. "
                        "Пересоздайте файл и проверьте корректность экспорта"
                    )
                elif char == "\ufffd":
                    result.add_file_error(
                        "Файл содержит некорректные символы (�). "
                        "Сохраните файл заново в кодировке UTF-8."
                    )
                elif char == "\u2026":
                    result.add_file_error(
                        "Файл содержит символы многоточия"
                    )

    def _validate_row(self, row_num: int, row: list[str],
                      headers: list[str], result: ValidationResult):
        # Количество полей
        if len(row) != HEADER_COUNT:
            result.add_row_error(row_num, None,
                                 "Строка содержит неверное количество полей")
            return  # дальше нет смысла валидировать

        for col_idx, value in enumerate(row):
            if col_idx >= len(headers):
                break
            header = headers[col_idx]
            field_def = self._fields_by_header.get(header)
            if not field_def:
                continue

            # Обязательность
            if field_def["required"] and value.strip() == "":
                # Для boolean полей пустое значение допустимо
                if field_def["type"] != "boolean":
                    result.add_row_error(
                        row_num, header,
                        f"Обязательное поле {header} не заполнено"
                    )
                    continue

            if value.strip() == "":
                continue

            # Длина
            max_len = field_def.get("max_len")
            if max_len and len(value) > max_len:
                result.add_row_error(
                    row_num, header,
                    f"Значение в поле {header} превышает максимальную "
                    f"допустимую длину: {max_len} символов"
                )

            # Допустимые значения
            allowed = field_def.get("allowed")
            if allowed and value not in allowed:
                result.add_row_error(
                    row_num, header,
                    f"Недопустимое значение в поле «{header}». "
                    f"Может быть только одно из следующих значений: "
                    f"{', '.join(a if a else 'пустое значение' for a in allowed)}"
                )

            # Дата
            if field_def["type"] == "date":
                self._validate_date(row_num, header, value, result)

            # Кавычки (баланс)
            if '"' in value:
                if value.count('"') % 2 != 0:
                    result.add_row_error(
                        row_num, header,
                        f"Возможно, несбалансированные кавычки в поле {header}"
                    )

    def _validate_date(self, row_num: int, header: str, value: str,
                       result: ValidationResult):
        pattern = re.compile(r'^(\d{2})\.(\d{2})\.(\d{4})$')
        m = pattern.match(value)
        if not m:
            result.add_row_error(
                row_num, header,
                "Недопустимое значение в поле «Дата». Неверный формат даты"
            )
            return

        day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))

        if month < 1 or month > 12 or day < 1 or day > 31:
            result.add_row_error(
                row_num, header,
                "Недопустимое значение в поле «Дата». "
                "Дата содержит некорректные день или месяц"
            )
            return

        if year < 2000:
            result.add_row_error(
                row_num, header,
                "Недопустимое значение в поле «Дата». Неверный формат даты"
            )
            return

        # Реальность даты
        try:
            datetime(year, month, day)
        except ValueError:
            result.add_row_error(
                row_num, header,
                "Недопустимое значение в поле «Дата». "
                "Указанная дата не существует"
            )
            return

        # Проверка на вхождение в месяц обзора
        if self.review_month:
            ry, rm = self.review_month
            if year != ry or month != rm:
                result.add_row_error(
                    row_num, header,
                    "Недопустимое значение в поле «Дата». "
                    "Дата не входит в календарный месяц, выбранный для обзора"
                )
