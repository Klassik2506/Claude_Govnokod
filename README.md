# Автоматизация приёмочного тестирования валидации CSV

Проект автоматизированных тестов для технической валидации CSV-файлов
системы **«Мастер обзоров»** (импорт данных по обращениям из АС ОГ).

## Архитектура

```
csv_validator_tests/
├── config.py                    # Конфигурация: поля, ограничения, спецсимволы
├── validator.py                 # Валидатор CSV (объект тестирования)
├── conftest.py                  # Pytest-фикстуры
├── pytest.ini                   # Настройки pytest
├── requirements.txt             # Зависимости
│
├── fixtures/
│   ├── __init__.py
│   └── csv_factory.py           # Фабрика тестовых CSV-файлов
│
├── tests/
│   ├── __init__.py
│   ├── test_01_file_checks.py   # Этап 1: Проверки файла (формат, размер, кодировка)
│   ├── test_02_header_checks.py # Этап 2: Проверки заголовков
│   └── test_03_row_validation.py# Этап 3: Построчная валидация
│
└── utils/
    └── __init__.py
```

## Покрытие проверок (122 теста)

### Этап 1 — Проверки файла (`test_01_file_checks.py`)
| Тест-кейс | Описание |
|-----------|----------|
| TC-F-001  | Загрузка корректного CSV-файла |
| TC-F-002  | Отклонение файлов форматов .xlsx, .txt, .json, .xml, .tsv |
| TC-F-003  | Отклонение пустого файла (0 байт) |
| TC-F-004  | Отклонение файла > 2 Гб |
| TC-F-005  | Отклонение файлов в кодировках cp1251, utf-16 |

### Этап 2 — Проверки заголовков (`test_02_header_checks.py`)
| Тест-кейс | Описание |
|-----------|----------|
| TC-H-001  | Неверное количество заголовков (1, 10, 20, 24, 26, 30) |
| TC-H-002  | Отсутствие обязательного заголовка (7 параметризованных) |
| TC-H-003  | Дублирующиеся заголовки |

### Этап 3 — Построчная валидация (`test_03_row_validation.py`)
| Тест-кейс | Описание |
|-----------|----------|
| TC-R-001  | Файл без строк данных (только заголовки) |
| TC-R-002  | Неверное количество полей в строке (1, 10, 20, 24, 26) |
| TC-R-003  | Пустые обязательные поля (14 параметризованных) |
| TC-R-004  | Несбалансированные кавычки |
| TC-R-005  | Превышение максимальной длины полей (9 параметризованных) |
| TC-R-006  | Неверный формат даты (YYYY-MM-DD вместо DD.MM.YYYY) |
| TC-R-007  | Несуществующая дата (30.02.2025) |
| TC-R-008  | Некорректные компоненты даты (32.13.2025) |
| TC-R-009  | Дата вне месяца обзора |
| TC-R-010  | Допустимые/недопустимые значения поля «Комп» (6+5) |
| TC-R-011  | Допустимые/недопустимые значения поля «ПВ» (4+4) |
| TC-R-012–014 | Boolean-поля ОЖ, Контр, Повторность (3×3 допустимых + 3×5 недопустимых) |
| TC-R-015–019 | Спецсимволы: Null, Tab, SUB, U+FFFD, U+2026 |
| TC-R-020  | Дубликаты строк (предупреждение) |
| TC-R-021  | Экранирование кавычек |
| TC-R-022  | Экранирование точки с запятой |
| TC-R-023–025 | Маппинг boolean (1→true, 0→false, ''→false) |
| TC-R-026–027 | Формат кода вопроса/подвопроса |
| TC-R-028  | Високосный год: 29.02 |
| TC-R-029  | Все необязательные поля пустые |

## Быстрый старт

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск всех тестов
pytest

# Запуск с подробным выводом
pytest -v

# Запуск конкретного этапа
pytest tests/test_01_file_checks.py
pytest tests/test_02_header_checks.py
pytest tests/test_03_row_validation.py

# Запуск конкретного класса тестов
pytest tests/test_03_row_validation.py::TestDateValidation

# Запуск с HTML-отчётом (нужен pytest-html)
pytest --html=report.html --self-contained-html

# Параллельный запуск (нужен pytest-xdist)
pytest -n auto
```

## Ключевые паттерны

### 1. Фабрика тестовых данных (`fixtures/csv_factory.py`)
Генерирует CSV-файлы с нужными характеристиками:
- `valid_csv_file(row_count)` — корректный файл
- `csv_with_modified_row(field_idx, value)` — одно изменённое поле
- `csv_with_forbidden_char(char)` — спецсимвол в данных
- и другие фабричные методы

### 2. Параметризация (`@pytest.mark.parametrize`)
Один тест покрывает множество вариантов:
```python
@pytest.mark.parametrize("value", ["ФГО", "ФОИВ", "РОИВ", "ОСВ", "ОЗВ", "Другие"])
def test_valid_values_accepted(self, validator, value):
    ...
```

### 3. Конфигурация как единый источник правды (`config.py`)
Все ограничения (имена полей, макс. длины, допустимые значения)
берутся из `config.py`, который соответствует документации.

## Расширение проекта

### Интеграция с API системы
Если «Мастер обзоров» предоставляет REST API для загрузки:

```python
import requests

class TestAPIUpload:
    BASE_URL = "https://master-obzorov.example.com/api/v1"

    def test_upload_valid_csv(self):
        path = valid_csv_file()
        with open(path, "rb") as f:
            resp = requests.post(f"{self.BASE_URL}/csv/upload",
                                 files={"file": f})
        assert resp.status_code == 200
        assert resp.json()["success"] is True
```

### Интеграция с Selenium/Playwright
Для тестирования через UI:

```python
from playwright.sync_api import sync_playwright

def test_upload_via_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("https://master-obzorov.example.com/upload")
        page.set_input_files("#csv-upload", str(valid_csv_file()))
        page.click("#submit-btn")
        assert page.locator(".success-message").is_visible()
```

### CI/CD (GitHub Actions)
```yaml
name: CSV Validation Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt
      - run: pytest --junitxml=results.xml
      - uses: actions/upload-artifact@v4
        with:
          name: test-results
          path: results.xml
```

## Альтернативные инструменты

| Инструмент | Применение |
|------------|-----------|
| **pytest** | Основной фреймворк (используется в проекте) |
| **pytest-html** | HTML-отчёты |
| **pytest-xdist** | Параллельный запуск тестов |
| **Allure** | Расширенные отчёты с шагами и вложениями |
| **Great Expectations** | Декларативная валидация данных (Data Quality) |
| **Pandera** | Схема-валидация pandas DataFrame |
| **Cerberus / Pydantic** | Валидация структуры данных |
| **Playwright / Selenium** | E2E тестирование через UI |
| **Locust** | Нагрузочное тестирование загрузки файлов |
