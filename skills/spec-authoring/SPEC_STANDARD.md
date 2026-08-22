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
  "standard_version": 2,
  "contracts": { ... },
  "notes": [ ... ],
  "config": { ... },
  "models": { ... },
  "implementation_obligations": { ... },
  "rules": { ... },
  "persistence": { ... },
  "properties": { ... },
  "determinism": { ... },
  "imports": { ... },
  "module_functions": { ... },
  "module_order": [ ... ],
  "function_order": [ ... ],
  "module_paths": { ... },
  "default_module": "app"
}
```

`standard_version` — обязательная целочисленная редакция этого стандарта.
Отсутствующее или неизвестное значение является BLOCK: умолчание и чтение по
«ближайшей» версии запрещены. Нормализатор сохраняет значение без изменения;
editor, deploy, handoff, verification и terminal OTK записывают его в lineage
рядом с хэшами base и normalized spec. Изменение нормативного прочтения
существующего ключа требует новой редакции, даже если JSON-форма не изменилась.

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
"module_name: [NOTE_CLASS] описание требования"
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
Для общих правил модуля, не привязанных к конкретной функции, обязательно используй точный префикс модуля:

```
"image_pipeline: [RETURN_SHAPE] All public functions return PIL.Image.Image, never numpy array"
"logging: [DEPENDENCY_BOUNDARY] Use logging.getLogger(__name__) for all warnings"
```

Нота без префикса запрещена. Нормализатор разрешает адресата только тремя
механизмами: точный `function_name:`, точный `ClassName.method_name:` и точный
`module_name:`. Поиск имён и ключевых слов в теле ноты, контекстные hints и
падение в `default_module` не являются допустимыми механизмами. Если префикс не
соответствует явно объявленной функции, методу или модулю, нормализация
завершается ошибкой до генерации.

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

**Несовпадение форм на стыке вызова:**

Если caller располагает данными в форме, отличной от контракта callee, это
поведение принадлежит конкретному вызову и записывается классифицированной
нотой caller-а, например:

```text
process_upload: [ORCHESTRATION] MUST call validate_file with the uploaded byte content and filename and MUST read the byte content once
```

Владелец такой ноты — caller/callsite, не callee. Нота остаётся требованием к
поведению: выражения, вызовы методов, точечная навигация и строковый
микро-синтаксис в ней запрещены. Нормативные значения размещаются процедурой
15.2 и адресуются ссылкой. Если точный внешний способ извлечения значения
является частью контракта, он объявляется отдельным портом/контрактом, а не
прячется псевдокодом в note.

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
    "role": "data",
    "schema_version": 1,
    "RecognitionResult": {
      "identity": "value",
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
- `role` имеет служебное значение `"data"`; `schema_version` на верхнем
  уровне — целое число версии секции. Имена зарезервированы и не являются
  объявлениями моделей.
- Указывай все поля с типами
- Если поле имеет default — укажи в типе: `"str = ''"` или добавь note
- Модели должны совпадать с реальными dataclass'ами в `models.py`
- Каждая runtime-модель без `kind` обязана объявлять
  `identity: "value"|"entity"`; модели с `kind` поле `identity` не содержат.
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

### 5.1 implementation_obligations

`implementation_obligations` машинно связывает interface-typed dependency с
его способом реализации. Это не прежний call-shape `adapters` DSL: секция не
преобразует аргументы и не описывает вызовы. Она закрывает архитектурный вопрос,
который нельзя восстанавливать из имён классов или текста notes.

```json
"implementation_obligations": {
  "DiagramRepository": {
    "disposition": "local",
    "implementations": ["PostgresDiagramRepository"]
  },
  "IdentityProvider": {
    "disposition": "external"
  }
}
```

**Правила (нарушение = BLOCK до Factory handoff):**

- каждый `kind: interface`, используемый в type position параметра другого
  контракта, обязан иметь ровно одну запись;
- `disposition` принадлежит закрытому реестру `local|external`;
- `local` содержит непустой уникальный список `implementations`; каждый символ
  является объявленным concrete-классом в `module_functions` и имеет contract
  для каждого метода interface с той же канонической сигнатурой;
- модуль-владелец каждой `local` concrete-реализации выбирается
  зарегистрированным deterministic backend IR; fallback в LLM-генерацию
  запрещён, потому что сигнатуры и prose не замыкают исполняемую границу;
- `external` не содержит local implementations и явно оставляет создание
  реализации внешнему composition/deployment boundary;
- имя, общий суффикс, соседство в модуле и prose note не доказывают отношение
  concrete↔interface;
- генератор получает эту секцию в local spec как implementation obligations и
  не вправе считать один только `__init__` полной реализацией порта.

---

## 6. rules

**Что это:** read-only structured normative data двух непересекающихся видов:
project policy data и зарезервированные versioned backend IR.

```json
{
  "rules": {
    "role": "data",
    "schema_version": 1,
    "example_policy": {
      "kind": "policy",
      "threshold": 10
    }
  }
}
```

**Правила:**
- `role` имеет служебное значение `"data"`; `schema_version` на верхнем
  уровне — целое число версии секции. Имена зарезервированы и не являются
  политиками.
- Обычный ключ `rules` содержит декларативную domain/policy semantics и не
  является исполняемым кодом или псевдокодом.
- Зарезервированный backend namespace имеет `kind`, `schema_version` и
  `backend`; его полную закрытую форму определяет соответствующий подраздел
  этого стандарта. Backend IR не является project policy и не может молча
  наследовать поля другой версии.
- Не смешивай `rules` с `config`: config — runtime knobs, rules — domain/policy semantics.
- Не переносись сюда schema/model definitions.
- Notes ссылаются на rules адресно: `"derive_policy: [RULE_REFERENCE] MUST use = rules.example_policy.threshold"`.

### 6.0 Закрытый словарь backend IR

Детерминированный backend читает только форму, полностью известную его версии.
Ссылка на источник значения внутри backend IR является объектом закрытого
словаря, а не строковым выражением:

```json
{"ref": "parameter", "path": ["invoice_id"]}
{"ref": "literal", "value": 300}
```

**Правила (нарушение = невалидная спека):**

- `ref` — листовой объект. Значения всех его полей — JSON-скаляры либо массивы
  JSON-скаляров. Вложенный объект, вложенный `ref` и массив объектов запрещены.
- `literal:300`, `arg0`, `payload.email`, `file.getvalue()`, `Capability.X` и
  иной строковый микро-синтаксис запрещены.
- Допустимые `ref`, их точные поля и значения принадлежат версии конкретного
  backend-а. Допустимость ref в другом backend-е ничего не разрешает.
- Неизвестный ref, поле или enum-значение останавливает сборку fail-closed.
- Реестр конструкций backend-а не содержит проектных имён. Проектные имена
  являются значениями валидных ячеек IR, но не расширяют словарь конструкций.
- Последовательность операций не является значением спеки. Спека объявляет
  форму; порядок и число операций lowering-а детерминированы backend version.

§6.0 действует только для backend IR. Notes остаются прозой требований, однако
общий запрет псевдокода в notes сохраняется.

### 6.1 `http_router_backend/v1`

`rules.http_router_backend` — нормативный IR детерминированной сборки тонкого
HTTP-router. Он описывает экспонирование handler-ов, transport wiring и
принадлежность исключений, но не повторяет Python-контракты.

Обязательный верхнеуровневый состав версии 1 показан ниже; пустые коллекции и
`error_policy` здесь только сокращают схему и должны быть заполнены согласно
инвариантам валидатора:

```json
{
  "kind": "http_router_backend",
  "schema_version": 1,
  "backend": {"framework": "fastapi", "emitter": "fastapi_sync_v1"},
  "wiring": {
    "module": "api",
    "app_factory": "create_app",
    "request_parameter": "request",
    "state_bindings": {
      "store": {"factory_parameter": "store", "state_attribute": "store"}
    },
    "credential_extractors": {}
  },
  "auth_policies": {},
  "principals": {},
  "routes": [],
  "projections": [],
  "error_policy": {},
  "irregular_ownership": {"module": "api_irregular"}
}
```

Маршрут с `emission: "table"` содержит только transport/orchestration data:

```json
{
  "handler": "get_invoice",
  "method": "GET",
  "path": "/invoices/{invoice_id}",
  "auth": "staff_bearer",
  "success_status": 200,
  "response_mode": "json",
  "emission": "table",
  "authorize": [],
  "delegate": {
    "function": "load_invoice",
    "args": [
      {"ref": "slot", "name": "store"},
      {"ref": "parameter", "path": ["invoice_id"]},
      {"ref": "enum", "type": "Capability", "member": "INVOICE_READ"}
    ]
  },
  "projection": null,
  "returns": "delegate"
}
```

Нормативные инварианты:

- Единственный источник сигнатуры handler-а, app factory, resolver-а,
  delegate-а и projection-функции — `contracts[function]`. Поле `signature` в
  route row запрещено. Path parameters и parameter refs обязаны разрешаться
  через этот контракт и поля `models`.
- Аргумент вызова — объект закрытого DSL, а не Python-строка. Версия 1 знает
  только `slot`, `credential`, `parameter`, `enum` и JSON-scalar `literal`.
  Неизвестный `ref`, дополнительное поле или строка вроде
  `"payload.email"`/`"Capability.X"` — дефект спеки.
- `wiring.state_bindings` связывает параметры контракта app factory с
  атрибутами app state; имена slots проектные. Backend не содержит
  project-specific классов, state names, capability constants или companion
  module names.
- `principals`, `auth_policies`, `authorize`, `delegate` и `projection`
  ссылаются только на объявленные функции/slots/credentials. Число аргументов
  проверяется по canonical contract; результат authorization-step может
  связать один `context`, delegate — `result` для projection.
- `projections` обязаны точно покрывать поля модели возвращаемого типа из
  контракта projection-функции. Форма модели и сигнатура в IR не дублируются.
- Маршрут `emission: "irregular"` не содержит скрытого тела. Он объявляет
  `irregular_reason`, а handler обязан принадлежать ровно companion-модулю из
  `irregular_ownership.module`. Router только импортирует и регистрирует его.
- `irregular_ownership` является механизмом реестра маршрутов: handler —
  свободная функция, а обязательство router-а исчерпывается регистрацией.
  Механизм неприменим к членам типа. Перенос метода класса в другой модуль не
  освобождает класс от реализации метода; распространение companion ownership
  на repositories и другие типы является дефектом спеки.
- `error_policy` задаёт единое отображение exception → HTTP status. Доступные
  router-модулю исключения обязаны быть прямыми imports; намеренно недоступные
  перечисляются в `unavailable_to_module` и lower-ятся backend-ом без
  project-specific констант.
- Пара `(method, path)` и `handler` уникальны; status/method/response/return
  modes принадлежат закрытым реестрам версии backend. Неизвестные поля на всех
  узлах запрещены.
- Если `http_router_backend/v1` присутствует и владеет router-модулем,
  генерация fail-closed: дефект IR останавливает сборку, а не переводит модуль
  на LLM. Отсутствие IR оставляет проекту обычный недетерминированный путь.

Версия backend является частью значения. Новая форма extractor-а, ref-а,
response mode или lowering требует новой поддерживаемой версии; emitter не
угадывает форму по существующему Python-коду.

### 6.2 `persistence_backend/v2`

`rules.persistence_backend` — нормативный IR детерминированной сборки SQLite
repository-модулей. `persistence_backend/v1` был донормативной реализацией без
текста стандарта и не поддерживается. Первая нормативная версия — 2.

Верхнеуровневая форма v2 закрыта:

```json
{
  "kind": "persistence_backend",
  "schema_version": 2,
  "backend": {"engine": "sqlite", "emitter": "sqlite_sync_v2"},
  "conventions": {
    "assert_open": "inside_try",
    "guard_reraise": "unchanged",
    "codec_naming": "row_to_snake_model",
    "primary_key_not_null": "always"
  },
  "tables": [],
  "aggregates": [],
  "repositories": []
}
```

Дополнительные поля запрещены на каждом узле. Коллекции являются списками;
идентификаторы таблиц, агрегатов, репозиториев и методов уникальны.

#### Таблицы и колонки

Каждая table row содержит ровно `table`, `table_name_ref`, `model`, `read_by`,
`columns`, `primary_key`, `unique`. Column row содержит ровно `column`, `field`,
`storage`, `nullable`, `check`, `element_model`. Эти ячейки ссылаются на уже
объявленные models/config и не повторяют тип поля. `primary_key` и строки
`unique` — непустые списки имён колонок. `read_by` равен module name или null;
`check` и `element_model` имеют закрытые формы валидатора версии.

#### Aggregate persistence

Если repository contract принимает или возвращает объявленный aggregate,
состоящий из персистируемых моделей в форме реестра v2, backend обязан принять
и детерминированно lower-ить эту форму. Неподдержка является `DEFECT` версии,
а не разрешённым пропуском или основанием для генерации по догадке.

Aggregate row имеет ровно `aggregate`, `root` и `relations`. Root row содержит
`field`, `model`, `table`, `key`. Relation row содержит `field`, `model`,
`table`, `cardinality`, `root_columns`, `related_columns`, `order_by`.
`root_columns` и `related_columns` — равнодлинные непустые списки скаляров;
поэлементные пары задают join и допускают разные имена колонок. `field`
обязан резолвиться в поле aggregate model с соответствующим model type;
`cardinality: "one"` требует неoptional поле и ровно одну строку,
`cardinality: "many"` — `list[Model]`. Версия 2 знает только обязательную
`one` и коллекционную `many`; появление допустимого repository aggregate с
иной cardinality означает `DEFECT` версии.

Все поля aggregate model обязаны быть покрыты root/relations. Runtime outcome,
default, fallback и иное неперсистируемое значение не добавляются literal-ом в
aggregate IR: они принадлежат другой модели/слою. Поэтому значение вроде
`replayed` не может быть угадано lowering-ом.

Repository row имеет одну из двух закрытых форм:

- deterministic: ровно `repository`, `module`, `schema_function`,
  `emission: "table"`, `methods`;
- irregular: ровно `repository`, `module`, `schema_function`,
  `emission: "irregular"`, `irregular_reason`.

Один persistence module владеет ровно одной repository class и её schema
function. Нерегулярность одного метода делает весь такой module irregular;
частичная эмиссия класса/файла и companion-делегирование отсутствуют.

Для обычной table method версия 2 сохраняет закрытые виды `insert`,
`insert_many`, `get_by_key`, `get_unique`, `list_by`, `update_fields`,
`update_many`, `upsert`. Их обязательные ячейки соответственно:

```text
insert, insert_many                 -> table, columns
get_by_key                          -> table, filter, select
get_unique                          -> table, filter, select, on_multiple
list_by                             -> table, filter, select, order_by
update_fields, update_many          -> table, filter, updates, require_existing
upsert                              -> table, columns, conflict, updates
```

Aggregate methods образуют закрытый реестр:

```text
get_aggregate_by_key                -> aggregate, filter
get_aggregate_by_unique             -> aggregate, filter, on_multiple
list_aggregates_by                  -> aggregate, filter, order_by
insert_aggregate                    -> aggregate
replace_aggregate                   -> aggregate
```

Method row всегда содержит `method` и `query` плюс ровно ячейки выбранного
вида. `filter`, `order_by`, column lists и `on_multiple` используют закрытые
формы этой версии; field/column/model names обязаны резолвиться. Список шагов,
SQL, временные значения и передача результата между запросами отсутствуют.
Чтение root, обязательных one relations и many relations, а также запись или
замена их строк разворачиваются lowering-ом на переданном соединении.

#### Владение транзакцией и guarded mutation

Backend не владеет `begin`, `commit`, `rollback` или `close`: открытое
соединение передаёт внешний Unit of Work. Это не запрещает lowering-у выполнить
несколько SQL-операций внутри уже открытой транзакции.

Условие записи, зависящее от доменного состояния другой сущности, не является
storage shape. Например, разрешение записи только при project-specific enum
state принадлежит policy/use case или порту и не расширяет persistence IR.
Метод с таким требованием irregular, пока требование остаётся на repository
boundary.

Версия backend является частью значения. Новая форма relation, query,
constraint или storage representation требует новой поддерживаемой версии.
Владение транзакцией, второй движок, блокировка и множественные фильтры
введены версией 3 (§6.3); в версии 2 они остаются невалидными.

---

### 6.3 `persistence_backend/v3`

Версия 3 — надмножество версии 2. Форма таблиц, колонок, агрегатов, видов
запросов и конвенций не меняется; v3 добавляет ровно семь вещей, каждая из
которых в v2 останавливала сборку репозиториев, чьи контракты уже приняты:

1. второй движок — PostgreSQL;
2. владение транзакцией репозиторием;
3. вид метода `lock`;
4. два bind-а фильтра для множеств и необязательных аргументов;
5. формы хранения `json_model` и `json_value` для вложенных значений;
6. адресация ключей внутри вложенных значений (`path`) в фильтрах и
   `unique`;
7. виды запросов `upsert_many` и `list_all`.

Всё остальное читается по §6.2. Версия — часть значения: спека с
`schema_version: 3` валидируется только правилами v3, спека с
`schema_version: 2` никогда не получает v3-формы по умолчанию.

#### Движок

`backend` принимает ровно одну из двух закрытых пар:

```json
{"engine": "sqlite", "emitter": "sqlite_sync_v2"}
{"engine": "postgres", "emitter": "postgres_sync_v1"}
```

Движок не меняет IR. Типы DDL, плейсхолдеры, синтаксис `ON CONFLICT`,
драйвер (`sqlite3` или `psycopg`) и форма блокировки принадлежат emitter-у
названной версии. Неизвестная пара останавливает сборку fail-closed.

#### Владение транзакцией

Repository row в deterministic-форме v3 содержит ровно `repository`,
`module`, `schema_function`, `emission: "table"`, `transaction`, `methods`.
Irregular-форма получает ту же ячейку `transaction`. Значение закрыто:

- `"external"` — как в v2: конструктор принимает открытое соединение, backend
  не владеет `begin`/`commit`/`rollback`/`close`;
- `"owned"` — репозиторий сам открывает одну транзакцию на одну операцию
  сервиса. Конструктор обязан иметь контракт
  `(self, database_url: str) -> None`; класс обязан объявить в `contracts`
  ровно `begin(self) -> None`, `commit(self) -> None`,
  `rollback(self) -> None`. Эти три метода **не** перечисляются в `methods`:
  их lowering фиксирован версией — `begin` открывает соединение и
  транзакцию и отвергает вложенный `begin`; `commit` фиксирует ровно один раз
  и освобождает соединение; `rollback` идемпотентен, освобождает соединение
  и не скрывает исходную ошибку. Все `methods` выполняются на соединении
  активной транзакции; вызов без активной транзакции — ошибка, а не
  autocommit.

Для `transaction: "owned"` `schema_function` имеет контракт
`(database_url: str) -> None`: она открывает собственное соединение,
идемпотентно создаёт таблицы репозитория и закрывает его. Для `"external"`
контракт остаётся `(connection: object) -> None`.

`database_url` — секретная конфигурация: lowering не логирует её и не
включает в текст исключений.

#### Вид метода `lock`

```text
lock                                -> scope, keys
```

`scope` — непустой строковый литерал, уникальный среди `lock`-методов
репозитория; `keys` — непустой список имён аргументов метода. Метод
захватывает транзакционную эксклюзивную блокировку на кортеж
`(scope, keys...)` и держит её до конца активной транзакции. Блокировка
существует до строки: она применима к ключу, которого ещё нет в таблице.
Lowering в PostgreSQL — `pg_advisory_xact_lock` над детерминированным хешем
кортежа; в SQLite — перевод транзакции в режим немедленной записи. Метод
обязан иметь контракт `(self, <keys...>) -> None`. `lock` не принимает
`table`, `filter` или `select`: условие «какую строку читать после
блокировки» принадлежит следующему методу.

#### Bind-ы фильтра

К `argument` и `constant` версия 3 добавляет:

- `argument_set` — ровно `bind`, `column`, `argument`; аргумент метода имеет
  тип `tuple[<scalar>, ...]`, lowering — `column IN (...)` с одним
  плейсхолдером на элемент; пустой кортеж даёт пустой результат без запроса;
- `optional_argument` — ровно `bind`, `column`, `argument`; аргумент метода
  имеет тип `<scalar> | None`; при `None` условие опускается целиком.

Метод `get_unique` с `optional_argument` обязан объявить `on_multiple`, как и
без него: опущенное условие не делает выборку уникальной.

#### Формы хранения для вложенных значений

К формам `storage` версии 2 добавляются две, нужные персистируемым моделям с
вложенными значениями:

- `json_model` — ровно одна вложенная record-модель; `element_model`
  обязателен и называет её. Lowering — JSON-объект, кодек — сериализация
  модели (`model_dump(mode="json")` / `model_validate`); вложенные
  коллекции и модели внутри неё не перечисляются в IR;
- `json_value` — JSON-значение без модели: кортеж скаляров или
  `dict[str, object]`; `element_model` равен `null`. Кодек — `json.dumps` /
  `json.loads`; модель-владелец приводит список к кортежу сама.

Форма `json` по-прежнему означает список record-моделей. Все три формы
хранятся как TEXT; движок не меняет их кодек.

#### Ключи внутри вложенных значений

Персистируемая модель может нести ключ поиска внутри `json_model`-поля
(например, `card_revision.invoice_id`). Версия 3 адресует его, не раскрывая
вложенную модель в колонки:

- терм фильтра с bind `argument`, `optional_argument` или `argument_set`
  может нести ячейку `path` — непустой список имён полей вложенной модели;
  `column` при этом обязана иметь storage `json_model`, и путь обязан
  резолвиться в скалярное поле вложенной модели. Lowering —
  `column::jsonb #>> '{path}'` (PostgreSQL) или `json_extract` (SQLite);
