# Построение записей как детерминированный backend: `record_construction_backend/v1`

Статус: проект (design), решение владельца об утверждении структуры — 2026-11-08.
Реализации нет. Этот документ ничего не меняет в `tools/`, в стандарте и в кейсах.
Текст раздела стандарта (§7 ниже) — черновик, не применён ни к одной копии.

Связано: #147 (дефекты States 1/2/4/6 всплывают только на сборке),
`examples/client-portal/spec/record_construction_gaps.json` на ветке
`agent/client-portal` (коммит `9ac5ed63`).

---

## 1. Принцип и проблема

**Принцип владельца.** Всё, что можно выпустить детерминированно, выпускается;
проза держит только адреса. Модель спотыкается о структуры данных, потому что
замкнутость и владение в прозе не проверить: то, что сгенерировались 27 модулей,
ничего не доказывает — модель могла угадать. Система эмиттеров фабрики
расширяема намеренно: «Эммитер можно дописать в фабрику, это не проблема».

**Чего не хватает.** Доменные функции строят записи объявленных моделей из
входов. Пример: `expense_intake._build_expense_aggregate` строит `Expense`,
`ExpenseDocument` и список `ExpenseAllocation` из `ExpenseIntake`. Сегодня это
пишет LLM по прозе notes: «same-named field of intake», «the one timestamp the
operation captured», «None, never amended». Route B остановился именно здесь —
на гейте `model_constructor_unknown_field` (`tools/draft_static_gates.py`).

**Прецедент.** У фабрики уже есть две проверяемые формы того же вида знания:

- §6.1 `http_router_backend/v1`: `projections` обязаны **точно** покрывать поля
  модели возвращаемого типа;
- §6.2 `persistence_backend/v2`: все поля aggregate model покрыты root/relations,
  runtime outcome и default literal-ом не добавляются.

Построение доменной записи — тот же вопрос («откуда каждое поле цели и куда
делось каждое поле входа»), но без закрытой формы.

**Данные.** `record_construction_gaps.json` перечисляет 84 места построения,
153 целевые записи, 1080 целевых полей. У каждого поля ровно один источник;
для 32 мест входные модели (43 блока) размечены «потреблено / отброшено с
причиной». Открыто 26 полей: 16 полей трёх декодеров Registry (имена полей на
проводе нигде в кейсе не записаны) и 10 полей в 7 местах, где notes и
работающий код расходятся или источник не назван. (Заголовок файла говорит
«18 wire names + 8 conflicts»; счёт по полям-ячейкам даёт 16 + 10, разница —
в том, считать ли две ячейки `ProjectReference` в двух декодерах одной и
открытые ячейки производных представлений конфликтом. На дизайн это не влияет.)

Этот файл и есть прототип IR: он доказывает, что источник поля можно записать
адресом, а не прозой. Документ превращает его в закрытую форму, проверку
замыкания и эмиттер.

---

## 2. IR: `rules.record_construction_backend`, версия 1

### 2.1 Верхний уровень

```json
{
  "kind": "record_construction_backend",
  "schema_version": 1,
  "backend": {"emitter": "python_record_builders_v1"},
  "wiring": {"module": "record_builders", "models_module": "core.models"},
  "constructions": {
    "<builder_function>": { "...": "строка построения, §2.2" }
  }
}
```

- Ровно эти пять ключей; `backend` равен
  `{"emitter": "python_record_builders_v1"}`; `wiring` содержит ровно `module`
  и `models_module` (`models_module` равен `module_paths.models`).
- `constructions` — непустой объект; ключ — имя функции-построителя
  (builder). Ключ объекта, а не позиция списка: имя — идентификатор (§15.4), и
  так `deterministic_method_scopes` Workbench выводится тем же путём, что у
  рецептов §6.7 (`scope_mapping_path=("constructions",)`).
- Модуль `wiring.module` владеет **ровно** функциями из `constructions` и
  ничем больше (`module_functions[wiring.module]`), как модуль §6.7 владеет
  ровно функциями рецептов.
- Сигнатура построителя — **только** `contracts[<builder_function>]` (как
  §6.1: «единственный источник сигнатуры — `contracts`»). В IR сигнатура не
  повторяется; параметры, их типы и возвращаемый тип читаются из контракта.

### 2.2 Строка построения

```json
"build_expense_aggregate": {
  "form": "construct",
  "target": "ExpenseAggregate",
  "consumers": ["expense_intake"],
  "over": null,
  "element": null,
  "base": null,
  "parts": { "<part_name>": { "...": "строка части, §2.3" } },
  "fields": { "<target_field>": { "ref": "..." } },
  "dropped": {
    "<name>": { "<field>": {"reason": "<reason_code>", "decision": "<id>|null"} }
  }
}
```

| ячейка | смысл |
|---|---|
| `form` | `construct` — новая запись; `replace` — новая запись того же типа на месте входной (неизменяемые модели, `model_immutability_policy`). Вид `project` из файла пробелов — это `construct`, все поля которого из одного входа; отдельной формы не нужно, проверка одна и та же. |
| `target` | объявленная модель (`kind` не `enum`/`interface`/`discriminated_union`). |
| `consumers` | непустой список модулей, которые вызывают построитель. Нужен для проверки рёбер импорта и для гейта обхода (§4.5). |
| `over`, `element` | вместе или оба `null`. `over` — ref на коллекцию (`list[...]`/`tuple[...]`), `element` — имя, под которым элемент виден ссылкам. Тогда построитель возвращает `list[target]`, по одной записи на элемент, в порядке коллекции. |
| `base` | только при `form: replace`: имя параметра типа `target`. Поля, которых нет в `fields`, берутся из `base` без изменения; их не перечисляют. |
| `parts` | вложенные построения (агрегаты), §2.3. |
| `fields` | ровно один источник на поле цели (при `replace` — только изменяемые поля). |
| `dropped` | для каждого *имени модельного типа* (параметр, `element`, связка части) — поля, которые построение сознательно не читает, с кодом причины. |

Потреблённые поля **не перечисляются**: они выводятся из ссылок. Файл пробелов
хранит оба списка; в IR у факта «поле потреблено» один дом — сама ссылка
(§15.4), и замыкание проверяет `потреблённые ∪ отброшенные = поля модели`,
`потреблённые ∩ отброшенные = ∅`.

### 2.3 Части (агрегаты)

