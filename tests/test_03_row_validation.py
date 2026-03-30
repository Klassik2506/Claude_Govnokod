"""
Этап 3: Построчная валидация.

TC-R-001 .. TC-R-029
Проверяются: количество полей, обязательность, длины, типы,
допустимые значения, даты, спецсимволы, дубликаты, экранирование,
маппинг boolean.
"""
import pytest
from pathlib import Path

from validator import CSVValidator
from config import HEADERS, BOOLEAN_MAPPING
from fixtures.csv_factory import (
    headers_only_csv,
    csv_with_wrong_field_count,
    csv_with_modified_row,
    csv_with_forbidden_char,
    csv_with_duplicate_rows,
    csv_with_escaped_quotes,
    csv_with_semicolon_in_field,
    valid_csv_file,
)


@pytest.fixture
def validator():
    return CSVValidator()


@pytest.fixture
def validator_sept2025():
    """Валидатор для обзора за сентябрь 2025."""
    return CSVValidator(review_month=(2025, 9))


# --- TC-R-001: Только заголовки ---

class TestNoDataRows:
    def test_headers_only_rejected(self, validator):
        path = headers_only_csv()
        result = validator.validate(path)
        assert not result.success
        assert any("только заголовки" in e.lower() or "нет данных" in e.lower()
                    for e in result.all_errors)
        Path(path).unlink(missing_ok=True)


# --- TC-R-002: Неверное количество полей ---

class TestFieldCount:
    @pytest.mark.parametrize("count", [1, 10, 20, 24, 26])
    def test_wrong_field_count(self, validator, count):
        path = csv_with_wrong_field_count(count)
        result = validator.validate(path)
        assert not result.success
        assert any("количество полей" in e.message.lower()
                    for e in result.row_errors)
        Path(path).unlink(missing_ok=True)


# --- TC-R-003: Обязательные поля ---

class TestRequiredFields:
    """Пустое обязательное поле → ошибка."""

    @pytest.mark.parametrize("field_name,field_idx", [
        ("ГруппаГ", 0),
        ("Округ", 1),
        ("Регион", 2),
        ("Номер", 6),
        ("Дата", 7),
        ("Код", 8),
        ("Наименование", 9),
        ("Тип", 10),
        ("Комп", 11),
        ("ПВ", 12),
        ("Орган", 13),
        ("Вид письма", 18),
        ("Цель напр.", 21),
        ("Приемная", 24),
    ])
    def test_empty_required_field_rejected(self, validator, field_name, field_idx):
        path = csv_with_modified_row(field_idx, "")
        result = validator.validate(path)
        assert not result.success
        assert any(field_name in e.message for e in result.row_errors)
        Path(path).unlink(missing_ok=True)


# --- TC-R-004: Несбалансированные кавычки ---

class TestUnbalancedQuotes:
    def test_odd_quotes_warning(self, validator):
        # Создаём вручную: нечётное число кавычек внутри значения
        # csv.writer сам экранирует, поэтому тестируем через валидатор напрямую
        from validator import ValidationResult
        result = ValidationResult()
        row = ["val"] * 25
        row[9] = 'Тест"нечётная'  # 1 кавычка — нечётное
        validator._validate_row(2, row, HEADERS, result)
        assert any("кавычки" in e.message.lower() for e in result.row_errors)


# --- TC-R-005: Превышение максимальной длины ---

class TestFieldLength:
    @pytest.mark.parametrize("field_name,field_idx,max_len", [
        ("ГруппаГ", 0, 10),
        ("Округ", 1, 10),
        ("Регион", 2, 50),
        ("Номер", 6, 30),
        ("Код", 8, 24),
        ("Комп", 11, 10),
        ("ПВ", 12, 10),
        ("Вид письма", 18, 15),
        ("Приемная", 24, 50),
    ])
    def test_exceeding_max_length(self, validator, field_name, field_idx, max_len):
        long_value = "А" * (max_len + 5)
        # Нужно дать допустимое значение, но слишком длинное
        # Для полей с allowed мы получим ещё и ошибку "недопустимое значение",
        # но нас интересует ошибка длины
        from validator import ValidationResult
        result = ValidationResult()
        from fixtures.csv_factory import _valid_row
        row = _valid_row()
        row[field_idx] = long_value
        validator._validate_row(2, row, HEADERS, result)
        assert any("длину" in e.message.lower() or "длин" in e.message.lower()
                    for e in result.row_errors)


# --- TC-R-006..009: Валидация даты ---