- элемент `unique` может быть объектом ровно из `column` и `path` с теми же
  правилами; такая группа lower-ится в уникальный индекс по выражению, а не
  в табличный constraint. `primary_key` остаётся списком колонок.

#### Дополнительные виды запросов

```text
upsert_many                         -> table, columns, conflict, updates
list_all                            -> table, select, order_by
```

`upsert_many` — `upsert` над аргументом-коллекцией моделей; пустая коллекция
не выполняет запрос. `list_all` — единственный вид без `filter`: он
объявляет чтение всей таблицы явно, поэтому `order_by` обязателен.

#### Что остаётся вне v3

Условные записи («переиспользовать только эквивалентную запись», «разрешить
только этот переход состояния») по-прежнему не являются storage shape.
Репозиторий выдаёт `get_*`, `list_*`, `insert*`, `update_*`, `upsert`;
решение принимает сервис под `lock`. Метод с таким требованием на границе
репозитория остаётся irregular, и весь его module уходит на LLM-path.

---

### 6.4 `holded_transport_backend/v1`

`rules.holded_transport_backend` — нормативный закрытый IR для конкретного
HTTP-клиента Holded Invoicing V1 purchase documents. Версия 1 поддерживает
только emitter `python_httpx_holded_purchase_v1`: один POST create, один GET
полного списка для recovery и один GET точного документа. Пагинационный,
повторный или repair-цикл в transport lowering отсутствует.

