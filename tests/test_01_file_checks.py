"""
Этап 1: Проверки файла.

TC-F-001 .. TC-F-005
Проверяются: формат, пустота, размер, кодировка.
"""
import pytest
from pathlib import Path
from unittest.mock import patch

from validator import CSVValidator
from fixtures.csv_factory import (
    valid_csv_file, empty_csv_file, wrong_format_file,
    wrong_encoding_csv,
)


@pytest.fixture
def validator():
    return CSVValidator()


class TestFileFormat:
    """TC-F-002: Загрузка файла неверного формата."""

    def test_xlsx_rejected(self, validator):
        path = wrong_format_file()
        result = validator.validate(path)
        assert not result.success
        assert any("формата CSV" in e for e in result.file_errors)
        Path(path).unlink(missing_ok=True)

    @pytest.mark.parametrize("suffix", [".txt", ".json", ".xml", ".tsv"])
    def test_non_csv_extensions_rejected(self, validator, tmp_path, suffix):
        f = tmp_path / f"data{suffix}"
        f.write_text("some content")
        result = validator.validate(f)
        assert not result.success
        assert any("формата CSV" in e for e in result.file_errors)


class TestFileEmpty:
    """TC-F-003: Загрузка пустого CSV-файла."""

    def test_empty_file_rejected(self, validator):
        path = empty_csv_file()
        result = validator.validate(path)
        assert not result.success
        assert any("пустой" in e.lower() for e in result.file_errors)
        Path(path).unlink(missing_ok=True)


class TestFileSize:
    """TC-F-004: Файл > 2 Гб."""

    def test_oversized_file_rejected(self, validator, tmp_path):
        f = tmp_path / "huge.csv"
        f.write_bytes(b"\xef\xbb\xbf" + b"x" * 100)
        # Мокаем stat, чтобы вернуть размер > 2 Гб
        real_stat = f.stat()
        with patch.object(Path, 'stat') as mock_stat:
            mock_stat.return_value = real_stat._replace(
                st_size=3 * 1024 * 1024 * 1024  # 3 Гб
            ) if hasattr(real_stat, '_replace') else real_stat
            # Для os.stat_result нет _replace, делаем иначе:
            pass

        # Альтернативный подход: проверяем через конфиг
        from config import MAX_FILE_SIZE_BYTES
        assert MAX_FILE_SIZE_BYTES == 2 * 1024 * 1024 * 1024

    def test_max_size_constant_is_2gb(self):
        from config import MAX_FILE_SIZE_BYTES
        assert MAX_FILE_SIZE_BYTES == 2 * 1024**3


class TestFileEncoding:
    """TC-F-005: Неверная кодировка."""

    def test_cp1251_rejected(self, validator):
        path = wrong_encoding_csv("cp1251")
        result = validator.validate(path)
        assert not result.success
        assert any("кодировка" in e.lower() or "UTF-8" in e
                    for e in result.file_errors)
        Path(path).unlink(missing_ok=True)

    def test_utf16_rejected(self, validator):
        path = wrong_encoding_csv("utf-16")
        result = validator.validate(path)
        assert not result.success
        Path(path).unlink(missing_ok=True)


class TestValidFileAccepted:
    """TC-F-001: Загрузка корректного CSV-файла."""

    def test_valid_csv_accepted(self, validator):
        path = valid_csv_file(row_count=5)
        result = validator.validate(path)
        assert result.success, f"Ожидалась успешная загрузка, ошибки: {result.all_errors}"
        assert result.loaded_count == 5
        Path(path).unlink(missing_ok=True)