class TestDateValidation:
    """Проверки поля «Дата» (index=7)."""

    def test_wrong_format_rejected(self, validator):
        """TC-R-006: Неверный формат (YYYY-MM-DD вместо DD.MM.YYYY)."""
        path = csv_with_modified_row(7, "2025-09-01")
        result = validator.validate(path)
        assert not result.success
        assert any("формат даты" in e.message.lower() for e in result.row_errors)
        Path(path).unlink(missing_ok=True)

    def test_nonexistent_date_rejected(self, validator):
        """TC-R-007: 30.02.2025 — не существует."""
        path = csv_with_modified_row(7, "30.02.2025")
        result = validator.validate(path)
        assert not result.success
        assert any("не существует" in e.message.lower() for e in result.row_errors)
        Path(path).unlink(missing_ok=True)

    def test_invalid_day_month_rejected(self, validator):
        """TC-R-008: День > 31, месяц > 12."""
        path = csv_with_modified_row(7, "32.13.2025")
        result = validator.validate(path)
        assert not result.success
        assert any("день" in e.message.lower() or "месяц" in e.message.lower()
                    for e in result.row_errors)
        Path(path).unlink(missing_ok=True)

    def test_date_outside_review_month(self, validator_sept2025):
        """TC-R-009: Дата не в месяце обзора."""
        path = csv_with_modified_row(7, "15.08.2025")
        result = validator_sept2025.validate(path)
        assert not result.success
        assert any("месяц" in e.message.lower() for e in result.row_errors)
        Path(path).unlink(missing_ok=True)

    @pytest.mark.parametrize("date_str", [
        "01.09.2025", "15.09.2025", "30.09.2025"
    ])
    def test_valid_dates_accepted(self, validator_sept2025, date_str):
        """Корректные даты в месяце обзора проходят."""
        path = csv_with_modified_row(7, date_str)
        result = validator_sept2025.validate(path)
        date_errors = [e for e in result.row_errors
                       if e.field_name == "Дата"]
        assert not date_errors, f"Ожидалось без ошибок даты: {date_errors}"
        Path(path).unlink(missing_ok=True)

    def test_leap_year_feb29_valid(self, validator):
        """29.02.2024 — високосный год, дата существует."""
        from validator import ValidationResult
        result = ValidationResult()
        from fixtures.csv_factory import _valid_row
        row = _valid_row()
        row[7] = "29.02.2024"
        validator._validate_row(2, row, HEADERS, result)
        date_errors = [e for e in result.row_errors if e.field_name == "Дата"]
        assert not date_errors

    def test_non_leap_year_feb29_invalid(self, validator):
        """29.02.2023 — не високосный, дата не существует."""
        from validator import ValidationResult
        result = ValidationResult()
        from fixtures.csv_factory import _valid_row
        row = _valid_row()
        row[7] = "29.02.2023"
        validator._validate_row(2, row, HEADERS, result)
        assert any("не существует" in e.message for e in result.row_errors)


# --- TC-R-010: Поле «Комп» ---

class TestFieldKomp:
    VALID = ["ФГО", "ФОИВ", "РОИВ", "ОСВ", "ОЗВ", "Другие"]

    @pytest.mark.parametrize("value", VALID)
    def test_valid_values_accepted(self, validator, value):
        path = csv_with_modified_row(11, value)
        result = validator.validate(path)
        komp_errors = [e for e in result.row_errors if e.field_name == "Комп"]
        assert not komp_errors
        Path(path).unlink(missing_ok=True)

    @pytest.mark.parametrize("value", ["НЕИЗВЕСТНО", "ФОИ", "фоив", "123", " "])
    def test_invalid_values_rejected(self, validator, value):
        path = csv_with_modified_row(11, value)
        result = validator.validate(path)
        assert any("Комп" in e.message for e in result.row_errors)
        Path(path).unlink(missing_ok=True)


# --- TC-R-011: Поле «ПВ» ---

class TestFieldPV:
    VALID = ["РФ", "СУБ", "МСТ", "Надзор"]

    @pytest.mark.parametrize("value", VALID)
    def test_valid_values_accepted(self, validator, value):
        path = csv_with_modified_row(12, value)
        result = validator.validate(path)
        pv_errors = [e for e in result.row_errors if e.field_name == "ПВ"]
        assert not pv_errors
        Path(path).unlink(missing_ok=True)

    @pytest.mark.parametrize("value", ["Федеральный", "РФФ", "мст", "Другие"])
    def test_invalid_values_rejected(self, validator, value):
        path = csv_with_modified_row(12, value)
        result = validator.validate(path)
        assert any("ПВ" in e.message for e in result.row_errors)
        Path(path).unlink(missing_ok=True)


# --- TC-R-012..014: Целочисленные/boolean поля ---

class TestBooleanFields:
    """ОЖ (idx=15), Контр (idx=16), Повторность (idx=23)."""

    @pytest.mark.parametrize("field_name,idx", [
        ("ОЖ", 15), ("Контр", 16), ("Повторность", 23)
    ])
    @pytest.mark.parametrize("valid_val", ["0", "1", ""])
    def test_valid_values(self, validator, field_name, idx, valid_val):
        path = csv_with_modified_row(idx, valid_val)
        result = validator.validate(path)
        field_errors = [e for e in result.row_errors
                        if e.field_name == field_name]
        assert not field_errors, f"{field_name}={valid_val!r} должно быть допустимым"
        Path(path).unlink(missing_ok=True)

    @pytest.mark.parametrize("field_name,idx", [
        ("ОЖ", 15), ("Контр", 16), ("Повторность", 23)
    ])
    @pytest.mark.parametrize("invalid_val", ["2", "Да", "true", "-1", "10"])
    def test_invalid_values(self, validator, field_name, idx, invalid_val):
        path = csv_with_modified_row(idx, invalid_val)
        result = validator.validate(path)
        assert any(field_name in e.message for e in result.row_errors), \
            f"{field_name}={invalid_val!r} должно быть отклонено"
        Path(path).unlink(missing_ok=True)


