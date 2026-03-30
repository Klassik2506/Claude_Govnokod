"""
Конфигурация полей CSV-файла согласно документации
«2. Формат и техническая валидация файла CSV»

Система: «Мастер обзоров»
Назначение: Ежемесячный импорт данных по вопросам обращений из АС ОГ
"""

# Общие параметры файла
FILE_FORMAT = "csv"
FILE_ENCODING = "utf-8-sig"  # UTF-8-BOM
LINE_SEPARATOR = "\r\n"      # CRLF
FIELD_SEPARATOR = ";"
MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024 * 1024  # 2 Гб
HEADER_COUNT = 25

# Определения полей CSV (порядок, имя заголовка, параметр системы, тип, макс.длина, обязательность)
FIELDS = [
    {"index": 1,  "header": "ГруппаГ",     "param": "authorCitizenshipGroup",     "type": "string",  "max_len": 10,   "required": True,  "allowed": ["РФ", "ДГ"]},
    {"index": 2,  "header": "Округ",        "param": "authorFederalDistrict",      "type": "string",  "max_len": 10,   "required": True,  "allowed": ["ДГ", "ДФО", "Новые", "ПФО", "СЗФО", "СКФО", "СФО", "УФО", "ЦФО", "ЮФО"]},
    {"index": 3,  "header": "Регион",       "param": "authorSubject",              "type": "string",  "max_len": 50,   "required": True},
    {"index": 4,  "header": "Район",        "param": "authorMunicipalUnit",        "type": "string",  "max_len": 512,  "required": False},
    {"index": 5,  "header": "Город",        "param": "authorSettlement",           "type": "string",  "max_len": 512,  "required": False},
    {"index": 6,  "header": "Кол-во",       "param": "questionQuantity",           "type": "integer", "max_len": 1,    "required": False, "allowed": ["", "1"]},
    {"index": 7,  "header": "Номер",        "param": "requestNumber",              "type": "string",  "max_len": 30,   "required": True},
    {"index": 8,  "header": "Дата",         "param": "createDate",                 "type": "date",    "max_len": 10,   "required": True,  "format": "DD.MM.YYYY"},
    {"index": 9,  "header": "Код",          "param": "questionCode",               "type": "string",  "max_len": 24,   "required": True},
    {"index": 10, "header": "Наименование", "param": "questionName",               "type": "string",  "max_len": 512,  "required": True},
    {"index": 11, "header": "Тип",          "param": "questionType",               "type": "string",  "max_len": 128,  "required": True},
    {"index": 12, "header": "Комп",         "param": "competentAuthorityType",     "type": "string",  "max_len": 10,   "required": True,  "allowed": ["ФГО", "ФОИВ", "РОИВ", "ОСВ", "ОЗВ", "Другие"]},
    {"index": 13, "header": "ПВ",           "param": "jurisdictionLevel",          "type": "string",  "max_len": 10,   "required": True,  "allowed": ["РФ", "СУБ", "МСТ", "Надзор"]},
    {"index": 14, "header": "Орган",        "param": "departmentNameASOG",         "type": "string",  "max_len": 512,  "required": True},
    {"index": 15, "header": "Группа",       "param": "departmentNameGroup",        "type": "string",  "max_len": 512,  "required": False},
    {"index": 16, "header": "ОЖ",           "param": "isAwaitingDocuments",        "type": "boolean", "max_len": 1,    "required": True,  "allowed": ["0", "1", ""]},
    {"index": 17, "header": "Контр",        "param": "isUnderControl",             "type": "boolean", "max_len": 1,    "required": True,  "allowed": ["0", "1", ""]},
    {"index": 18, "header": "Сотрудник",    "param": "employee",                   "type": "string",  "max_len": 70,   "required": False},
    {"index": 19, "header": "Вид письма",   "param": "sourceType",                 "type": "string",  "max_len": 15,   "required": True,  "allowed": ["ЗУ", "интернет", "ЛП", "письмо", "ПП", "факс", "телеграмма", "Устно"]},
    {"index": 20, "header": "ОрганССТУ",    "param": "departmentNameSSTU",         "type": "string",  "max_len": 512,  "required": False},
    {"index": 21, "header": "ГруппаССТУ",   "param": "departmentNameGroupSSTU",    "type": "string",  "max_len": 512,  "required": False},
    {"index": 22, "header": "Цель напр.",   "param": "directionPurpose",           "type": "string",  "max_len": 40,   "required": True},
    {"index": 23, "header": "Событие",      "param": "events",                     "type": "string",  "max_len": None, "required": False},
    {"index": 24, "header": "Повторность",  "param": "isRepeat",                   "type": "boolean", "max_len": 1,    "required": True,  "allowed": ["0", "1", ""]},
    {"index": 25, "header": "Приемная",     "param": "receptionAPRF",              "type": "string",  "max_len": 50,   "required": True},
]

HEADERS = [f["header"] for f in FIELDS]
REQUIRED_FIELDS = [f["header"] for f in FIELDS if f["required"]]
BOOLEAN_FIELDS = [f["header"] for f in FIELDS if f["type"] == "boolean"]

# Маппинг boolean: CSV → система
BOOLEAN_MAPPING = {"1": True, "0": False, "": False}

# Недопустимые спецсимволы
FORBIDDEN_CHARS = {
    "\x00": "нулевой символ (Null)",
    "\t":   "символы табуляции (отступы)",
    "\x1a": "служебный символ конца файла (Ctrl+Z)",
    "\ufffd": "некорректные символы (�)",
    "\u2026": "символы многоточия",
}

# Допустимые значения для поля «Цель напр.»
DIRECTION_PURPOSE_VALUES = [
    "в дело", "в ином порядке в целях надзора", "в целях контроля",
    "В целях надзора", "для сведения", "запрос документов и материалов",
    "иной закон", "иной порядок", "иной порядок в дело",
    "иной порядок в целях надзора", "иной порядок в целях надзора в дело",
    "по компетенции",
]
