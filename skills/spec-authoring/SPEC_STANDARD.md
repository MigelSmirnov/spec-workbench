# Стандарт создания спецификации (global_spec.json)

Короткий индекс для точечных правок: [SPEC_STANDARD_INDEX.md](SPEC_STANDARD_INDEX.md).

## Зачем

Спецификация — единый источник правды о проекте. По ней:
- нормализатор строит модуль-центричную структуру
- билдер собирает контекст для каждого модуля
- агент-сборщик исправляет шумный код
- линкер верифицирует межмодульные вызовы

Если спека полная и точная — сборка проходит чисто. Если дырявая — агент будет угадывать и ошибаться.

---

## Структура файла

```json
{
  "contracts": { ... },
  "notes": [ ... ],
  "adapters": { ... },
  "config": { ... },
  "models": { ... },
  "rules": { ... },
  "imports": { ... },
  "module_functions": { ... },
  "module_order": [ ... ],
  "function_order": [ ... ],
  "module_hints": { ... },
  "module_paths": { ... },
  "default_module": "app"
}
```

---

## Архитектура создаваемого кода

Фабрика генерирует код с помощью LLM, поэтому спека должна задавать не только список функций, но и устойчивую архитектуру. Предпочтение отдаётся **глубоким модулям**: модуль должен иметь ясную ответственность, скрывать внутренние детали и отдавать наружу небольшой публичный API через `imports.internal`.

**Правила:**
- Модуль не обязан быть одним файлом. Если смысловой шов очевиден, лучше выделить новый модуль/файл через `module_paths`, чем наращивать один большой скрипт.
- Допустимы широкие правки спеки, если они нужны для глубоких модулей: перенос функций между модулями, выделение guard/helper/policy/catalog модулей, уточнение `module_order`, `imports.internal`, `module_paths`.
- Широкая правка спеки не должна менять продуктовую семантику сама по себе. Если меняется поведение, это должно быть явно отражено в notes/contracts/rules и проходить валидацию.
- Не складывай данные в notes. Поведение остаётся в notes, а значения, таблицы, словари, лимиты и политики выносятся в `config`, `models` или `rules`.
- Модуль `api` должен оставаться тонким роутером: HTTP wiring, auth/dependencies, request/response boundary. Бизнес-логика, policy checks, artifact guards, storage rules и rendering должны жить в отдельных модулях.
- Если endpoint начинает концентрировать много требований разных типов, это сигнал к декомпозиции, а не к добавлению ещё notes в router.

---

## 1. contracts

**Что это:** точные сигнатуры всех функций и методов проекта.

**Формат ключа:**
- Обычная функция: `"function_name"`
- Метод класса: `"ClassName.method_name"`

**Формат значения:** строка с типизированной сигнатурой Python.

**Правила:**
- Каждая публичная и приватная функция должна быть в contracts
- Сигнатура должна включать все аргументы с типами и возвращаемый тип
- `self` указывается для методов
- Дефолтные значения указываются: `db_path: str = DB_PATH`
- Используй реальные имена типов из проекта, не абстракции

```json
{
  "contracts": {
    "validate_file": "(file_bytes: bytes, filename: str) -> tuple[bool, str]",
    "extract_images": "(file_bytes: bytes, filename: str) -> list[Image.Image]",
    "Database.__init__": "(self, db_path: str = DB_PATH) -> None",
    "Database.save_result": "(self, meta: ProjectMeta, result: RecognitionResult) -> int",
    "ClaudeClient.recognize": "(self, image: Image.Image) -> RecognitionResult"
  }
}
```

**Частые ошибки:**
- Пропущен `self` у методов
- Не указан тип возврата (`-> None` тоже нужен)
- Имя в contracts не совпадает с реальным именем функции

---

## 2. notes

**Что это:** конкретные требования к реализации каждой функции.

**Формат:** массив строк. Каждая строка ДОЛЖНА начинаться с имени функции/метода/модуля и двоеточия. Новый стандарт notes использует classified prose:

```
"function_name: [NOTE_CLASS] описание требования"
"ClassName.method_name: [NOTE_CLASS] описание требования"
```

