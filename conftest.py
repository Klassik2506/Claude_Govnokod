"""
Pytest-фикстуры для приёмочного тестирования
валидации CSV-файла системы «Мастер обзоров».
"""
import pytest
from pathlib import Path
from fixtures.csv_factory import *  # noqa: F401,F403


@pytest.fixture
def valid_csv(tmp_path) -> Path:
    """Корректный CSV-файл."""
    return valid_csv_file(row_count=5)


@pytest.fixture
def cleanup():
    """Собирает пути для удаления после теста."""
    paths = []
    yield paths
    for p in paths:
        try:
            Path(p).unlink(missing_ok=True)
        except Exception:
            pass