# --- TC-R-015..019: Спецсимволы ---

class TestForbiddenChars:
    @pytest.mark.parametrize("char,expected_fragment", [
        ("\x00", "нулевой символ"),
        ("\t", "табуляции"),
        ("\x1a", "конца файла"),
        ("\ufffd", "некорректные символы"),
        ("\u2026", "многоточия"),
    ])
    def test_forbidden_char_rejected(self, validator, char, expected_fragment):
        path = csv_with_forbidden_char(char)
        result = validator.validate(path)
        assert not result.success
        assert any(expected_fragment in e for e in result.file_errors), \
            f"Ожидалась ошибка с '{expected_fragment}', получено: {result.file_errors}"
        Path(path).unlink(missing_ok=True)


# --- TC-R-020: Дубликаты строк ---

class TestDuplicateRows:
    def test_duplicate_rows_warning(self, validator):
        path = csv_with_duplicate_rows()
        result = validator.validate(path)
        assert any("дубликат" in w.lower() for w in result.warnings)
        Path(path).unlink(missing_ok=True)


# --- TC-R-021..022: Экранирование ---

class TestEscaping:
    def test_quotes_in_field_correctly_parsed(self, validator):
        """TC-R-021: Кавычки внутри поля экранируются удвоением."""
        path = csv_with_escaped_quotes()
        result = validator.validate(path)
        # Файл должен загрузиться (поле корректно экранировано csv.writer)
        # Могут быть ошибки длины, но кавычки не должны ломать парсинг
        field_count_errors = [e for e in result.row_errors
                              if "количество полей" in e.message.lower()]
        assert not field_count_errors, "Экранированные кавычки не должны ломать парсинг"
        Path(path).unlink(missing_ok=True)

    def test_semicolon_in_field_correctly_parsed(self, validator):
        """TC-R-022: Точка с запятой внутри поля."""
        path = csv_with_semicolon_in_field()
        result = validator.validate(path)
        field_count_errors = [e for e in result.row_errors
                              if "количество полей" in e.message.lower()]
        assert not field_count_errors, "Точка с запятой в поле не должна ломать парсинг"
        Path(path).unlink(missing_ok=True)


# --- TC-R-023..025: Маппинг boolean ---

class TestBooleanMapping:
    """Проверка маппинга: 1→true, 0→false, ''→false."""

    def test_mapping_values(self):
        assert BOOLEAN_MAPPING["1"] is True
        assert BOOLEAN_MAPPING["0"] is False
        assert BOOLEAN_MAPPING[""] is False

    @pytest.mark.parametrize("csv_val,expected", [
        ("1", True), ("0", False), ("", False)
    ])
    def test_boolean_conversion(self, csv_val, expected):
        assert BOOLEAN_MAPPING[csv_val] is expected


# --- TC-R-026..027: Формат кода вопроса ---

class TestQuestionCode:
    @pytest.mark.parametrize("code", [
        "0005.0005.0056.1153",         # код вопроса
        "0004.0015.0158.0965.0064",    # код подвопроса
    ])
    def test_valid_codes_accepted(self, validator, code):
        path = csv_with_modified_row(8, code)
        result = validator.validate(path)
        code_errors = [e for e in result.row_errors if e.field_name == "Код"]
        assert not code_errors
        Path(path).unlink(missing_ok=True)


# --- TC-R-029: Необязательные поля пустые ---

class TestOptionalFieldsEmpty:
    """Все необязательные поля пустые — загрузка успешна."""

    def test_all_optional_empty(self, validator):
        from fixtures.csv_factory import _valid_row, build_csv, write_csv_file
        row = _valid_row()
        # Индексы необязательных полей: Район(3), Город(4), Кол-во(5),
        # Группа(14), Сотрудник(17), ОрганССТУ(19), ГруппаССТУ(20), Событие(22)
        optional_indices = [3, 4, 5, 14, 17, 19, 20, 22]
        for idx in optional_indices:
            row[idx] = ""
        path = write_csv_file(build_csv(rows=[row, row]))
        result = validator.validate(path)
        # Не должно быть ошибок по необязательным полям
        optional_errors = [e for e in result.row_errors
                           if e.field_name in ["Район", "Город", "Кол-во",
                                                "Группа", "Сотрудник",
                                                "ОрганССТУ", "ГруппаССТУ",
                                                "Событие"]]
        assert not optional_errors
        Path(path).unlink(missing_ok=True)