Часть — именованное вложенное построение внутри одного построителя:

```json
"parts": {
  "expense":     {"target": "Expense",           "over": null, "element": null, "fields": {"...": {}}},
  "document":    {"target": "ExpenseDocument",   "over": null, "element": null, "fields": {"...": {}}},
  "allocations": {"target": "ExpenseAllocation",
                  "over": {"ref": "field", "of": "intake", "field": "allocations"},
                  "element": "instruction",
                  "fields": {"...": {}}}
}
```

- Строка части содержит ровно `target`, `over`, `element`, `fields`; форма
  части всегда `construct` (замена с частями — отдельная строка построения).
- Части образуют ациклический граф по ссылкам `part`/`part_field`; порядок
  эмиссии — топологический с лексикографическим разрешением ничьих. Порядок не
  является значением спеки (§6.0, «последовательность операций»).
- Поле части с `over` (коллекции) нельзя читать снаружи её области: снаружи
  видна только вся коллекция (`{"ref": "part", "name": "allocations"}`).

### 2.4 Закрытый словарь источников

Каждый источник — листовой `ref` §6.0: значения ячеек — JSON-скаляры или
массивы скаляров, вложенных объектов нет. *Имя* ниже — параметр контракта,
`element` построения или части. Одиннадцать ссылок версии 1:

| `ref` | ячейки | значение | откуда в файле пробелов |
|---|---|---|---|
| `name` | `name` | значение имени целиком | `param` |
| `field` | `of`, `field` | одно поле имени, **один уровень** | `param_field`, `result Model.field` над входом |
| `part` | `name` | вся запись (или коллекция) части | `result Model` |
| `part_field` | `part`, `field` | поле одиночной части | `result Expense.expense_id` |
| `call` | `function`, `args` | результат объявленного контракта; `args` — массив *имён* | `result <функция>` |
| `clock` | — | мгновение операции часов §6.9 | `clock utc_now` |
| `fresh_id` | `kind` | новый идентификатор; `kind` ∈ {`uuid4`} | `fresh_id uuid4` |
| `constant` | `symbol` | константа поставщика данных §6.10 | (`constant` со строковым значением) |
| `enum` | `type`, `member` | член объявленного перечисления (как §6.1) | `constant AuditAction.X` |
| `literal` | `value` | только `true`/`false` | `constant true/false` |
| `none` | — | `None` | `none` |
| `empty` | — | пустая коллекция | `constant empty list` |

Плюс одна необязательная ячейка `convert` у `name`, `field`, `part_field` —
значение из закрытого набора версии 1:

| `convert` | из → в | что делает | нужна в данных |
|---|---|---|---|
| `uuid_canonical_string` | `UUID` → `str` | `str(x)` | 33 поля (`AuditIntent.entity_id`, «canonical string») |
| `is_present` | `T \| None` → `bool` | `x is not None` | 5 (`email_verified`) |
| `enum_by_value` | `str` → `Enum` | `Enum(x)` | 2 (`registry_status`) |
| `naive_utc` | `datetime` → `datetime` | aware → naive UTC, naive без изменений | 1 (`photo_date`) |

Конверсия у nullable-источника пропускает `None` насквозь, кроме `is_present`.
Новая конверсия — новое значение закрытого набора (и новая версия, если меняет
смысл валидной спеки), а не выражение.

Строки (`"ok"`, коды причин) литералом не бывают: строковое значение,
которое читает код, — член перечисления (`enum`) или константа поставщика
(`constant`); у значения один дом (§15.3.1). Целые литералом тоже не бывают
в версии 1: единственный целый литерал данных (`0` в `ensure_manual_budget`)
условен и уходит в параметр (§5.3).

**Почему ровно эти.** Это семь видов источника из постановки владельца
(поле входа по адресу, результат контракта, часы, новый id, константа
поставщика, None/пусто, вложенное построение) плюс то, без чего данные не
закрываются: целый вход (`name`), поле уже построенной части (`part_field`,
39 полей — `ExpenseDocument.expense_id ← Expense.expense_id`), член
перечисления (`enum`, 140 полей) и булев литерал (10 полей). Выражения
(`a + b`, `if`, `sum`) не входят и не войдут: см. §5.3.

### 2.5 Коды причин отброса

Закрытый набор; каждая строка может назвать `decision` (идентификатор решения
или инварианта кейса: `M27`, `INV-015`) или `null`.

| код | смысл | примеры причин из данных (74 строки) |
|---|---|---|
| `not_in_target` | целевая модель поля не объявляет | «not declared», «not declared by the view», «omitted», «never returned», «the session carries none», «free label, accepted and not kept (M34)» |
| `authorization_fact` | факт авторизации, не данные записи | «authorization fact» ×8 |
| `checked_only` | проверено на границе и отброшено | «checked, not audited», «checked complete … then discarded (M24, M27)», «the one rejection made here» |
| `confidential` | секрет/персональное, не хранится и не выходит | «never leaves the module», «never stored», «only its hash is stored», INV-015 |
| `stored_elsewhere` | значение живёт в другой записи | «content lives in ApprovedEstimateSnapshot (M36)», «carried as the linked PortalSection.source_key», «Registry customer data» |
| `superseded_by_persisted` | заявка, решает сохранённое | «a claim; persisted role decides», «re-read from persistence» |
| `filter_only` | использовано только для отбора | «filter only» |
| `ordering_only` | использовано только для порядка | «ordering only» |
| `binary_boundary` | ссылка на байты не пересекает границу | «binary boundary», «never in a view» |

Все 74 строки отброса из файла пробелов ложатся на эти девять кодов без остатка.

### 2.6 Пример: `_build_expense_aggregate`

Контракт (State 6) переезжает в модуль построителей и становится публичным:

```json
"build_expense_aggregate": "(intake: ExpenseIntake, fingerprint: str, created_at: datetime) -> ExpenseAggregate"
```

