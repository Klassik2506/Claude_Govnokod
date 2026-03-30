# Инструкция по локальному запуску проекта

## Требования

- **Python 3.10+** (рекомендуется 3.12)
- **Git**
- **pip**

---

## 1. Клонирование репозитория

```bash
git clone https://github.com/Klassik2506/Claude_Govnokod.git
cd Claude_Govnokod
```

---

## 2. Создание виртуального окружения

### Windows (cmd)
```cmd
python -m venv venv
venv\Scripts\activate
```

### Windows (PowerShell)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### macOS / Linux
```bash
python3 -m venv venv
source venv/bin/activate
```

После активации в начале строки терминала появится `(venv)`.

---

## 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

Это установит:
- `pytest` — фреймворк тестирования
- `pytest-html` — HTML-отчёты
- `pytest-xdist` — параллельный запуск
- `openpyxl` — работа с Excel

---

## 4. Запуск тестов

### Все тесты (основная команда)
```bash
pytest
```

### С подробным выводом
```bash
pytest -v
```

### Конкретный этап валидации
```bash
# Этап 1: Проверки файла (формат, размер, кодировка)
pytest tests/test_01_file_checks.py -v

# Этап 2: Проверки заголовков
pytest tests/test_02_header_checks.py -v

# Этап 3: Построчная валидация
pytest tests/test_03_row_validation.py -v
```

### Конкретный класс тестов
```bash
# Только проверки даты
pytest tests/test_03_row_validation.py::TestDateValidation -v

# Только проверки поля «Комп»
pytest tests/test_03_row_validation.py::TestFieldKomp -v

# Только спецсимволы
pytest tests/test_03_row_validation.py::TestForbiddenChars -v

# Только boolean-поля
pytest tests/test_03_row_validation.py::TestBooleanFields -v
```

### Один конкретный тест
```bash
pytest tests/test_03_row_validation.py::TestDateValidation::test_nonexistent_date_rejected -v
```

### По ключевому слову в имени теста
```bash
# Все тесты со словом "date" в названии
pytest -k "date" -v

# Все тесты со словом "rejected"
pytest -k "rejected" -v

# Комбинация: тесты с "valid" но без "invalid"
pytest -k "valid and not invalid" -v
```

---

## 5. Отчёты

### HTML-отчёт
```bash
pytest --html=report.html --self-contained-html
```
Откройте файл `report.html` в браузере.

### JUnit XML (для CI/CD)
```bash
pytest --junitxml=results.xml
```

### Вывод только упавших тестов
```bash
pytest --tb=short -q
```

---

## 6. Параллельный запуск (ускорение)

```bash
# Автоматически по числу ядер CPU
pytest -n auto

# Фиксированное число потоков
pytest -n 4
```

---

## 7. Полезные флаги pytest

| Флаг | Описание |
|------|----------|
| `-v` | Подробный вывод (имя каждого теста) |
| `-vv` | Ещё подробнее (diff при ошибках) |
| `-q` | Краткий вывод |
| `-x` | Остановиться на первом падении |
| `--lf` | Запустить только упавшие в прошлый раз |
| `--ff` | Сначала упавшие, потом остальные |
| `-s` | Показывать print() из тестов |
| `--co` | Только собрать тесты (не запускать) |
| `--durations=10` | Показать 10 самых медленных тестов |

---

## 8. Проверка окружения

```bash
# Версия Python
python --version

# Версия pytest
pytest --version

# Список установленных пакетов
pip list

# Собрать тесты без запуска (проверить что всё находится)
pytest --collect-only
```

---

## 9. Деактивация виртуального окружения

```bash
deactivate
```

---

## Ожидаемый результат запуска

```
$ pytest -v

============================= test session starts ==============================
collected 122 items

tests/test_01_file_checks.py::TestFileFormat::test_xlsx_rejected PASSED
tests/test_01_file_checks.py::TestFileFormat::test_non_csv_extensions_rejected[.txt] PASSED
tests/test_01_file_checks.py::TestFileFormat::test_non_csv_extensions_rejected[.json] PASSED
...
tests/test_03_row_validation.py::TestOptionalFieldsEmpty::test_all_optional_empty PASSED

============================= 122 passed in 0.60s =============================
```

Все 122 теста должны пройти со статусом **PASSED**.

---

## Устранение проблем

**`ModuleNotFoundError: No module named 'pytest'`**
→ Активируйте venv и установите зависимости:
```bash
source venv/bin/activate   # или venv\Scripts\activate на Windows
pip install -r requirements.txt
```

**`ModuleNotFoundError: No module named 'config'`**
→ Запускайте pytest из корня проекта (папка `Claude_Govnokod`):
```bash
cd Claude_Govnokod
pytest
```

**`SyntaxError` на type hints вида `str | None`**
→ Нужен Python 3.10+. Проверьте версию: `python --version`