`[NOTE_CLASS]` — машинно-читаемый маркер из закрытого реестра классов. Человеческий текст после маркера остаётся основным semantic payload для LLM/codegen. Маркер не должен превращать note в псевдокод.

**Правила:**

### Обязательный префикс
```
ПРАВИЛЬНО: "parse_response: [VALIDATION_ERROR] MUST raise ValueError when JSON cannot be parsed"
ПРАВИЛЬНО: "Database.__init__: [CONFIG_REFERENCE] MUST read db path from = config.storage.db_path"

НЕПРАВИЛЬНО: "opens sqlite3.connect and calls _create_tables"
НЕПРАВИЛЬНО: "__init__: opens sqlite3.connect"  ← неоднозначно, чей __init__?
```

Для методов всегда используй полное имя `ClassName.method_name`, не голое имя метода. `__init__`, `to_dict`, `from_dict`, `close` — без класса невозможно определить принадлежность.

### Модуль-level notes
Для общих правил модуля, не привязанных к конкретной функции, используй префикс модуля или пиши без префикса (попадёт в module-level notes):

```
"image_pipeline: [RETURN_SHAPE] All public functions return PIL.Image.Image, never numpy array"
"logging: [DEPENDENCY_BOUNDARY] Use logging.getLogger(__name__) for all warnings"
```

### Реестр классов notes

Класс выбирается по основной роли note, а не по продуктовой теме. Нельзя плодить классы вида `CIRCUIT_LOGIC`, `OCR_LOGIC`, `RENDERING_BUSINESS_RULE`: это продуктовая таксономия, не стандарт notes.

Текущий реестр:
- `[BEHAVIOR]` — доменное поведение, когда более точный generic-класс не подходит.
- `[CONFIG_REFERENCE]` — требование ссылается на `= config.*`.
- `[MODEL_REFERENCE]` — требование ссылается на `= models.*`.
- `[RULE_REFERENCE]` — требование ссылается на `= rules.*`.
- `[FORBIDDEN_ACTION]` — запрет действия: MUST NOT, never, no file I/O, no direct access.
- `[SCHEMA_CONSTRAINT]` — форма модели/DTO/полей, required/optional/no extra fields.
- `[VALIDATION_ERROR]` — invalid/unsupported/missing input, raise/reject/error response.
- `[RETURN_SHAPE]` — структура возвращаемого значения или response shape.
- `[FIELD_ASSIGNMENT]` — присваивание/заполнение конкретного поля.
- `[FIELD_PROJECTION]` — перенос/проекция полей из одного объекта/слоя в другой.
- `[DETERMINISM_OR_ORDERING]` — стабильный порядок, deterministic ids, неизменность результата.
- `[PROVENANCE]` — источник данных, source_ref, tracking, audit trail.
- `[SECURITY_BOUNDARY]` — auth/owner scoping/access control/security boundary.
- `[PATH_OR_ARTIFACT_POLICY]` — artifact kind, path safety, file/artifact access policy.
- `[DEPENDENCY_BOUNDARY]` — allowed imports, layering, module dependency direction.
- `[TEST_EVIDENCE]` — проверочное ожидание, fixture/evidence, regression evidence.
- `[FALLBACK]` — degraded behavior, fallback path, tolerated incomplete input.
- `[ORCHESTRATION]` — wiring/orchestration: register route, import-and-call, thin wrapper, exception handler.

Если note смешивает несколько ролей, выбери primary class по смыслу, потеря которого сильнее изменит generated behavior. Не расщепляй note механически ради классификации, если это только ухудшает читаемость.

### Что включать в notes

**Поведение:**
```
"parse_response: [FALLBACK] if json.loads fails MUST attempt to extract JSON from raw text"
"ClaudeClient.recognize: [VALIDATION_ERROR] wrap API call in try/except anthropic.APIError and return a user-facing error"
```

**Формат данных:**
```
"ClaudeClient.recognize: [SCHEMA_CONSTRAINT] message format uses role/content parts accepted by the provider client"
"Database._create_tables: [SCHEMA_CONSTRAINT] creates the required storage table columns"
```

**Граничные случаи:**
```
"validate_item: [VALIDATION_ERROR] quantity must be int >= 1; if validation fails return None"
"export_excel: [FALLBACK] if items is empty, write an empty-result message in the output sheet"
```