```json
"build_expense_aggregate": {
  "form": "construct",
  "target": "ExpenseAggregate",
  "consumers": ["expense_intake"],
  "over": null, "element": null, "base": null,
  "parts": {
    "expense": {
      "target": "Expense", "over": null, "element": null,
      "fields": {
        "expense_id":            {"ref": "fresh_id", "kind": "uuid4"},
        "project_id":            {"ref": "field", "of": "intake", "field": "project_id"},
        "recognized_document_id":{"ref": "field", "of": "intake", "field": "recognized_document_id"},
        "supplier":              {"ref": "field", "of": "intake", "field": "supplier"},
        "document_date":         {"ref": "field", "of": "intake", "field": "document_date"},
        "total_amount":          {"ref": "field", "of": "intake", "field": "total_amount"},
        "included":              {"ref": "literal", "value": true},
        "created_at":            {"ref": "name", "name": "created_at"},
        "confirmed_at":          {"ref": "field", "of": "intake", "field": "confirmed_at"},
        "confirmed_by":          {"ref": "field", "of": "intake", "field": "confirmed_by"},
        "provenance_ref":        {"ref": "field", "of": "intake", "field": "provenance_ref"},
        "intake_fingerprint":    {"ref": "name", "name": "fingerprint"},
        "updated_at":            {"ref": "none"},
        "updated_by":            {"ref": "none"}
      }
    },
    "document": {
      "target": "ExpenseDocument", "over": null, "element": null,
      "fields": {
        "document_id":        {"ref": "fresh_id", "kind": "uuid4"},
        "expense_id":         {"ref": "part_field", "part": "expense", "field": "expense_id"},
        "document_reference": {"ref": "field", "of": "intake", "field": "document_reference"},
        "file_ref":           {"ref": "field", "of": "intake", "field": "file_ref"},
        "description":        {"ref": "field", "of": "intake", "field": "document_type"},
        "client_visible":     {"ref": "literal", "value": true},
        "created_at":         {"ref": "name", "name": "created_at"},
        "updated_at":         {"ref": "none"},
        "updated_by":         {"ref": "none"}
      }
    },
    "allocations": {
      "target": "ExpenseAllocation",
      "over": {"ref": "field", "of": "intake", "field": "allocations"},
      "element": "instruction",
      "fields": {
        "allocation_id": {"ref": "fresh_id", "kind": "uuid4"},
        "expense_id":    {"ref": "part_field", "part": "expense", "field": "expense_id"},
        "target":        {"ref": "field", "of": "instruction", "field": "target"},
        "section_id":    {"ref": "field", "of": "instruction", "field": "section_id"},
        "amount":        {"ref": "field", "of": "instruction", "field": "amount"},
        "created_at":    {"ref": "name", "name": "created_at"},
        "created_by":    {"ref": "field", "of": "intake", "field": "confirmed_by"},
        "updated_at":    {"ref": "none"},
        "updated_by":    {"ref": "none"}
      }
    }
  },
  "fields": {
    "expense":     {"ref": "part", "name": "expense"},
    "document":    {"ref": "part", "name": "document"},
    "allocations": {"ref": "part", "name": "allocations"}
  },
  "dropped": {
    "intake": {
      "currency":         {"reason": "checked_only", "decision": null},
      "contract_version": {"reason": "checked_only", "decision": null}
    }
  }
}
```

Все источники взяты из файла пробелов как есть; `created_by` файл помечает
как «no note names it; running code» — источник из работающего кода, который
IR делает явным решением, а не догадкой генерации.

---

## 3. Проверка замыкания (Workbench)

### 3.1 Слой

Проверка принадлежит **State 6** и запускается на его передаче, отдельной
фазой сразу после `state6_exact_contracts`:

```text
state6_exact_contracts
  -> deterministic_record_construction_closure   (новая; conditional: rules.record_construction_backend is used)
  -> deterministic_persistence_closure
  -> ...
```

- Артефакт кейса: `70_record_construction_closure.json`
  (`schema_version: spec_workbench_record_construction_backend_closure.v1`,
  `status`, `source_refs`, `rationale`, `backend_ir` — как у
  `70_data_provider_closure.json`).
- Gate tool: `tools/design_record_construction.py --coverage`.
- Почему State 6: всё, что проверка читает, принадлежит State 1 (модели) и
  State 6 (контракты построителей, их владельцы, детерминизм). Notes (State 7)
  ей не нужны. Это прямой ответ на #147: дефект построения (неизвестное поле,
  поле без источника) обнаруживается на передаче слоя, который его создал, а
  не на сборке и не на Route B (`model_constructor_unknown_field`).
- Почему не раньше: до State 6 нет контрактов, а сигнатура построителя —
  единственный источник типов параметров (§2.1).
- Регистрация: строка `StandardBackend(id="record_construction",
  closure_file="70_record_construction_closure.json", rule_key=
  "record_construction_backend", scope_mapping_path=("constructions",))` в
  `tools/standard_backends.py`; State 7 и Stage 8.1 видят построители как
  детерминированные scopes так же, как рецепты §6.7.

### 3.2 Проверки (любая находка = BLOCK)

