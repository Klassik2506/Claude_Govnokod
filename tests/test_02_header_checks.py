"""
Этап 2: Проверки заголовков.

TC-H-001 .. TC-H-003
Проверяются: количество, наличие всех, дубликаты.
"""
import pytest
from pathlib import Path

from validator import CSVValidator
from fixtures.csv_factory import (
    csv_with_wrong_header_count,
    csv_with_missing_header,
    csv_with_duplicate_header,
)


@pytest.fixture
def validator():
    return CSVValidator()


class TestHeaderCount:
    """TC-H-001: Неверное количество заголовков."""

    @pytest.mark.parametrize("count", [1, 10, 20, 24, 26, 30])
    def test_wrong_count_rejected(self, validator, count):
        path = csv_with_wrong_header_count(count)
        result = validator.validate(path)
        assert not result.success
        assert any("количество заголовков" in e.lower()
                    for e in result.header_errors)
        Path(path).unlink(missing_ok=True)


class TestHeaderPresence:
    """TC-H-002: Отсутствие обязательного заголовка."""

    @pytest.mark.parametrize("missing", [
        "ГруппаГ", "Номер", "Дата", "Код", "Комп", "ПВ", "Приемная"
    ])
    def test_missing_header_rejected(self, validator, missing):
        path = csv_with_missing_header(missing)
        result = validator.validate(path)
        assert not result.success
        assert any(missing in e for e in result.header_errors)
        Path(path).unlink(missing_ok=True)


class TestHeaderDuplicates:
    """TC-H-003: Дублирующиеся заголовки."""

    def test_duplicate_header_rejected(self, validator):
        path = csv_with_duplicate_header("Регион")
        result = validator.validate(path)
        assert not result.success
        assert any("дублируемые" in e.lower() and "Регион" in e
                    for e in result.header_errors)
        Path(path).unlink(missing_ok=True)