**Промпты (для модулей с LLM-вызовами):**
```
"RECOGNITION_PROMPT: [BEHAVIOR] module-level constant instructs the model to return only raw JSON, no markdown"
```

**Что НЕ включать:**
- Очевидные вещи: `"save_result: saves result to database"` — это и так понятно из имени
- Реализацию: не пиши алгоритм построчно, пиши требования к поведению
- Дублирование contracts: сигнатура уже есть в contracts, не повторяй
- Inline-данные: таблицы соответствий, allow-lists, пороги, TTL, пути, рейтинги, размеры, словари alias'ов. Для них используй `config`, `models` или `rules`, а note оставляй address-only: `MUST use = rules.some_policy`.

---

## 3. adapters

**Что это:** правила преобразования аргументов при вызове функции из другого модуля.

**Когда нужен адаптер:** когда вызывающий модуль имеет данные в одном формате, а вызываемая функция ожидает другой.

**Формат:**

Вариант A — распаковка объекта в аргументы:
```json
{
  "validate_file": {
    "from": "UploadedFile",
    "mapping": ["file_bytes", "file.name"],
    "requires_cache": true
  }
}
```
Означает: вызывающий код имеет `UploadedFile` объект, нужно вызывать как `validate_file(file.getvalue(), file.name)`.

Вариант B — маппинг параметров:
```json
{
  "normalize_dpi": {
    "mapping": {
      "image": "arg0",
      "target_dpi": "literal:300"
    }
  }
}
```
Означает: `image` берётся из первого аргумента, `target_dpi` всегда равен 300.

**Правила:**
- Адаптер привязывается к имени функции, НЕ к имени модуля
- `requires_cache: true` — подсказка агенту, что нужно прочитать данные один раз (например `file.getvalue()`)
- Адаптер нужен только если формат аргументов отличается между caller и callee

**Частая ошибка:** забыть адаптер. Если функция принимает `(bytes, str)`, а вызывающий модуль имеет объект `UploadedFile` — без адаптера агент передаст объект целиком.

---

## 4. config

**Что это:** runtime/product configuration: плоские значения, лимиты, пути, TTL, feature knobs, списки разрешённых пользовательских ключей.

```json
{
  "config": {
    "role": "data",
    "schema_version": 1,
    "public_calc": {
      "rate_limit": {
        "max_requests": 20,
        "window_seconds": 3600
      }
    }
  }
}
```

**Правила:**
- `role` имеет служебное значение `"data"`; `schema_version` на верхнем уровне — целое число версии секции.
- Имена `role` и `schema_version` зарезервированы и не используются внутри вложенных namespace.
- В `config` идут небольшие runtime/product knobs, которые могут меняться независимо от моделей предметной области.
- Notes ссылаются на config адресно: `"calc_generate_endpoint: [CONFIG_REFERENCE] MUST enforce rate limit using = config.public_calc.rate_limit"`.
- Не клади в `config` большие структурные доменные таблицы, enum definitions или Pydantic schema semantics.

---

## 5. models

**Что это:** описание dataclass'ов и DTO проекта.

```json
{
  "models": {
    "RecognitionResult": {
      "fields": {
        "items": "list[SpecItem]",
        "raw_response": "str",
        "model_used": "str",
        "processing_time": "float",
        "image_hash": "str"
      }
    }
  }
}
```

**Правила:**
- Указывай все поля с типами
- Если поле имеет default — укажи в типе: `"str = ''"` или добавь note
- Модели должны совпадать с реальными dataclass'ами в `models.py`
- Большие структурные доменные справочники и catalog/mapping tables тоже живут в `models`, если это domain taxonomy или upstream/downstream contract.
- Не смешивай таблицы только потому, что у них похожая форма. Решение о merge/split принимается по change-axis: что меняется вместе и по одной причине.

### kind моделей

Запись в `models` может объявлять `kind`. Реестр закрытый:

| `kind` | Значение |
| --- | --- |
| (отсутствует) | обычная модель-произведение: `fields` обязательны |
| `enum` | перечисление с закрытым списком значений |
| `mapping`, `vocabulary`, `catalog` | структурные spec-данные (read-only справочники), не runtime-DTO |
| `discriminated_union` | именованный тип-сумма (см. ниже) |
| `interface` | порт с методами, объявленными в `contracts` (см. ниже) |

Неизвестный `kind` делает спеку невалидной; компилятор обязан отказать
(fail-closed), а не эмитить заглушку.

### kind: discriminated_union

Тип-сумма: значение — ровно один из закрытого списка вариантов, выбираемый по
полю-дискриминатору. Вторая половина алгебры типов рядом с моделью-произведением;
эквиваленты — OpenAPI `oneOf` + `discriminator`, protobuf `oneof`.

```json
"TypedValue": {
  "kind": "discriminated_union",
  "discriminator": "value_type",
  "variants": ["StringValue", "IntegerValue", "DecimalValue", "BooleanValue"]
}
```

**Правила (нарушение = невалидная спека):**
- `discriminator` и непустой `variants` обязательны; `fields` отсутствует или пуст
- каждый variant — объявленная в этой же спеке модель с `fields`
- каждый variant содержит поле с именем дискриминатора типа `Literal['…']`
  с уникальным в пределах union значением
- union внутри union (variant с `kind: discriminated_union`) запрещён
- union — именованный тип: употребим в полях моделей и сигнатурах contracts
  наравне с моделями

Семантика: при десериализации variant выбирается по значению дискриминатора.
Форма эмиссии (например, `Annotated[Union[…], Field(discriminator=…)]`) —
деталь компилятора: backend вправе эмитить alias для именованной конструкции
языка, но произвольный `type_alias` в спеке запрещён.

### kind: interface

Порт: узкая граница, за которой прячется реализация (repository, unit of work,
authorizer, gateway). Интерфейс не вводит нового синтаксиса сигнатур — методы
объявляются в `contracts` под ключами `ИмяИнтерфейса.метод`, как обычные
классовые методы:

```json
"models": {
  "DiagramRepository": { "kind": "interface" }
},
"contracts": {
  "DiagramRepository.get": "(self, diagram_id: DiagramId) -> Diagram | None",
  "DiagramRepository.save": "(self, diagram: Diagram) -> None"
}
```

**Правила (нарушение = невалидная спека):**
- интерфейс, экспортируемый модулем (`imports.internal`), обязан иметь хотя бы
  один контракт `Имя.*`
- каждый такой контракт — полная машинно-проверяемая сигнатура: все параметры
  с типами и возвращаемый тип; усечённые записи не допускаются
- у интерфейса нет `fields` и нет данных
- восстанавливать методы интерфейса из реализаций (кода, ORM-классов)
  запрещено: спека — единственный источник истины; отсутствие method
  contracts у экспортированного порта — дефект спеки

---

## 6. rules

**Что это:** read-only structured policy data: нормативные правила, layout policy, routing policy, fallback policy, threshold tables.

```json
{
  "rules": {
    "example_policy": {
      "kind": "policy",
      "threshold": 10
    }
  }
}
```

**Правила:**
- `rules` — не исполняемый код и не псевдокод. Представляй политику декларативно.
- Не смешивай `rules` с `config`: config — runtime knobs, rules — domain/policy semantics.
- Не переносись сюда schema/model definitions.
- Notes ссылаются на rules адресно: `"derive_policy: [RULE_REFERENCE] MUST use = rules.example_policy.threshold"`.

---

## 7. imports

```json
{
  "imports": {
    "stdlib": ["os", "json", "logging", "sqlite3"],
    "third_party": [
      "import streamlit as st",
      "from PIL import Image",
      "import anthropic"
    ],
    "internal": {
      "models": ["SpecItem", "ProjectMeta", "RecognitionResult", "CLAUDE_MODEL", "DB_PATH"],
      "upload_handler": ["validate_file", "extract_images"],
      "preprocessor": ["preprocess"],
      "claude_client": ["ClaudeClient"],
      "exporter": ["export_excel", "export_pdf"],
      "db": ["Database"],
      "parser": ["parse_response"]
    }
  }
}
```