| код | проверка |
|---|---|
| `RC001 construction_form` | закрытая форма §2: ключи каждого узла, известные `ref`/ячейки/значения `convert`/`kind`/`reason`, ref — лист §6.0, `over` и `element` вместе, `base` только при `replace`. Неизвестное — отказ, не пропуск. |
| `RC002 target_field_unsourced` | у поля цели (части) нет источника. При `replace` источник незаданных полей — `base`. |
| `RC003 target_field_multiple_sources` | у поля больше одного источника: дубль ключа в JSON (загрузка с `object_pairs_hook`, отвергающим повтор); при `replace` поле в `fields` со ссылкой `{"ref": "field", "of": <base>, "field": <то же поле>}` — пустая замена, второй дом значения `base`. |
| `RC004 target_field_unknown` | поле не объявлено моделью цели — то, что сегодня ловит `model_constructor_unknown_field` после генерации. |
| `RC005 input_field_undisposed` | поле модельного имени не прочитано ни одной ссылкой и не отброшено. |
| `RC006 input_field_read_and_dropped` | поле и прочитано, и отброшено; либо отброшено поле, которого у модели нет. |
| `RC007 name_unused` | параметр контракта не используется ни одной ссылкой (`name`, `field`, `over`, `call.args`, `base`). Неиспользуемому параметру в сигнатуре построителя не место; отброс бывает только у полей модельного имени. |
| `RC008 source_type_incompatible` | тип источника не присваивается типу поля по §12: равенство типов; `T` → `T \| None`; `list[T]` для части с `over`; `none` только в nullable; `empty` только в коллекцию; `fresh_id` только в `UUID`; `clock` — в тип представления мгновения §6.9 (`datetime` для v4/v5); `literal` — в `bool`; `enum` — в этот же enum; `constant` — по таблице типов доступа §6.10; `convert` — по своей сигнатуре. Неявных числовых или строковых преобразований нет. |
| `RC009 reference_unresolved` | имя, часть, функция, enum/член, символ поставщика не существуют; `clock` при отсутствии `rules.system_clock_backend` с функцией настенных часов; `field` глубже одного уровня (адрес из двух звеньев невыразим: нужна часть или параметр). |
| `RC010 call_contract_mismatch` | `call`: контракт существует; число и типы `args` совпадают с параметрами; `determinism[function] is true`; среди параметров нет порта (interface, хранилище, транзакция); функция публична и принадлежит **другому** модулю, чем потребитель построителя, либо сама является построителем этого backend-а. Иначе это не источник данных, а поведение (§5.3). |
| `RC011 builder_contract_mismatch` | контракт построителя: возвращает `target` (или `list[target]` при `over`); при `replace` параметр `base` имеет тип `target`. |
| `RC012 owner_not_unique` | `module_functions[wiring.module]` равен ключам `constructions`; ни один построитель не принадлежит другому модулю; имя построителя не совпадает с другой экспортируемой функцией. |
| `RC013 determinism_mismatch` | `determinism[builder]` равен выводу из IR: `false`, если в построении (или в вызванном построителе) есть `clock` или `fresh_id`, иначе `true`. |
| `RC014 import_edges` | у каждого `consumers[i]` есть ребро `imports.module_internal[consumer][wiring.module]` с этим построителем; у модуля построителей есть рёбра к модулю часов (если есть `clock`), к поставщику данных (если есть `constant`), к модулям вызываемых функций; граф без циклов (потребитель не может быть модулем вызываемой функции). |
| `RC015 part_graph` | граф частей ацикличен; поле части-коллекции не читается вне её области; каждая часть использована. |

Проверки детерминированы и локальны к IR, `models`, `contracts`,
`module_functions`, `determinism`, `imports.module_internal` и
`rules.system_clock_backend`/`rules.data_provider_backend`. Тексты notes не
читаются.

### 3.3 Совпадение с фабрикой

Фабрика остаётся судьёй закрытой формы: `_closed_data` эмиттера (§4.2)
выполняет те же проверки и стоит в `validate_spec` до генерации. Чтобы
Workbench и Factory не разъехались, обе стороны прогоняют один набор фикстур
(одна валидная спека + по фикстуре на каждый код RC001–RC015 с ожидаемым
отказом); Stage 9 admission получает строку вида FA021: функции, которыми
владеет модуль построителей, равны ключам `constructions` целевой фабрики.

---

## 4. Сторона фабрики

### 4.1 Где живёт выпущенный построитель: отдельный модуль

Решение: **отдельный выпущенный модуль** `wiring.module` (по умолчанию
`record_builders`), который целиком принадлежит эмиттеру. LLM-модуль
получает построители как обычные импорты.

Встроить выпущенные функции внутрь LLM-модуля нельзя без ломки трёх опор
фабрики:

1. **§15.9, исключительное владение файлом.** «Каждый файл проекта
   порождается ровно одним генератором… Смешанное владение внутри файла
   запрещено». Встраивание — ровно смешанное владение.
2. **Сборка помодульная.** Стратегия детерминированной сборки —
   `selected_draft_copy`: `rebuild_module.py` копирует черновик целиком после
   draft static gate и сверяет `<draft>.producer.json` (штамп связывает байты
   черновика с эмиттером, его скриптом и входами спеки). Черновик,
   отличающийся от эмиссии текущих входов, блокируется
   (`deterministic_draft_producer_mismatch`). Склейки «часть файла от
   эмиттера, часть от LLM» нет; её пришлось бы вводить новой стратегией
   сборки с частичной аттестацией, и цикл ремонта черновика
   (`repair_draft_from_static_gates`) получил бы право править выпущенный
   код.
3. **Класс неделим, модуль неделим** (§8, §6.2): прецедент фабрики —
   «нерегулярность одного метода делает весь module irregular; частичная
   эмиссия класса/файла и companion-делегирование отсутствуют».

Что это стоит: построители, которые сегодня — приватные помощники
(`_build_expense_aggregate`), переезжают в другой модуль и становятся
публичными контрактами (`build_expense_aggregate`); у потребителя появляется
ребро `module_internal`. Это обычное изменение State 6, и оно проверяется
RC012/RC014.

Почему один модуль, а не модуль на потребителя: `DeclaredBackend` фабрики
несёт один `default_module`, а `declared_backend_selector` выбирает модуль по
`rules.<key>.wiring.module` — один модуль ложится на существующий механизм без
нового селектора. Срез каждого потребителя получает только импортированные им
символы (`imports.declared` берёт контракты ровно объявленных функций), так что
размер модуля на промпт не влияет. Разбиение по потребителям — открытый
вопрос (§8).

### 4.2 Эмиттер: `tools/generate_record_construction_draft.py`

По `tools/emitters/ADDING_AN_EMITTER.md`, без правки центральных файлов:

- `PRODUCER = "deterministic_record_construction_v1"`,
  `EMISSION_KIND = "record_construction"`,
  `RULE_KEY = "record_construction_backend"`.
- `_closed_data(spec, module)` — проверки §3.2 над базовой спекой; любое
  нарушение — `EmissionDefect` (exit 1, `spec_defect`).
- `emit_module(spec, module) -> str` — чистая функция; построители в
  лексикографическом порядке имён, части в топологическом порядке, поля
  каждого конструктора в порядке объявления полей модели.
- `CATALOG_ENTRY` с `ir_skeleton`, который `_closed_data` принимает как есть.
- `focused_check(project_root, spec, module)` — см. §4.6.

Что выпускается для примера §2.6:

```python
"""Emitted by deterministic_record_construction_v1. Do not edit."""
from __future__ import annotations

import uuid
from datetime import datetime

from core.models import Expense, ExpenseAggregate, ExpenseAllocation, ExpenseDocument, ExpenseIntake


def build_expense_aggregate(intake: ExpenseIntake, fingerprint: str, created_at: datetime) -> ExpenseAggregate:
    expense = Expense(
        expense_id=uuid.uuid4(),
        project_id=intake.project_id,
        recognized_document_id=intake.recognized_document_id,
        supplier=intake.supplier,
        document_date=intake.document_date,
        total_amount=intake.total_amount,
        included=True,
        created_at=created_at,
        confirmed_at=intake.confirmed_at,
        confirmed_by=intake.confirmed_by,
        provenance_ref=intake.provenance_ref,
        intake_fingerprint=fingerprint,
        updated_at=None,
        updated_by=None,
    )
    allocations = [
        ExpenseAllocation(
            allocation_id=uuid.uuid4(),
            expense_id=expense.expense_id,
            target=instruction.target,
            section_id=instruction.section_id,
            amount=instruction.amount,
            created_at=created_at,
            created_by=intake.confirmed_by,
            updated_at=None,
            updated_by=None,
        )
        for instruction in intake.allocations
    ]
    document = ExpenseDocument(
        document_id=uuid.uuid4(),
        expense_id=expense.expense_id,
        document_reference=intake.document_reference,
        file_ref=intake.file_ref,
        description=intake.document_type,
        client_visible=True,
        created_at=created_at,
        updated_at=None,
        updated_by=None,
    )
    return ExpenseAggregate(expense=expense, allocations=allocations, document=document)
```

Правила lowering версии 1:

- Каждое поле — keyword-аргумент конструктора; позиционных аргументов,
  `**kwargs`, `model_copy`, `model_construct` нет. `replace` понижается в
  полный конструктор, где неизменённые поля — `base.<field>`: так запись
  проходит валидацию модели и статические гейты конструктора.
- `clock`: если в построителе есть хотя бы один `clock`, первая строка тела —
  одно чтение функции настенных часов из `rules.system_clock_backend`
  (`now = utc_now()`), и все ссылки `clock` получают это одно показание
  («the one timestamp the operation captured» — 45 из 50 полей с часами
  несут ровно эту формулировку). Это согласовано с §6.8
  (`clock_dependency_bypassed`): модуль построителей не читает часы хоста,
  а импортирует выданную операцию.
- `fresh_id: uuid4` → `uuid.uuid4()` на каждое поле и каждый элемент.
- `constant` → импорт символа из `rules.data_provider_backend.wiring.module`;
  значение в модуль построителей не попадает (§15.9).
- `call` → вызов импортированной функции с именами-аргументами по порядку
  параметров контракта.
- Ветвлений, циклов кроме comprehension для `over`, исключений, I/O нет.

### 4.3 Регистрация

`tools/emitters/plugins/record_construction.py`:

```python
RULE_KEY = "record_construction_backend"

DESCRIPTOR = EmitterDescriptor(
    emitter_id="record_construction",
    order=495,                      # свободно: 490 keyed_file_spool, 500 system_clock
    select=declared_backend_selector(RULE_KEY, RULE_KEY),
    tool="tools.generate_record_construction_draft",
    validation="tools.generate_record_construction_draft:emit_module",
    focused_check=True,
    declared_backend=DeclaredBackend(rule_key=RULE_KEY, kind=RULE_KEY, default_module="record_builders"),
    catalog_rank=11,                # занято 0..10
    slice_contribution="tools.emitters.slices.record_construction:CONTRIBUTION",
    capability=CapabilityDeclaration(
        standard_sections=("6.13",),
        ir_forms=(IRForm(1, "python_record_builders_v1"),),
        consumes=("rules.record_construction_backend", "models", "contracts",
                  "module_functions", "determinism", "imports", "rules.system_clock_backend",
                  "rules.data_provider_backend"),
    ),
)
```

`not_applicable` — `refuse` (по умолчанию): объявленный backend без эмиссии —
ошибка, а не LLM. `BUILTIN_IDS` в `test_emitter_registry.py` получает
`record_construction`. Дальше всё, что перечисляет `ADDING_AN_EMITTER.md`
(«What the factory then does on its own»), включается само: закрытое
пространство имён в `validate_spec`, диспетчеризация в `run_generate`,
аттестация штампа в `rebuild_module`, каталог MCP `emitter_catalog`, запуск
`focused_check`.

### 4.4 Как построитель доходит до LLM-модуля

Существующий срез уже несёт то, что нужно:

- проход `imports.declared` (order 60) кладёт в локальную спеку потребителя
  контракты функций, объявленных ребром `module_internal` — значит, модель
  видит `build_expense_aggregate(intake: ExpenseIntake, fingerprint: str,
  created_at: datetime) -> ExpenseAggregate` и импорт;
- note потребителя называет построитель именем выпущенного символа (§15.3.1:
  «то, что выпускает детерминированный backend, note называет именем
  выпущенного символа»): `MUST build the ExpenseAggregate with the imported
  build_expense_aggregate`. Прозы о том, какое поле откуда, в notes больше нет.

Новый проход среза `backend.record_construction` (order 34 — до коллектора
`rules.final` на 38; читает только `in.spec`, как `backend.router` на 32)
пишет `contrib.rules.record_construction` — **вид владения** для потребителя,
а не IR целиком:

```json
"record_construction_backend": {
  "owned_targets": {"ExpenseAggregate": ["build_expense_aggregate"],
                    "Expense": ["build_expense_aggregate"],
                    "ExpenseDocument": ["build_expense_aggregate"],
                    "ExpenseAllocation": ["build_expense_aggregate"]}
}
```

Это множество моделей, которые модуль получает от построителей и не
конструирует сам. Таблица источников полей в промпт не идёт: модели она не
нужна (она вызывает функцию), а увидев её, модель склонна переписать
построение руками. Тот же вид читает гейт §4.5.

### 4.5 Новый draft static gate и `model_constructor_unknown_field`

`record_construction_bypassed` (BLOCK, источник `local_spec.rules`): в
LLM-черновике потребителя вызов конструктора (или `model_copy`/
`model_construct`) модели из `owned_targets` этого модуля. Строится по
образцу `clock_dependency_bypassed` §6.8: если спека выдала модулю
построитель, модуль не строит запись сам.

Взаимодействие с существующими гейтами конструктора
(`model_constructor_unknown_field`, `model_constructor_missing_required_field`,
`model_constructor_field_type_mismatch`, `model_constructor_positional_arguments`):

- В модуле построителей они срабатывать не могут: RC004/RC002/RC008 и
  keyword-only lowering доказывают это до эмиссии. Гейты по-прежнему
  прогоняются на выпущенном черновике (rebuild ставит draft static gate перед
  копированием) — как страховка эмиттера, а не как проверка спеки.