IR обязан фиксировать `wiring`, точные HTTP method/path, имя credential header,
TLS/redirect/retry policy, отображение полей payload/item и отображение полей
трёх response shapes. Runtime credential берётся из `config`; секретное
значение не входит в IR. Origin и wire contract берутся из принятого
экспериментального evidence, а не угадываются по SDK, V2 API или prose.

Closure считается пригодным для deterministic emission только когда
`70_holded_transport_closure.json` имеет статус `closed`, а его `backend_ir`
дословно равен `rules.holded_transport_backend` в assembled spec. Любое
неизвестное поле, другое значение protocol/payload/response registry или
неполное покрытие concrete contracts останавливает генерацию fail-closed;
fallback к LLM запрещён.

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
    },
    "module_internal": {
      "upload_handler": {
        "models": ["RecognitionResult"],
        "preprocessor": ["preprocess"]
      }
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
- `module_internal` — явный граф зависимостей: consumer → provider → список
  импортируемых символов. Имена consumer/provider — логические ключи из
  `module_functions`; каждый символ обязан принадлежать provider. Эта запись
  имеет приоритет над эвристическим выводом зависимости из сигнатур и notes
- `module_internal[consumer][provider]` содержит **минимальный прямой runtime
  import surface** consumer-модуля, а не копию публичного API provider-а.
  Добавляй символ только если consumer обязан импортировать его для своих
  contracts, classified notes или иного явно объявленного
  module-local поведения. Само наличие символа в `models`,
  `imports.internal` или `module_functions[provider]` зависимостью не является
- Для provider-а `models` перечисляй только модели, enum и interface, которые
  consumer непосредственно называет/конструирует/проверяет в своём runtime
  коде. Типы полей выбранной модели, variants discriminated union и другие
  транзитивные model-ссылки расширяют model-context локального прохода, но не
  добавляются в Python-import consumer-а, пока consumer не обращается к ним
  непосредственно
- Запрещено заполнять `module_internal` широким переносом всего
  `imports.internal[provider]`, всего реестра `models` или wildcard-семантикой
  «может понадобиться». Явная запись имеет приоритет над inference, поэтому
  лишний символ реально раздувает dependency graph, affected-set и prompt
  context; это ошибка спеки, а не безвредная избыточность
- Если consumer не импортирует ни одного символа provider-а, ребро provider-а
  отсутствует целиком. Facade/router также перечисляет только реально
  используемые символы, даже если по замыслу имеет доступ ко многим операциям
- Полные import-строки — авторская форма записи. Нормализация разбирает их
  один раз в структурную форму (module, symbol, alias); все последующие
  инструменты (resolver, validator, inspector, slicing, generator) работают
  только по структурной таблице, а не по regex-разбору Python-текста
- `stdlib_by_module` и `third_party_by_module` — module → список полных import
  строк, необходимых конкретному модулю. Для записи в этих таблицах projector
  обязан перенести import в local spec без поиска имени библиотеки в notes или
  contracts. Глобальные `stdlib`/`third_party` остаются каталогом допустимых
  imports; module-scoped таблицы являются структурным доказательством
  необходимости. Не объявленный там module import может быть сужен только по
  связанному импортом symbol/type, но не по совпадению сырого текста import
  statement с prose

**`internal` и `module_internal` отвечают на разные вопросы:**
- `internal` определяет полный публичный export surface provider-модуля
- `module_internal` определяет минимальный прямой import surface каждого
  consumer-модуля
- локальный model-context может быть транзитивно шире прямого runtime-import,
  но не должен превращать этот context closure в новые dependency edges

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
- Класс неделим при назначении модулю: методы следуют за классом. Если один
  метод не принят deterministic backend-ом, весь владеющий persistence module
  (`schema_function` плюс одна repository class) остаётся на LLM-path.
  Частичное смешивание и companion-делегирование для членов типа запрещены.
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

## 10. module_paths

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

## 11. default_module

**Что это:** имя модуля, в который попадают неопределённые функции.

```json
{
  "default_module": "app"
}
```

**Правила:**
- Строка с именем модуля
- Если секция отсутствует — дефолтится к `"app"`
- Модуль с этим именем должен существовать в `module_functions`
- Сюда попадают функции из `contracts` без записи в `module_functions`.
- Для notes `default_module` не применяется: неизвестный или отсутствующий
  префикс является ошибкой нормализации.

---

## 12. Система типов и происхождение имён

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

## 13. properties

**Что это:** исполняемые инварианты функции. Ключ — точное имя из
`contracts`, значение — непустой список строковых булевых выражений.

```json
{
  "properties": {
    "normalize_loads": [
      "all(0 <= load.uncertainty <= 1 for load in result)",
      "len(project.loads) > 0 implies len(result) > 0"
    ],
    "BoardDesignResult.to_summary": [
      "result.design_id == self.design_id"
    ]
  }
}
```

Нормативное подмножество выражений замкнуто:

- корневые имена: `result`, аргументы контракта и `self` для метода;
- литералы `str`, `int`, `float`, `bool`, `None`, коллекционные литералы;
- чтение атрибутов и элементов, сравнения, `in` / `not in`, булевы и
  арифметические операции;
- comprehensions/generator expressions с локально связанными именами;
- чистые builtins `abs`, `sum`, `len`, `all`, `any`, `range`, `min`, `max`,
  `str`; чистые строковые проверки `startswith`, `endswith`, `lower`, `upper`;
- одна верхнеуровневая форма `A implies B`, эквивалентная `not A or B`.

Выражение обязано возвращать `bool` и не должно выполнять import, assignment,
I/O, mutation, вызов проектной функции, доступ к clock/random/global state или
вычисление через undeclared helper. `properties` описывает наблюдаемое
отношение входов и результата, а не алгоритм реализации.

**Правила:**

- функция обязана существовать в `contracts`;
- пустой список запрещён: удали ключ, если properties нет;
- имена аргументов должны точно совпадать с контрактом;
- property должно быть истинно для всех допустимых входов; предусловие пиши
  через `implies`, а не скрывай внутри тестовой fixture;
- правило, требующее побочного эффекта, exception/transaction observation,
  внешнего состояния или интеграции, остаётся classified note;
- таблицы переходов, allow-lists и policy values остаются в `rules`.

---

## 14. determinism

**Что это:** явное требование повторяемости функции при одинаковых аргументах
и одинаковом допустимом состоянии `self`.

```json
{
  "determinism": {
    "normalize_loads": true,
    "BoardDesignResult.to_summary": true
  }
}
```

Ключ обязан существовать в `contracts`, значение обязано быть JSON boolean.
`true` запрещает зависимость результата от clock, random, uuid, secrets,
порядка hash-контейнеров и иного скрытого недетерминированного состояния.
Если порядок результата значим, закрепи его отдельной property или note класса
`[DETERMINISM_OR_ORDERING]`.

`false` означает, что недетерминизм является осознанной частью контракта, а не
«не проверено». Не добавляй записи для функций, по которым решение ещё не
принято. `determinism` не заменяет properties: повторяемый `return []` остаётся
детерминированной заглушкой.

---

## 15. Данные: замыкание, размещение, жизненный цикл

**Что это:** правило замыкания значений. Раздел 12 замыкает пространство *типов*;
этот раздел замыкает пространство *значений*. Оба обязательны: спека без
замкнутых значений допускает несколько корректных сборок и не может быть
собрана детерминированно.

Блоки данных эмитируются детерминированным генератором и в контекст модели не
подаются. Значения не участвуют в генерации кода: модель получает только
адрес и тип. Алгоритм не имеет права догадываться. Поэтому каждое состояние,
допущенное в финализированной спеке, формулируется как машинно-проверяемое
условие, а нарушение является ошибкой валидации, а не предупреждением.
Авторские semantic-gates могут требовать вопроса владельцу продукта до
финализации; их результат обязан быть материализован в спеке так, чтобы
валидатор отличал принятое решение от пропущенного вопроса.

При переходе от доменной семантики к детерминированной эмиссии различаются
четыре механизма. Смешивать их запрещено:

1. **derivation** — техническое следствие уже однозначно выводится из
   канонического объявления спеки; нового проектного решения нет;
2. **placement** — продуктовое значение обязано получить ровно один дом по
   процедуре 15.2;
3. **lowering** — одно и то же значение представляется в двух технических
   формах и требуется каноническое преобразование между ними;
4. **legacy recovery** — существующая реализация содержит решение, которое
   старая спека не сохранила; код служит только источником обнаружения
   semantic gap, но не источником нормы.

Отсутствие отдельной ячейки допустимо только для `derivation`: компилятор
обязан уметь доказать результат из уже объявленных данных и версии backend.
Во всех остальных случаях отсутствие решения является недоспецификацией, а
не разрешением эмиттеру выбрать наиболее правдоподобный вариант.

---

### 15.1 Границы данных спеки

Спека содержит **только значения времени сборки**. Значение принадлежит спеке
тогда и только тогда, когда оно известно до запуска приложения и не зависит от
действий пользователя.

**Правила:**

- Экземпляры доменных сущностей в спеке не хранятся. Площадь помещения, имя
  контрагента, номинал конкретного аппарата, дата замера — это runtime-данные;
  в спеке у них есть только поле в `models`.
- Иллюстративное значение запрещено. Пример в note (`например, 12.5`) при
  генерации превращается в дефолт или в literal внутри кода. Если значение
  нужно как дефолт — оно объявляется дефолтом в `config` или в типе поля; если
  не нужно — его не должно быть в спеке.
- Значение, порождаемое внешней системой (remote id, номер документа,
  выданный провайдером, токен), в спеку не попадает никогда, включая примеры
  формата.

#### 15.1.1 Замыкание доменной идентичности

До назначения `persistence.class` каждая runtime-модель обязана явно объявить
семантику идентичности. Это правило применяется **ко всем моделям с
отсутствующим `kind`**. Отсутствие решения не означает default: это
недоспецифицированная модель и BLOCK до генерации.

Объявление модели содержит обязательное поле:

```json
"Money": {
  "identity": "value",
  "fields": {
    "amount": "Decimal",
    "currency": "Currency"
  }
},
"Invoice": {
  "identity": "entity",
  "fields": {
    "id": "InvoiceId",
    "total": "Money"
  }
}
```

Закрытый реестр:

| `identity` | Значение |
| --- | --- |
| `value` | экземпляр определяется своими значениями; замена на равный экземпляр предметно незаметна |
| `entity` | экземпляр имеет непрерывную идентичность, сохраняемую через изменения состояния |

Поле `identity` отсутствует только у моделей с `kind`; для модели с
отсутствующим `kind` отсутствие, неизвестное значение или попытка объявить
`UNRESOLVED` делает спеку невалидной. `UNRESOLVED` существует только как
авторский исход до финализации спеки: писатель обязан запросить продуктовое
решение и не имеет права материализовать недоопределённость в валидной спеке.

Автор до валидации применяет два парных теста:

1. **Тест подстановки.** Если экземпляр заменить другим экземпляром с полностью
   равными значениями полей, должен ли продукт считать, что предметно ничего
   не изменилось? Если да — кандидат на `value`.
2. **Тест непрерывности.** Может ли экземпляр остаться тем же предметным
   объектом после изменения всех или большинства его атрибутов? Если да —
   кандидат на `entity`.

Если тесты не дают однозначного результата из продуктовых требований, это
semantic gap. Писатель обязан остановиться и запросить решение; техническая
форма хранения не может использоваться как ответ.

**Правила (нарушение = невалидная спека):**

- Запрещено выводить `identity: entity` из наличия таблицы, ORM, `id`, UUID,
  persistence или CRUD. Техническая форма хранения не определяет предметную
  идентичность.
- Запрещено добавлять `id` «на будущее» или потому, что у записей обычно есть
  идентификатор. Стабильная идентичность допустима только когда её требует
  продуктовая семантика либо внешний владелец данных.
- Запрещено считать составное значение entity только потому, что оно
  представлено отдельной моделью. `Money`, `Quantity`, `Dimensions`,
  `Address` и аналогичные типы могут иметь `identity: value`.
- Если понятие является лишь производным представлением другого факта
  (например, число упаковок как функция требуемого количества и размера
  упаковки), не создавай отдельную entity без требования продукта
  отслеживать такие экземпляры независимо.
- Для `identity: entity` писатель обязан определить, чем сохраняется
  идентичность экземпляра через изменения состояния.
- Для `identity: value` состояние полностью определяется значениями полей.
  Такой экземпляр не имеет самостоятельного mutable lifecycle. Если его нужно
  независимо адресовать, мутировать, синхронизировать или вести его историю,
  объявление `value` недействительно: семантика объявляется `entity` либо
  автор возвращается в состояние `UNRESOLVED` до финализации спеки.
- Решение об `identity` принимается **до** назначения `persistence.class`.
  `identity` отвечает на вопрос «что делает экземпляр именно этим
  экземпляром», а `persistence.class` — «как живут экземпляры». Оси различны,
  но совместимость между ними проверяется валидатором.

#### Совместимость `identity` и `persistence.class`

| `identity` | `persistence.class` | Допустимость |
| --- | --- | --- |
| `value` | отсутствует (`derived` по умолчанию) | да |
| `value` | отдельная самостоятельная persisted-запись с собственным идентификатором | нет |
| `value` | embedded/snapshot как поле entity или `issued`-документа | да |
| `entity` | `master` | да |
| `entity` | `derived` | да, если экземпляр выводим, но его идентичность определена доменом |
| `entity` | `issued` | да |
| `entity` | `mirrored` | да |
| `value` | `mirrored` | нет: внешний владелец задаёт непрерывную идентичность |

При `persistence.class = mirrored` модель обязана иметь `identity: entity`.
При `identity: value` компилятор не создаёт самостоятельное хранилище с
собственным идентификатором; значение может быть embedded, частью snapshot или
получаться как derived.

**Пример semantic gap:**

Требование «приложение считает коробки саморезов» недостаточно для объявления
`ScrewBox`.

- Если коробка означает только закупочное представление
  `ceil(required_quantity / pack_size)`, отдельная runtime-entity не нужна.
- Если продукт обязан различать конкретные физические коробки, их остаток,
  местоположение или историю, модель имеет `identity: entity` со стабильной
  идентичностью.
- Если требование не говорит, какой из двух смыслов нужен, писатель обязан
  остановиться и запросить решение до появления модели в валидной спеке.

---

### 15.2 Тотальная процедура размещения

Каждое значение спеки имеет **ровно один дом**. Дом определяется процедурой
ниже. Проверки упорядочены, выигрывает первое совпадение. Процедура тотальна:
значение, не разместившееся ни в один дом, — дефект спеки, а не повод для
свободной прозы.

| # | Проверка | Дом |
| --- | --- | --- |
| 0 | Это форма (набор полей, их типы, закрытый список вариантов), а не значение | `models` |
| 1 | Значением владеет внешняя система | не хранится; см. 15.5, класс `mirrored` |
| 2 | Значение вводит пользователь во время работы приложения | не хранится; см. 15.1 |
| 3 | Значение меняется при смене окружения или деплоя | `config` |
| 4 | Значение меняется по продуктовому, нормативному или коммерческому решению | `rules` |
| 5 | Значение — закрытая доменная таксономия | `models` с `kind: enum`, `catalog`, `mapping`, `vocabulary` |

**Различение 4 и 5 — операциональное, не тематическое.** Если добавление нового
значения требует изменения кода, это таксономия (`models`). Если существующий
код продолжает работать без изменений, это политика (`rules`). Форма данных
критерием не является: две таблицы одинаковой формы могут иметь разные дома.

**Различение 3 и 4:** `config` меняется без решения о продукте (порог нагрузки
на инфраструктуру, таймаут, путь). `rules` требует чьего-то решения и, как
правило, имеет дату вступления в силу.

---

### 15.3 Адресация и дереференсируемость

Note обращается к данным **только адресом**. Воспроизведение содержимого блока
данных внутри note запрещено (см. §2).

**Правила (нарушение = невалидная спека):**

- Каждая ссылка вида `= config.*`, `= models.*`, `= rules.*` обязана
  резолвиться в существующий узел. Неразрешённая ссылка — ошибка валидации.
- Ссылка указывает на **наименьший узел, который потребитель использует
  целиком**. Ссылка на родителя при использовании одного листа запрещена:
  она расширяет affected-set при изменении соседних листьев.
- Каждый лист блока данных обязан быть достижим хотя бы одной ссылкой из
  `notes`, `properties` или другого блока данных. Недостижимый лист — мёртвые
  данные и ошибка спеки, а не безвредный остаток.
- Таблицу достижимости строит тот же resolver, что и таблицу происхождения
  типов (§12). Отдельные проектные списки известных ключей запрещены.

---

### 15.4 Каноническая форма блоков данных

Блоки данных эмитируются алгоритмом, поэтому их представление обязано быть
каноническим: две сборки из одного входа дают побайтово одинаковый блок. Это
единственная часть проекта, воспроизводимая точно, и она служит опорой при
диагностике: расхождение между двумя сборками локализуется в генерации кода, а
не в данных.

**Правила:**

- Ключи объектов сериализуются в отсортированном порядке. Порядок ключей
  семантики не несёт.
- Значение фиксированной точности записывается строкой (`"21.00"`), не числом
  с плавающей точкой. Тип восстанавливается при эмиссии по объявленному типу
  поля.
- Каждая строка табличных данных имеет **стабильный идентификатор**,
  объявленный в самих данных. Позиция в массиве идентификатором не является:
  пересборка блока переставляет строки и разрывает ссылки на них из уже
  записанных runtime-данных.
- Вычисляемые значения в блоках запрещены: никаких выражений, шаблонов,
  подстановок и ссылок одного листа на другой. Производное значение
  вычисляется кодом, а не собирается склейкой блоков.
- Дублирование листа в двух домах запрещено. Совпадение значений в разных
  домах допустимо только как случайное; если значения обязаны совпадать, у них
  один дом и одна ссылка.

---

### 15.5 persistence: класс данных

**Что это:** объявление того, как живут экземпляры модели. Ключ — имя
объявленной модели, значение — объект с обязательным полем `class`.

```json
{
  "persistence": {
    "PriceCatalogItem": { "class": "master" },
    "Estimate":         { "class": "issued" },
    "EstimateLine":     { "class": "issued" },
    "RemoteInvoice":    { "class": "mirrored", "remote": "holded" }
  }
}
```

**Реестр классов закрыт:**

| `class` | Значение | Следствия эмиссии |
| --- | --- | --- |
| `master` | источник истины, мутабельный | обычная таблица, история по 15.6 |
| `derived` | производное, пересчитываемое | таблица не создаётся; хранение только как кэш с объявленным ключом инвалидации |
| `issued` | выпущенный документ, снапшот | append-only; `UPDATE` и `DELETE` запрещены; исправление вносится новой записью со ссылкой на исходную; модель эмитится immutable |
| `mirrored` | владелец — внешняя система | локально read-only; обязательны `remote_id` и `synced_at`; расхождение разрешается в пользу remote; поле `remote` обязательно |

**Правила (нарушение = невалидная спека):**

- Запись допустима только для модели с **отсутствующим `kind`**. `enum`,
  `discriminated_union`, `interface` не имеют персистируемых экземпляров;
  `catalog`, `mapping`, `vocabulary` — данные времени сборки, вне оси
  персистентности.
- Отсутствие записи означает `derived`. Перечислять все модели не требуется.
- `issued` обязан хранить значения, а не ссылки на `master` и `rules`.
  Нормализация выпущенного документа запрещена: изменение каталога или политики
  не должно изменять уже выпущенный документ. Это единственное место, где
  дублирование значения предписано, а не запрещено.
- Модель класса `mirrored` не участвует в расчётах: факт, которым владеет
  внешняя система, не выводится из локального состояния, а читается из
  подтверждённого ответа.
- Взаимодействие с внешней системой отделяется переводящим слоем
  (anti-corruption layer): DTO внешнего API не проникает в доменные модели.
  Состояние обмена — явная модель состояний, не булев флаг; повторяемый вызов
  снабжается idempotency key, выводимым из содержимого.

#### 15.5.1 Storage projection и замыкание кодека

Persistence не вводит вторую модель предметной области. Схема хранения является
детерминированной проекцией `models` плюс явно объявленных storage-решений.

**Выводимые ограничения не повторяются в persistence-данных.** Если ограничение
однозначно следует из поля модели и выбранного backend, эмиттер обязан вывести
его сам. В частности, nullable/non-nullable semantics не назначается повторно
при эмиссии: обязательность поля берётся из его объявления в `models`.
Backend-specific ограничения, являющиеся однозначным следствием модели и версии
backend, также принадлежат компилятору, а не проектной спеке.

Расхождение между доменной формой и выводимой storage-схемой является дефектом
компилятора/эмиттера. Оно не исправляется дополнительной note и не создаёт
новую проектную ячейку только ради проверки постфактум.

Для каждого персистируемого поля, чьё runtime-представление отличается от
представления хранения, преобразование обязано замыкаться парой:

```text
(domain type, storage representation)
    -> ровно один канонический codec backend-а
```

Storage representation и SQLite affinity — разные уровни. Версия backend-а
объявляет закрытый реестр representations (`text`, `integer`, `real`, `blob`,
а также закрытые codec-backed формы вроде `uuid`, `datetime`, `decimal`,
`enum`, `json`) и детерминированно lower-ит их в SQLite affinities `TEXT`,
`NUMERIC`, `INTEGER`, `REAL`, `BLOB`. `NULL` является storage class, не
affinity; nullable semantics берётся только из типа model field.

Реестр и допустимые пары не содержат проектных имён. Проект выбирает только из
разрешённых для domain type representations; если выбор единственный, он
выводится и не дублируется.

**Правила (нарушение = невалидная спека или DEFECT backend-а):**

- Допустимые storage representations образуют закрытый реестр конкретного
  deterministic backend-а. Свободная строка, содержащая выражение
  encode/decode, SQL или фрагмент кода, запрещена.
- Если для одного domain type backend допускает несколько storage
  representations, проектная спека обязана явно выбрать одну из закрытого
  словаря. Если выбор единственный, он является `derivation` и в проекте не
  дублируется.
- Для каждой допустимой пары `(domain type, storage representation)` backend
  определяет ровно один канонический encode/decode codec. Проектный генератор
  не выбирает имя, алгоритм или формат кодека.
- Имена внутренних codec/helper-функций принадлежат backend-эмиттеру,
  детерминированы его версией и не являются проектными символами:
  они не добавляются в `contracts`, `module_functions` или notes.
- Ручной проектный кодек внутри детерминированно эмитируемого persistence-модуля
  запрещён. Неподдерживаемая пара типов является `DEFECT`, а не поводом
  сгенерировать `_parse_*`, `_row_to_*` или аналогичный helper по догадке.
- Codec выполняет только представительное преобразование. Продуктовая
  нормализация, default, fallback, фильтрация и изменение смысла значения не
  являются codec-операциями и обязаны иметь владельца в `models`, `rules`,
  `config`, properties или поведении функции.
- Два repository-модуля, хранящие одну и ту же пару domain/storage типов,
  не могут иметь разные форматы преобразования. Различие означает либо другую
  явно объявленную storage representation, либо дефект.

#### 15.5.2 Область codec coverage

Равенство codec машинно обеспечивается только для модулей, целиком принятых
deterministic persistence backend. LLM-module не получает это утверждение по
умолчанию и не компенсирует разрыв classified note.

Если LLM-module и deterministic module используют хотя бы одну общую пару
`(domain type, storage representation)`, валидатор выдаёт отдельную
неблокирующую диагностику `codec_coverage_gap`. Она перечисляет обе стороны и
каждую общую пару. Диагностика не блокирует сборку, но делает состояние
`codec_coverage=complete` ложным и обязана попасть в lineage/OTK evidence.
Пары вычисляются из validated v2 table projection, не из существующего или
сгенерированного Python-кода. При отсутствии общих пар gap не возникает.

---

### 15.6 Действие во времени

Значение, изменяемое по решению и влияющее на уже выпущенные документы, имеет
период действия. Перезапись такого значения уничтожает историю и делает
пересчёт прошлого документа невоспроизводимым.

**Правила:**

- Для `master`-модели, значения которой цитируются в `issued`, объявляется
  период действия (`valid_from`, `valid_to`), а изменение выполняется вставкой
  новой строки, а не `UPDATE`.
- Расчёт, порождающий `issued`, обязан фиксировать момент, на который выбраны
  значения. Момент хранится в документе.
- Политика в `rules`, имеющая дату вступления в силу, объявляет её явно; note
  ссылается на политику адресно и не воспроизводит дату.

---

### 15.7 Версионирование и миграция

Код регенерируется, данные — нет. Поэтому форма данных версионируется
независимо от кода.

**Правила:**

- `schema_version` — целое, обязательно на верхнем уровне `config`, `models` и
  `rules`.
- Совместимое изменение: добавление поля с дефолтом, добавление значения в
  `rules`, добавление строки в каталог. Версия не повышается.
- Несовместимое изменение: удаление или переименование обязательного поля,
  изменение типа, удаление значения из закрытой таксономии, изменение
  стабильного идентификатора строки. Требует повышения `schema_version`.
- Несовместимое изменение объявляет переход как последовательность обратимых
  фаз (expand/contract): добавить новое → писать в оба → перенести → читать из
  нового → удалить старое. Одношаговая миграция запрещена.
- Читатель обязан игнорировать неизвестные поля, а не отказывать. При
  сосуществовании двух генераций кода forward-совместимость обязательна
  наравне с backward.

#### 15.7.1 Legacy recovery потерянных решений

При миграции старой спеки анализ `notes` недостаточен: прежняя генерация могла
вкомпилировать значения, predicates, ordering, storage conventions или иные
решения непосредственно в код.

Существующий код и тесты разрешено использовать как **зонд обнаружения**:
наблюдаемое решение сравнивается с текущей спекой. Если нормативного владельца
нет, фиксируется semantic gap и миграция обязана вернуть решение в правильный
дом или явно удалить его как случайную деталь реализации.

**Правила:**

- Existing code не является источником истины для новой спеки и не переносится
  автоматически в `rules`, `config`, `models` или persistence-данные.
- Найденный literal/predicate/ordering/convention без владельца в спеке является
  кандидатом на потерянное решение, а не доказательством его нормативности.
- Продуктовое значение, подтверждённое владельцем решения, размещается обычной
  процедурой 15.2; для него не создаётся специальный legacy-дом.
- Реализационная деталь, полностью выводимая из новой модели/backend, относится
  к `derivation` и в спеку не переносится.
- Миграция считается неполной, пока probe обнаруживает семантически значимые
  решения, которые новая спека не может ни вывести, ни адресовать.

---

### 15.8 Числовая точность

- Денежные и расчётные величины, требующие точности, представляются
  фиксированной точкой. `float` для них запрещён. Тип связывается полной
  import-строкой (§12, п. 3).
- Политика округления (шаг, направление, уровень применения — строка или итог)
  объявляется в `rules` и адресуется note. Округление, не описанное политикой,
  является недоспецифицированным поведением.
- Распределение суммы по позициям объявляет судьбу остатка от округления.
  Сумма частей обязана равняться целому; правило закрепляется в
  `properties`.

---

### 15.9 Контракт шва: данные и код

Блоки данных и код модулей порождаются двумя независимыми генераторами,
пишущими в один проект. Шов между ними описывается явно, иначе сборка
недетерминирована по составу файлов.

**Правила (нарушение = невалидная спека или дефект сборки):**

- **Эксклюзивное владение файлом.** Каждый файл проекта порождается ровно
  одним генератором. Файл, эмитируемый генератором данных, не редактируется
  моделью ни целиком, ни частично. Смешанное владение внутри файла запрещено.
- **Модель не видит значений.** В контекст модуля подаётся сигнатура доступа —
  имя модуля-носителя, имя символа и его тип, — но не значение. Блок данных
  является обычным provider-модулем; доступ к нему объявляется ребром
  `module_internal` наравне с любой другой зависимостью (§7).
- **Literal-check.** Значение, объявленное в блоке данных, не должно
  встречаться литералом в коде модуля-потребителя. При эмиссии мимо модели это
  инвариант по построению; проверка сохраняется как ассерт сборки и ловит
  протечку значения через notes.
- **Соответствие значений форме** проверяется валидатором спеки до эмиссии, а
  не эмиттером: значение, не соответствующее объявленному типу поля или
  выходящее за закрытый список, — дефект спеки.
- **Одно объявление для выводимой схемы.** Ограничения storage-схемы,
  однозначно следующие из `models` и версии deterministic backend-а, не
  объявляются повторно при эмиссии. Доменная модель и storage-проекция
  порождаются из одного канонического объявления; расхождение между ними
  невозможно по построению и является дефектом эмиттера, а не вторым
  проектным решением.
- **Fail-closed на обеих сторонах.** Неразмещённое значение останавливает
  сборку. Подстановка значения в контекст модели «на всякий случай»
  запрещена: она молча восстанавливает старое поведение и обесценивает шов.

---

### 15.10 Протокол отказа генератора данных

Генератор различает два исхода, и смешивать их запрещено.

| Исход | Условие | Действие |
| --- | --- | --- |
| `NOT_APPLICABLE` | процедура 15.2 отработала и не нашла ни одного размещаемого значения | генератор не эмитит файлов, сборка продолжается |
| `DEFECT` | процедура отработала и обнаружила нарушение | сборка останавливается |

`NOT_APPLICABLE` допустим только как результат выполненной процедуры.
Пропуск процедуры, отсутствие секций данных или ошибка чтения спеки —
`DEFECT`, а не «нечего размещать».

**Неоднозначность не разрешается статистикой.** Эмиттер, мигратор и probe не
имеют права выбирать вариант по частоте его употребления в существующем коде.
Большинство, наиболее свежая реализация и повторяемость конвенции не обладают
нормативной силой. Если несколько наблюдаемых реализаций расходятся, а стандарт
или спека не задают единственный результат, это `DEFECT` класса
`convention_mismatch` / semantic gap. Решение принимает владелец продукта либо
новая явная норма стандарта; алгоритм не голосует.

**Классы дефектов различаются в диагностике:**

- значение не разместилось ни в один дом (15.2) — недоспецифицированное
  значение;
- ссылка не резолвится (15.3) — висящий адрес;
- лист недостижим ссылкой (15.3) — мёртвые данные; диагностика обязана
  различать потерянную note и лишний лист, поскольку исправления
  противоположны;
- значение не соответствует объявленной форме (15.9) — рассогласование
  формы и значения;
- нарушена каноническая форма (15.4) — невоспроизводимый блок.
- отсутствует или неоднозначен codec для пары domain/storage типов (15.5.1) —
  незамкнутый lowering;
- несколько legacy-реализаций расходятся без нормативного владельца (15.7.1,
  15.10) — `convention_mismatch`, а не основание выбрать большинство.

---

### 15.11 Нормативный NOT-list данных

Следующее в язык данных не входит; обход через notes или нестандартные ключи
делает спеку невалидной:

- runtime-экземпляры и иллюстративные значения в любом блоке
- runtime-модель с отсутствующим или недопустимым `identity`; `UNRESOLVED`
  не является значением DSL и не может появляться в финализированной спеке
- угадывание `identity` по форме хранения, наличию `id`, CRUD или ORM
- inline-данные в notes: таблицы, пороги, allow-list, alias-словари, пути,
  ставки, коэффициенты
- вычисляемые значения, шаблоны и внутриблочные ссылки
- позиционная идентификация строк табличных данных
- `float` для величин фиксированной точности
- нормализация `issued`-документов ссылками на изменяемые источники
- одношаговая несовместимая миграция
- ручные encode/decode codec-фрагменты и свободные storage-конвертеры внутри
  deterministic persistence emission
- compiler-generated codec/helper symbols, материализованные как проектные
  `contracts`, `module_functions` или notes
- перенос наблюдаемой legacy-конвенции в новую спеку только потому, что она
  встречается чаще остальных
- расширение или отказ от расширения backend IR по частоте случая в текущем
  корпусе; критерий — замкнутость относительно уже разрешённых форм
- строковый микро-синтаксис и вложенный `ref` внутри backend IR
- последовательность операций как значение спеки
- перенос `irregular_ownership` за пределы router registry
- проектные имена как элементы реестра конструкций backend-а
- подача значений в контекст генерации кода
- смешанное владение файлом между генератором данных и моделью
- `NOT_APPLICABLE` как результат невыполненной процедуры размещения
- секции данных, не предусмотренные этим стандартом

---

## Чек-лист перед запуском сборки

0. **Запусти валидатор:** `python validate_spec.py global_spec.json` — он проверит всё из этого списка автоматически.

1. **Каждая функция в contracts?** Проверь что нет функций без сигнатуры.

2. **Каждая функция в module_functions?** Проверь что ничего не потерялось.

3. **Notes с префиксами и классами?** Каждая новая note начинается с `"function_name: [NOTE_CLASS]"` или `"ClassName.method_name: [NOTE_CLASS]"`.

4. **Нет неоднозначных имён?** `__init__`, `to_dict`, `close` — всегда с классом: `"Database.__init__:"`.

5. **Стыки вызовов описаны?** Несовпадение форм аргументов зафиксировано
   classified note у caller; секции `adapters` в спеке нет.

6. **Импортная поверхность точная?** `imports.internal` содержит полный
   публичный API provider-ов, а каждый `module_internal` — только прямые
   runtime-импорты конкретного consumer-а; нет переноса всего provider API или
   всего реестра `models`.

7. **config/models/rules разведены?** Runtime knobs лежат в `config`, domain schemas/catalogs в `models`, policy tables в `rules`; inline-данные не остаются в notes.

8. **models описаны?** Все dataclass'ы с полями и типами.

9. **module_order корректный?** Зависимости идут раньше зависимых. `models` всегда первый; `rules`/`config` доступны до модулей, которые на них ссылаются.

10. **Каждая note имеет точный адрес?** Разрешены только `function_name:`,
    `ClassName.method_name:` и `module_name:`; ноты без префикса и эвристическая
    маршрутизация запрещены.

11. **module_paths заполнены?** Если проект не плоский — укажи пути для каждого модуля.

12. **Типы замкнуты?** Каждое имя в type position — builtin, объявленная модель или символ, связанный полной import-строкой; коллизий происхождения нет (раздел 12).

13. **Порты полны?** Каждый экспортируемый `kind: interface` имеет полные method contracts; у каждого `discriminated_union` — discriminator, закрытые variants и `Literal`-теги.

13a. **Реализации портов приземлены?** Каждый interface-typed dependency имеет
     `implementation_obligations`; у `local` concrete contracts полностью и
     сигнатурно покрывают port, а модуль-владелец имеет зарегистрированный
     deterministic backend; `external` не маскирует локальную заглушку.

14. **Инварианты приземлены?** Каждый State 2 invariant имеет одного
владельца и первичное представление в `rules`, classified note или
`properties.<function>`; подходящие чистые функции отмечены в `determinism`.

15. **Доменная идентичность замкнута?** Каждая модель без `kind` явно имеет
    `identity: value|entity`; отсутствие поля — BLOCK. `UNRESOLVED` отсутствует
    в финальной спеке; `id`/CRUD/persistence не использованы как замена
    продуктового решения; совместимость `identity` × `persistence` валидна.

16. **Каждое значение размещено процедурой 15.2?** Нет значений, оставшихся в
    notes прозой; нет значений без дома.

17. **Все ссылки резолвятся, все листья достижимы?** Нет мёртвых данных и нет
    висящих адресов.

18. **Блоки канонизированы?** Сортированные ключи, строковая фиксированная
    точка, стабильные идентификаторы строк, отсутствие вычисляемых значений.

19. **Классы персистентности объявлены?** Каждая персистируемая модель имеет
    запись в `persistence`; `issued` хранит снапшот значений; `mirrored` имеет
    `remote_id`, `synced_at` и переводящий слой.

19a. **Persistence IR нормативен?** Если присутствует `persistence_backend`,
     это версия 2 или 3; v1 отсутствует. Aggregate покрыт root/one/many без
     списка шагов, а `codec_coverage_gap` перечисляет разрывы покрытия. В
     версии 3 каждый repository row называет `transaction`, владеющий
     репозиторий объявляет `begin`/`commit`/`rollback` в contracts, а `lock`
     не несёт `table`/`filter`.

20. **Историчность обеспечена?** Значения, цитируемые в `issued`, имеют период
    действия; документ фиксирует момент расчёта.

21. **Версия стандарта проставлена?** `standard_version` равен поддерживаемой
    редакции и перенесён в normalized spec и lineage.

22. **Backend refs листовые?** Нет вложенных ref, объектов внутри ref,
    строкового микро-синтаксиса и неизвестных ref-полей.

21. **Версии и переход объявлены?** `schema_version` присутствует в трёх
    блоках; несовместимое изменение сопровождается фазами expand/contract.

22. **Шов описан?** Каждый эмитируемый файл имеет ровно одного владельца;
    потребители данных объявлены рёбрами `module_internal`; в контекст модели
    не подаётся ни одно значение.

23. **Отказ различим?** `NOT_APPLICABLE` возможен только после выполненной
    процедуры размещения; каждый класс дефекта диагностируется отдельно.

24. **Lowering замкнут?** Для каждой persistence storage projection либо
    доказан единственный вывод из модели/backend, либо выбран допустимый
    storage representation; для каждой domain/storage пары существует ровно
    один backend codec, и проект не содержит ручных codec-helper'ов.

25. **Legacy recovery завершён?** При миграции старой спеки probe существующего
    кода не оставляет значимых literals/predicates/conventions без нормативного
    владельца; расхождения не разрешались голосованием большинством.

---

## Пример минимальной спеки для нового проекта

```json
{
  "standard_version": 2,
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
    "role": "data",
    "schema_version": 1,
    "Item": {
      "identity": "value",
      "fields": {
        "id": "str",
        "name": "str",
        "status": "str",
        "created_at": "str"
      }
    }
  },
  "rules": {
    "role": "data",
    "schema_version": 1
  },
  "persistence": {},
  "properties": {
    "transform": [
      "all(item.status == 'active' for item in result)"
    ]
  },
  "determinism": {
    "transform": true
  },
  "imports": {
    "stdlib": ["json"],
    "third_party": ["import requests"],
    "internal": {
      "models": ["Item"],
      "fetcher": ["fetch_data"],
      "transformer": ["transform"]
    },
    "module_internal": {
      "transformer": {
        "models": ["Item"]
      },
      "saver": {
        "models": ["Item"]
      }
    }
  },
  "module_functions": {
    "models": ["Item"],
    "fetcher": ["fetch_data"],
    "transformer": ["transform"],
    "saver": ["save"]
  },
  "module_order": ["models", "fetcher", "transformer", "saver"],
  "module_paths": {},
  "default_module": "main"
}
```

**Примечания к примеру:**
- `module_paths` — пустой означает плоскую структуру (все файлы в корне)
- `default_module` — `"main"` вместо `"app"`, потому что точка входа в этом проекте называется `main.py`