**Правила:**
- `stdlib` — имя модуля (`"json"`) или полная import-строка
  (`"from decimal import Decimal"`). Голое имя модуля — runtime-импорт, оно
  **не связывает типовых имён**; тип, используемый в полях или сигнатурах,
  обязан быть связан полной строкой
- `third_party` — полные строки импорта как в коде
- `internal` — модуль → список экспортируемых символов (функции, классы, константы)
- Полные import-строки — авторская форма записи. Нормализация разбирает их
  один раз в структурную форму (module, symbol, alias); все последующие
  инструменты (resolver, validator, inspector, slicing, generator) работают
  только по структурной таблице, а не по regex-разбору Python-текста

**`internal` — ключевая секция.** По ней определяется:
- Что каждый модуль экспортирует
- Какие зависимости у каждого модуля
- Куда направлять адаптеры и контракты при сборке

---

## 8. module_functions

**Что это:** явный маппинг каждой функции/класса/константы на модуль.

```json
{
  "module_functions": {
    "app": ["check_api_key", "init_session_state", "render_sidebar", "main"],
    "claude_client": ["ClaudeClient", "RECOGNITION_PROMPT"],
    "db": ["Database"],
    "models": ["SpecItem", "ProjectMeta", "RecognitionResult", "CLAUDE_MODEL", "DB_PATH"],
    "parser": ["validate_item", "parse_response"],
    "preprocessor": ["to_rgb", "auto_rotate", "enhance_scan", "normalize_dpi", "preprocess"],
    "upload_handler": ["get_extension", "validate_file", "extract_images"],
    "exporter": ["export_excel", "export_pdf"]
  }
}
```

**Правила:**
- Каждая функция и константа из `contracts` должна быть ровно в одном модуле
- Для классов — указывай имя класса, методы подтянутся автоматически
- Константы (UPPER_CASE) тоже включай
- Если функция не указана — она попадёт в модуль из `default_module` (по умолчанию `"app"`)
- Предпочитай глубокие модули с ясными смысловыми границами. Если функция является guard/policy/catalog/storage/render helper, вынеси её в соответствующий модуль, а не оставляй в толстом endpoint/script.
- `api`/router modules должны содержать минимум orchestration и не становиться владельцами бизнес-логики.

**Разница с `imports.internal`:**
- `imports.internal` — что модуль ЭКСПОРТИРУЕТ другим (публичный API)
- `module_functions` — что модуль СОДЕРЖИТ внутри (все функции, включая внутренние)

Пример: `preprocessor` экспортирует только `preprocess`, но содержит также `to_rgb`, `auto_rotate`, `enhance_scan`, `normalize_dpi`.

---

## 9. module_order и function_order

```json
{
  "module_order": ["upload_handler", "preprocessor", "claude_client", "parser", "exporter", "db", "app"],
  "function_order": ["check_api_key", "init_session_state", "render_sidebar", "..."]
}
```

- `module_order` — порядок сборки модулей (зависимости идут первыми)
- `function_order` — порядок функций внутри файлов (для читаемости)
- Если добавлен новый helper/guard/catalog/policy модуль, явно поставь его в `module_order` после его зависимостей и до потребителей.

---

## 10. module_hints

**Что это:** ключевые слова для каждого модуля, помогающие нормализатору привязать неоднозначные notes к правильному модулю.

**Когда нужен:** когда note не начинается с точного имени функции (module-level notes, заметки с неоднозначным контекстом). Нормализатор ищет ключевые слова в тексте ноты и определяет, к какому модулю она относится.

```json
{
  "module_hints": {
    "db": ["sqlite", "sqlite3", "db_path", "conn", "INSERT", "DELETE"],
    "parser": ["json.loads", "markdown", "validate_item", "VALID_CATEGORIES"],
    "preprocessor": ["PIL", "Image.Image", "numpy", "cv2", "dpi", "enhance"],
    "app": ["streamlit", "st.", "session_state", "sidebar"]
  }
}
```

**Правила:**
- Ключ — имя модуля (должен совпадать с ключом в `module_functions`)
- Значение — список строк-подсказок, которые могут встретиться в тексте notes
- Включай: имена библиотек, характерные термины, имена таблиц/полей, ключевые переменные
- Не дублируй имена функций — они и так матчатся напрямую по contracts
- Чем специфичнее ключевые слова, тем точнее disambiguation