- В потребителе построение владеемых моделей запрещено новым гейтом, поэтому
  класс ошибки, на котором остановился Route B, исчезает для них целиком.
  Для невладеемых моделей гейты работают как сейчас — миграция постепенная.

### 4.6 Покрытие и фокусная проверка

- `validate_generated_coverage` на результате эмиссии, как у всех эмиттеров.
- `focused_check`: для каждого построителя синтетические входы (значения,
  различимые по полю), вызов, затем для каждого поля цели сравнение с его
  ссылкой: `field` — равенство значению входа, `part_field` — тождество
  поля части, `clock` — одно и то же показание во всех полях (подменённые
  часы возвращают последовательные значения, разные показания — провал),
  `fresh_id` — UUID4 и попарно различны, `none`/`empty`/`literal`/`enum` —
  значение; входы после вызова не изменены. Ровно такую проверку нельзя
  написать для LLM-кода, потому что у него нет таблицы источников.
- Пин эмиссии (как `test_persistence_emission_compat.py`): байты эмиссии
  фикстур закреплены; аддитивная форма не сдвигает пин, иначе — новая версия.

---

## 5. Покрытие по данным client-portal

Одноразовый скрипт (вне репозитория, в scratchpad сессии) прогнал 84 места
файла пробелов против формы §2 при контрактах `global_spec.json` того же
коммита `9ac5ed63`.

### 5.1 Поля (1080)

| класс | полей | что это |
|---|---:|---|
| прямой источник версии 1 | 937 | `field` 211 (+81 над записью, которую оркестрация прочитала из хранилища, см. §5.2), `unchanged` при `replace` 172, `enum` 140, `none` 110, `name` 81, `clock` 46, `part_field` 39, `fresh_id` 22, `part` 18, `literal` 11, вызов другого построителя 6 |
| нужна `convert` | 41 | `uuid_canonical_string` 33, `is_present` 5, `enum_by_value` 2, `naive_utc` 1 |
| `call` публичной детерминированной функции | 6 | `validate_eur_amount`, `calculate_completed_work`, `calculate_material_balance`, … |
| **выразимо итого** | **984 (91,1 %)** | |
| подъём в параметр (значение вычисляет оркестрация) | 15 | вызов недетерминированной/портовой функции 8 (`hash_password`, `_next_key_version`, `build_*_view`), приватной функции того же модуля 7 (`_normalize_staff_email`, `_ordered_plans`, `_find_unresolved_allocation_count`) |
| логика | 54 | §5.3 |
| открыто в данных | 26 | §5.4 |
| значение не названо | 1 | `HealthStatus.status` у `readiness_endpoint` («the generic health response») |

Литерал `"ok"` у `liveness_endpoint` выразим, но по §2.4 требует константы
поставщика или члена перечисления, а не строкового литерала.

### 5.2 Места (84)

| вердикт | мест | |
|---|---:|---|
| полностью | 52 | 27 `construct`, 14 `project`, 11 `replace` |
| полностью, с подъёмом значения в параметр | 4 | `create_staff_account`, `change_staff_password`, `perform_recovery_override`, `bootstrap_first_administrator` (хеш пароля, нормализация email) |
| частично: логика остаётся в оркестрации | 17 | §5.3 |
| частично + открытое поле | 4 | `_build_imported_plans`, `set_expense_inclusion`, `_project_budget_sections`, `_project_expense_summary` |
| только открытые/неназванные поля мешают | 4 | `replace_expense_allocations`, `update_expense_document`, `publish_progress_photo`, `readiness_endpoint` — после решения владельца станут «полностью» |
| не выражается вовсе | 3 | декодеры Registry: `list_active_projects`, `validate_project_reference`, `get_project_context` |

Важная структурная цифра: из 84 мест **29** — уже чистые помощники (нет
параметра-хранилища/транзакции/порта), и 18 из них выражаются полностью: их
контракт просто переезжает в модуль построителей. **55** мест — оркестрации
(`create_staff_account(store, …)`): построение там встроено в функцию с I/O, и
для него нужен *новый* контракт построителя, которому оркестрация передаёт
прочитанные записи. В 24 местах источник — запись, прочитанная из хранилища
(`StaffAccount.staff_id` в `sign_out_staff`), то есть параметр построителя
появляется впервые. Это работа State 6 при миграции, не дефект формы.

### 5.3 Источники, которые на самом деле логика (54)

| вид | полей | где | что делать |
|---|---:|---|---|
| выбор члена перечисления по исходу | 10 | `AuditIntent.action/result` в `authenticate_staff`, `change_staff_status`, `change_service_principal_status`, `import_snapshot`, `set_expense_inclusion`, `upsert_manual_section_plan`; `BudgetVersion.status`; `WorkBalanceResult.label` | параметр построителя типа перечисления; выбор — поведение оркестрации, закрытое правилами/таблицей §6.10 v2 там, где это соответствие над таксономией |
| агрегат над коллекцией (sum/count) | 13 | `build_budget_view`, `_project_budget_sections`, `_project_expense_summary`, `_project_progress`, `_project_payments`, `revoke_staff_sessions` | параметр; суммы — поведение (или функция `financial_policy`, тогда `call`) |
| поиск/соединение с отсутствием | 8 | «None without a row», «no match», «linked section», «existing plan else fresh» | параметр; выбор строки — поведение |
| условное время/None по ветке | 6 | `change_staff_status.email_verified_at`, `change_service_principal_status.disabled_*`, `activate_budget_version.*` | два построителя на две ветки или параметр |
| доступность секции обзора | 6 | `build_project_overview.*_availability` | параметр; это исход чтения, не данные |
| ветка «учётная запись не найдена», reason по исходу | 3 | `authenticate_staff`, `import_snapshot.reason_code` | параметр |
| арифметика над значениями | 3 | `expires_at = clock + lifetime` ×2, `balance = completed − payments` | параметр или функция политики (`call`) |
| условное значение новой/существующей версии | 2 | `ensure_manual_budget.plans`, `.unresolved_allocation_count` | два построителя или параметр |
| проверка членства | 1 | `resolved_in_active_budget` | параметр |
| общий новый id с выпуском секрета | 1 | `authenticate_staff.session_id` | параметр (id создаётся до выпуска секрета) |
| конверсия + None при отсутствии | 1 | `issue_service_credential.expires_at` | `name` + `convert: naive_utc` (nullable пропускается) — после уточнения правила выразимо |