**Без этой секции** нормализатор не сможет распределять неоднозначные notes по модулям и будет складывать их в модуль по умолчанию.

---

## 11. module_paths

**Что это:** маппинг модулей на пути в файловой системе проекта.

**Когда нужен:** когда проект использует вложенную структуру директорий, а не плоскую раскладку файлов.

```json
{
  "module_paths": {
    "models": "core/models",
    "db": "storage/db",
    "parser": "core/parser",
    "preprocessor": "processing/preprocessor",
    "app": "app"
  }
}
```

**Правила:**
- Ключ — имя модуля (как в `module_functions`)
- Значение — путь без расширения `.py` (добавляется автоматически)
- Если модуль не указан в `module_paths` — дефолтится к `"<module_name>.py"` в корне
- Если секция отсутствует целиком — все модули ложатся в корень (плоская структура)
- Вложенная структура предпочтительна, когда она отражает смысловые границы: `core/*`, `domain/*`, `services/*`, `adapters/*`, `rendering/*`, `api/*`.
- Не бойся разделять старый файл на несколько `module_paths`, если это уменьшает связность и делает промпт для LLM уже и точнее.

**Пример использования:** агент при генерации кода берёт `path` из нормализованной спеки и создаёт файл по указанному пути: `core/models.py`, `storage/db.py` и т.д.

---

## 12. default_module

**Что это:** имя модуля, в который попадают все неопределённые функции и notes.

```json
{
  "default_module": "app"
}
```

**Правила:**
- Строка с именем модуля
- Если секция отсутствует — дефолтится к `"app"`
- Модуль с этим именем должен существовать в `module_functions`
- Сюда попадают: функции из `contracts` без записи в `module_functions`, notes которые не удалось привязать ни к одному модулю

---

## 13. Система типов и происхождение имён

**Что это:** правило замыкания языка. Пространство типов спеки состоит из трёх
источников:

1. **builtins** — закрытый список, фиксируемый этим стандартом:
   `str`, `int`, `float`, `bool`, `bytes`, `None`, `object`, `dict`, `list`,
   `set`, `tuple`, `Exception`, `BaseException`, плюс формы `Literal[...]`,
   `type[X]` и nullable-запись `X | None`.
   Список не расширяется под проект.
2. **объявленные модели** всех `kind` (включая `discriminated_union`,
   `interface`, enum и структурные spec-данные).
3. **символы, связанные полными import-строками** в `imports.stdlib` /
   `imports.third_party` (после структурной нормализации, см. раздел 7).
4. **классы, которыми владеют модули**: символ, экспортируемый через
   `imports.internal` и имеющий хотя бы один классовый контракт
   `Имя.метод` в `contracts`. Экспортированные функции и константы типами
   не являются.

**Правила:**
- Каждое имя в type position (поле модели, сигнатура contracts, `variants`)
  обязано резолвиться ровно в один источник. Неизвестное имя — ошибка
  валидации, не warning.
- **Коллизия происхождения — всегда BLOCK:** builtin, модель, import,
  interface и union не могут неоднозначно владеть одним локальным именем.
- Таблицу происхождения строит один общий resolver; validator, inspector,
  slicing и generator обязаны использовать его, а не собственные списки.
  Проектные allowlist'ы известных типов запрещены.

### Нормативный NOT-list

Следующее в язык спецификаций **не входит**. Это нормативные запреты, а не
пояснительные заметки; их обход через notes или нестандартные ключи делает
спеку невалидной:

- generics / TypeVar
- untagged unions — union без дискриминатора (nullable-форма `X | None`
  остаётся полевой записью, а не union-конструкцией)
- callable-типы и иные runtime-only типы в полях моделей
- модельное наследование как механизм union: принадлежность варианта
  объявляется в `variants`, а не через subclass
- проектное расширение builtins: новый тип — это модель, объявленный import
  или изменение этого стандарта
- восстановление `interface` из реализации: методы порта существуют только в
  `contracts`
- произвольный именованный `type_alias`: alias может появляться лишь как
  форма эмиссии именованных конструкций языка (см. раздел 5)

---

## Чек-лист перед запуском сборки

0. **Запусти валидатор:** `python validate_spec.py global_spec.json` — он проверит всё из этого списка автоматически.

1. **Каждая функция в contracts?** Проверь что нет функций без сигнатуры.

2. **Каждая функция в module_functions?** Проверь что ничего не потерялось.

3. **Notes с префиксами и классами?** Каждая новая note начинается с `"function_name: [NOTE_CLASS]"` или `"ClassName.method_name: [NOTE_CLASS]"`.

4. **Нет неоднозначных имён?** `__init__`, `to_dict`, `close` — всегда с классом: `"Database.__init__:"`.

5. **Адаптеры на стыках?** Если модуль A вызывает функцию модуля B, и A имеет данные в другом формате — нужен адаптер.

6. **imports.internal полный?** Каждый модуль экспортирует то, что другие реально импортируют.

7. **config/models/rules разведены?** Runtime knobs лежат в `config`, domain schemas/catalogs в `models`, policy tables в `rules`; inline-данные не остаются в notes.

8. **models описаны?** Все dataclass'ы с полями и типами.

9. **module_order корректный?** Зависимости идут раньше зависимых. `models` всегда первый; `rules`/`config` доступны до модулей, которые на них ссылаются.

10. **module_hints заполнены?** Ключевые слова для каждого модуля, иначе disambiguation notes не работает.

11. **module_paths заполнены?** Если проект не плоский — укажи пути для каждого модуля.

12. **Типы замкнуты?** Каждое имя в type position — builtin, объявленная модель или символ, связанный полной import-строкой; коллизий происхождения нет (раздел 13).

13. **Порты полны?** Каждый экспортируемый `kind: interface` имеет полные method contracts; у каждого `discriminated_union` — discriminator, закрытые variants и `Literal`-теги.

---

## Пример минимальной спеки для нового проекта

```json
{
  "contracts": {
    "fetch_data": "(url: str, timeout: int = 30) -> dict",
    "transform": "(data: dict) -> list[Item]",
    "save": "(items: list[Item], path: str) -> None"
  },
  "notes": [
    "fetch_data: [CONFIG_REFERENCE] MUST call requests.get using timeout from = config.fetch.timeout_seconds",
    "fetch_data: [VALIDATION_ERROR] MUST raise on non-200 HTTP status",
    "fetch_data: [RETURN_SHAPE] MUST return response.json()",
    "transform: [BEHAVIOR] MUST filter items where status is active",
    "transform: [DETERMINISM_OR_ORDERING] MUST sort by created_at descending",
    "save: [CONFIG_REFERENCE] MUST write JSON using = config.output.json_format"
  ],
  "adapters": {},
  "config": {
    "role": "data",
    "schema_version": 1,
    "fetch": {
      "timeout_seconds": 30
    },
    "output": {
      "json_format": {
        "indent": 2,
        "ensure_ascii": false
      }
    }
  },
  "models": {
    "Item": {
      "fields": {
        "id": "str",
        "name": "str",
        "status": "str",
        "created_at": "str"
      }
    }
  },
  "rules": {},
  "imports": {
    "stdlib": ["json"],
    "third_party": ["import requests"],
    "internal": {
      "models": ["Item"],
      "fetcher": ["fetch_data"],
      "transformer": ["transform"]
    }
  },
  "module_functions": {
    "models": ["Item"],
    "fetcher": ["fetch_data"],
    "transformer": ["transform"],
    "saver": ["save"]
  },
  "module_order": ["models", "fetcher", "transformer", "saver"],
  "module_hints": {
    "fetcher": ["requests", "url", "timeout", "HTTP"],
    "transformer": ["filter", "sort", "active", "status"],
    "saver": ["json", "write", "indent", "file"]
  },
  "module_paths": {},
  "default_module": "main"
}
```

**Примечания к примеру:**
- `module_hints` — минимальный набор ключевых слов для disambiguation; в реальном проекте список будет больше
- `module_paths` — пустой означает плоскую структуру (все файлы в корне)
- `default_module` — `"main"` вместо `"app"`, потому что точка входа в этом проекте называется `main.py`