Общий ответ один: **логика остаётся LLM-поведением, которое вызывает
построитель** и передаёт ему результат параметром. IR такие поля выражает
ссылкой `name` на параметр — то есть место становится «полностью выразимым»
ценой параметра, а логика остаётся в notes оркестрации как поведение
(условие, порядок, сумма), но уже без прозы о полях. Словарь выражений в IR
не входит: §6.0 запрещает микро-синтаксис, а условие — не форма данных.
Где логика — соответствие над таксономией (выбор `AuditAction` по исходу),
её дом — таблица `record_tuple` §6.10 v2 с `key`/`total`, а не IR построения.

### 5.4 Открытые поля (26) — не форма, а решение

- **16 полей декодеров Registry** (3 места). Источник — поле ответа внешнего
  сервиса; его имя нигде в кейсе не записано. Это не построение из входа
  модели, а декодирование провода: нужна запись контракта Registry
  (`platform/manifest`, `EXTERNAL_CONTRACT_EVIDENCE.md`) и отдельная форма
  декодера. В этот IR не входит.
- **10 полей в 7 местах** — расхождения notes и кода или неназванный источник
  (`updated_by` при `set_expense_inclusion`/`update_expense_document`,
  `updated_*` при `replace_expense_allocations` и `publish_progress_photo`,
  `SectionPlan.updated_by`, `section_display_name`,
  `has_unresolved_allocations`). IR их выразит, как только владелец выберет
  источник. Два последних требуют изменения сигнатуры (во вход не приходят
  имена секций).

---

## 6. План реализации

Порядок задан тем, что Workbench не может экспортировать IR, который фабрика
отвергает («declared deterministic backend has no registered emitter»).

| # | репозиторий, ветка | содержание | тесты |
|---|---|---|---|
| 0 | spec-workbench `docs/record-construction-backend` | этот документ | — |
| 1 | code_factory `tools/record-construction-emitter` + spec-workbench `tools/spec-standard-6-13` | эмиттер, дескриптор, каталог; текст §6.13 применяется **одновременно** к обеим копиям `SPEC_STANDARD.md` (одинаковые байты; слить парой) | выбор (`deterministic_emission_kind == "record_construction"`, `None` для чужого модуля); детерминизм (две эмиссии байт в байт); закрытая форма — фикстура на каждый RC-код даёт `EmissionDefect`; покрытие; `focused_check`; пин эмиссии; `test_emitter_registry`/`test_emitter_catalog` |
| 2 | spec-workbench `tools/record-construction-closure` | `tools/design_record_construction.py`, фаза в `authoring_sequence.json`, `StandardBackend`, сборка `backend_ir` → `rules`, строка admission | те же фикстуры, что в п.1: один и тот же набор принимается/отвергается обеими сторонами с теми же кодами (тест паритета читает фикстуры из обоих мест); фаза видна `authoring next` |
| 3 | code_factory `tools/record-construction-bypass-gate` | проход среза `backend.record_construction`, гейт `record_construction_bypassed` в `draft_static_table.py` | `test_slicer_passes` (порядок до `rules.final`), `test_draft_static_gates` (позитив/негатив), `test_gate_registry` |
| 4 | spec-workbench `tools/note-gate-construction` (по желанию) | State 7: находка, если note потребителя называет источник поля владеемой цели («same-named field of …») — проза, которую IR сделал вторым домом | `test_note_gate` |
| 5 | spec-workbench `agent/client-portal` | миграция кейса, ниже | gates кейса, сборка, admission, Route B |

### 6.1 Миграция client-portal

Кейс сейчас стоит на `state0_product_frame` (открыт один блок
`00_product.md:Decisions`); миграция идёт после его закрытия.

1. **State 6, контракты построителей.** Для каждого изменяемого имени —
   `design_provenance`; решения, которые его держат, называются в обосновании.
   18 полностью выразимых чистых помощников переезжают в `record_builders`
   под публичными именами. Для 34 полностью выразимых оркестраций и 4 мест с
   подъёмом — новые контракты построителей, входы которых — прочитанные
   записи (24 места) и поднятые значения. `determinism` построителей
   выводится из IR (RC013).
2. **IR.** `70_record_construction_closure.json` собирается из
   `record_construction_gaps.json` механическим переводом (`param_field` →
   `field`, `result Model` → `part`, `result Model.f` → `part_field`/`field`,
   `constant X.Y` → `enum`, `true/false` → `literal`, «canonical string» →
   `convert`), затем закрывается вручную: имена параметров вместо имён
   моделей, `dropped` с кодами §2.5 для мест, где файл пробелов источники
   входов не размечал (52 из 84).
3. **Частичные места (21).** Поле-логика становится параметром построителя;
   логика остаётся поведением оркестрации в её notes.
4. **Открытое.** 8 расхождений, значение готовности и 2 вопроса сигнатуры —
   вопросы владельцу (§8); Registry — запись внешнего контракта и отдельная
   форма декодера.
5. **Notes.** Из notes мигрированных функций уходит вся проза о полях
   («same-named field of publication», «the one timestamp the operation
   captured», «None, never amended»); остаётся одна note на вызов:
   `MUST build <Target> with the imported <builder>` плюс поведение, которое
   выбирает поднятые значения. `record_construction_gaps.json` выполнил роль:
   его содержание становится IR (один дом, §15.4), файл удаляется или
   остаётся историей — решение владельца.
6. **Политики-проза.** `rules.audit_entity_id_policy` («canonical string form
   of the audited entity identifier», `uuid_serialization: required_str_call`)
   становится ячейкой `convert: uuid_canonical_string` у 33 полей; сама
   политика — записанное решение, его судьба — вопрос владельцу.

---

## 7. Черновик раздела стандарта (не применён)

> Текст ниже — **черновик**. Обе копии `SPEC_STANDARD.md` (Workbench
> `skills/spec-authoring/SPEC_STANDARD.md` и Factory `SPEC_STANDARD.md`)
> сейчас байт в байт одинаковы и остаются такими: раздел вносится в обе
> копии одним парным изменением (план, п.1), не этим PR. Дополнительно
> меняются: строка индекса `SPEC_STANDARD_INDEX.md`, перечень «то, что
> выпускает детерминированный backend» в §6 и §15.3.1 (добавить «функцию
> построения записи (§6.13)»).

```markdown
### 6.13 `record_construction_backend/v1`

`rules.record_construction_backend` версии 1 — закрытый IR построения записей
объявленных моделей из входов: какое поле цели из какого источника и какое
поле входа отброшено и почему. Прежде это описывалось прозой notes и
переизобреталось генерацией в каждом модуле. Единственный emitter —
`python_record_builders_v1`.

Форма закрыта:

    {
      "kind": "record_construction_backend",
      "schema_version": 1,
      "backend": {"emitter": "python_record_builders_v1"},
      "wiring": {"module": "<module>", "models_module": "<models module>"},
      "constructions": {
        "<builder>": {
          "form": "construct | replace",
          "target": "<Model>",
          "consumers": ["<module>"],
          "over": null, "element": null, "base": null,
          "parts": {
            "<part>": {"target": "<Model>", "over": null, "element": null, "fields": {}}
          },
          "fields": {"<field>": {"ref": "<source>"}},
          "dropped": {"<name>": {"<field>": {"reason": "<code>", "decision": null}}}
        }
      }
    }

Модуль `wiring.module` владеет ровно функциями из `constructions`. Сигнатура
построителя — `contracts[<builder>]`; в IR она не повторяется. Построитель
возвращает `target`, при `over` — `list[target]`; при `form: replace`
параметр `base` имеет тип `target`, и поля, которых нет в `fields`, берутся из
него без изменения.

Источник поля — листовой ref §6.0 из закрытого набора версии:

| ref | ячейки | значение |
|---|---|---|
| `name` | `name` | параметр контракта или `element` целиком |
| `field` | `of`, `field` | одно поле имени — ровно один уровень |
| `part` | `name` | запись или коллекция части |
| `part_field` | `part`, `field` | поле одиночной части |
| `call` | `function`, `args` | результат детерминированного контракта без портов из другого модуля; `args` — имена |
| `clock` | — | одно показание операции настенных часов §6.9 на вызов построителя |
| `fresh_id` | `kind` | новый идентификатор; `kind`: `uuid4` |
| `constant` | `symbol` | константа поставщика данных §6.10 |
| `enum` | `type`, `member` | член объявленного перечисления |
| `literal` | `value` | `true` или `false` |
| `none` | — | `None` (поле nullable) |
| `empty` | — | пустая коллекция |

`name`, `field`, `part_field` могут нести `convert` из закрытого набора
`uuid_canonical_string`, `is_present`, `enum_by_value`, `naive_utc`.
Выражений, условий, сумм и строковых литералов нет: значение, которое
вычисляется поведением, приходит параметром построителя, а его вычисление
остаётся поведением вызывающей функции.

Код причины отброса — из закрытого набора `not_in_target`,
`authorization_fact`, `checked_only`, `confidential`, `stored_elsewhere`,
`superseded_by_persisted`, `filter_only`, `ordering_only`, `binary_boundary`.

**Замыкание (нарушение = невалидная спека):** у каждого поля цели и каждой
части ровно один источник, поля вне модели нет; каждое поле каждого
модельного имени прочитано ссылкой или отброшено, но не то и другое; каждый
параметр использован; тип источника присваивается типу поля по §12 без
неявных преобразований; все имена, части, функции, члены и символы
существуют, `call` — детерминированный контракт без портов; `determinism`
построителя равен `false` ровно при `clock` или `fresh_id`; у каждого
потребителя есть ребро `module_internal` к построителю, граф импорта без
циклов; граф частей ацикличен.

Потребитель вызывает построитель по имени (§15.3.1), note называет его
символом. Модуль, которому спека выдала построитель цели, эту цель сам не
конструирует (`record_construction_bypassed`). Новая форма ref, конверсии или
кода причины — новое значение закрытого набора и новая версия, если меняет
смысл хотя бы одной валидной спеки.
```

---

## 8. Открытые вопросы владельцу

1. **Часы.** Версия 1 читает часы внутри построителя одним показанием на
   вызов. Если оркестрация использует то же мгновение вне построителя (сравнение
   сроков, второй построитель той же операции), она читает его из
   построенной записи или передаёт параметром `created_at`, как делают уже
   сейчас `_build_expense_aggregate` и `_build_audit_record`. Принять так, или
   требовать, чтобы мгновение всегда приходило параметром (тогда `clock`
   исчезает из словаря, а построители становятся чистыми, кроме `fresh_id`)?
2. **Гранулярность.** Один построитель на место (84) или общие
   параметризованные построители? `AuditIntent` строится в ~35 местах почти
   одинаково (актор из контекста администратора, `action`/`entity_kind` —
   члены, `entity_id` — канонический UUID); один построитель с параметрами
   `action`, `entity_kind`, `entity_id` сократил бы IR в разы.
3. **Один модуль построителей или модуль на потребителя.** Версия 1 — один
   (ложится на существующий `DeclaredBackend`); модуль на потребителя требует
   своего селектора.
4. **Конверсии.** Принять четыре конверсии версии 1? Ячейка
   `uuid_canonical_string` заменяет прозу `rules.audit_entity_id_policy` —
   политику удалить после миграции или оставить как обоснование?
5. **Вид владения в промпте.** Отдавать потребителю `owned_targets`
   (§4.4) или только контракты и note? Без вида гейт обхода читает IR из
   базовой спеки, а модель узнаёт о запрете только из note.
6. **`call`.** Версия 1 разрешает только публичные детерминированные функции
   без портов из другого модуля. Приватные помощники того же модуля
   (`_normalize_staff_email`, `_ordered_plans`) значит поднимаются в
   параметры либо переезжают в модуль политики публичными. Что выбрать для
   client-portal?
7. **Расхождения кейса (10 полей, 7 мест)** и значение `readiness_endpoint`:
   какой источник верен — notes или работающий код (решение 2026-11-06
   «текущее поведение принято» касалось 7 мест с базисом
   `notes+running code`)?
8. **Registry.** Записать контракт ответа Registry в `platform/manifest` и
   дать декодерам отдельную форму (вне этого IR) — согласны?
9. **Судьба `record_construction_gaps.json`** после переноса в IR: удалить
   (один дом) или оставить историей?
10. **Версия стандарта.** Разрешать `record_construction_backend/v1` в
    спеках редакции 2 и 3 или только в 3?
