# Spike Q9-a — нормативный порядок enum и совместимость с Factory

## Статус

Технический spike к решению владельца по Q9-a (`DATA_CLOSURE_RESEARCH_Q9_Q10_Q11.md`, §6).

**Решение, взятое за основу.** Обычный enum — закрытое множество без
нормативного порядка. Для упорядоченного enum рассматривается кандидат:

```json
{"kind": "enum", "ordered": true, "values": ["open", "business_confidential", "personal_data"]}
```

**Чего spike не делал.** `SPEC_STANDARD.md`, код Workbench и код Factory не
менялись. Cabinet Kernel и рабочие спецификации не менялись. PR в
`code-factory` не открывался.

**База.**

| Что | Ревизия |
|---|---|
| Workbench | `origin/main` @ `9cde0aa` |
| Factory | `MigelSmirnov/code-factory` `main` @ `391c41c` (2026-10-12), shallow clone |
| Данные | копия `global_spec.json` и `60_model_closure_domain.json` Cabinet Kernel @ `b3bee2e` в scratch; перед каждым сценарием меняется только модель `DisclosureClass` |

Скрипты экспериментов (`/tmp/claude-0/q9a/exp*.py`) в PR не входят, их шаги
описаны в §4.

---

## 1. Итог

1. **`ordered` сегодня не отвергается нигде.** Атрибут проходит без
   ошибок и предупреждений через все звенья Workbench и Factory, где бы он
   ни стоял (на enum, на обычной модели, со значением `"yes"`). Он доходит
   до `global_spec.json` и срезов модулей, но **не влияет ни на эмиссию,
   ни на промпт**.
2. **Порядок `values` сохраняется по пути, пока ему не мешают три
   механизма Factory:**
   - эмиттер моделей берёт порядок из **существующего** `models.py`, если
     множество значений не изменилось — перестановка молча теряется;
   - `member_names` в форме `{NAME: value}` и `members` задают свой
     порядок;
   - боевой промпт выводит члены enum **по алфавиту имён**.
3. **Ни один компонент Factory не использует порядок enum как смысл.**
   Порядок влияет только на порядок строк при эмиссии и на хеши.
4. **`StrEnum` сравнивает члены как строки.** Нормативное сравнение по
   порядку объявления даёт только `list(Enum).index`. Эмиттер Factory
   никакого способа ранжирования не генерирует.
5. **Хеши и affected-set перестановку видят.** Адрес `models.X.values` или
   `models.X.ordered` меняется, резолвер Factory находит потребителей,
   черновики пересоздаются.
6. **Рекомендация.** Форма `ordered: true` достаточна как **объявление**,
   но **недостаточна** без четырёх условий (§7):
   - валидация в обоих репозиториях;
   - эмиссия, которая ставит `values` выше кэша `models.py`;
   - сгенерированный эмиттером способ ранжирования;
   - явный вывод упорядоченности в промпт.

   Кроме того, нужен fail-closed механизм против **старой** Factory: сейчас
   она молча проигнорирует атрибут.

---

## 2. Фактический путь enum

| # | Звено | Код | Что происходит с объявлением | Порядок `values` | `ordered` |
|---|---|---|---|---|---|
| 1 | Authored model closure | `60_model_closure_*.json`, схема `spec_workbench_model_closure.v1` | Пишется автором | Как написан | Как написан |
| 2 | Индекс поверхностей моделей Workbench | `tools/model_surface_workbench/index.py:76–95` (`ModelIndex.load`) | `kind == "enum"` → `surface_kind = "enum"`; `accepts()` для enum всегда `True` (`:58–59`) | Не используется | Игнорируется |
| 3 | Проекция Stage 8 | `tools/spec_projection_workbench/service.py:356–424` (`_project`) | Проверяются только `schema_version` и `status: closed` closure-файла (`:362–382`) и что объявление — объект (`:396–400`). Объявление копируется **дословно** (`:423–424`). Сериализация — `json.dumps(…, indent=2)` без `sort_keys` (`:714–715`). | Сохраняется | Сохраняется, не проверяется |
| 4 | Notes gate Workbench | `tools/notes_workbench/gate.py:103–112` | Из моделей берутся только корни `models.<Name>` | — | — |
| 5 | Каноническая валидация Factory | `tools/validate_spec.py:70` (`validate`), `:843–888` (`_check_models`) | Проверяет только, что типы из контрактов и полей объявлены. Форму enum не проверяет. | Не проверяется | Не проверяется |
| 6 | Типовая система v2 Factory | `tools/type_resolver.py:35–36` (`KNOWN_MODEL_KINDS`), `:374–387` (`check_model_kinds`) | Проверяет только `kind` по закрытому реестру | — | Не проверяется |
| 7 | Нормализация Factory | `tools/normalize_spec.py:245`, `:373` | `models` передаются без изменений | Сохраняется | Сохраняется |
| 8 | Срез модуля Factory | `tools/build_local_spec.py:136–145` (`model_reference_text`: `json.dumps(values, sort_keys=True)` — `sort_keys` списки не сортирует), `:148–160` (`select_referenced_models`), `:967` | Объявление попадает в local spec как есть | Сохраняется | Сохраняется |
| 9 | Детерминированная эмиссия `models` | `tools/generate_models_draft.py:276–303` (`emit_enum`) | `class X(StrEnum)`, по `values`: член с исходным именем + алиас UPPER (`enum_member_names`, `:144–154`) | См. ниже | Игнорируется |
| 9a | …если есть `members` | `:232–235` (`structured_enum_members`) | Порядок — из `members` | **Не из `values`** | — |
| 9b | …если `member_names` — список | `:237–240` | `zip(member_names, values)` | Сохраняется | — |
| 9c | …если `member_names` — `{NAME: value}` | `:243–244` | Порядок — из словаря `member_names` | **Не из `values`** | — |
| 9d | …если `member_names` — `{value: NAME}` | `:245–246` | Итерация по `values` | Сохраняется | — |
| 9e | …если уже есть `models.py` проекта | `:802` (`infer_runtime_models_path`), `:661` (`extract_runtime_enum_members`), `:250–264` (`runtime_members_for_spec`) | При **равенстве множеств** значений берутся члены и **порядок** из старого файла | **Перестановка теряется** | — |
| 10 | Промпт LLM-модуля, боевой путь | `tools/generate_agent.py:2016–2033` (`models_code` из `models.py`), `:343–372` (`_parse_runtime_model_surface`: берутся только члены с `isupper()`, `:366`), `:442` | `- X enum members: …` — `sorted(members.items())`, **по алфавиту имён** | **Не передаётся** | Не передаётся |
| 10a | Промпт, запасной путь (`models_code=None`) | `:464–466` | `- X enum values: …` в порядке `values` | Сохраняется | Не передаётся |
| 10b | Промпт для раундов Workbench | `tools/factory_slice_workbench/service.py:213–232` (`build_prompt(local_spec, None)`) | Всегда запасной путь 10a | Сохраняется | Не передаётся |
| 11 | Кэш и повторное использование черновика | `tools/draft_acceptance.py:15–19` (`inputs`: sha256 local spec, промпта, system prompt, `models`), `:22–26` | Любое изменение `models.py` или local spec делает черновик невалидным | Перестановка → новый хеш | `ordered` → новый хеш local spec |
| 12 | Delta и affected-set | `tools/spec_data_reachability.py:15` (`DATA_ROOTS`), `:96–119` (`changed_data_addresses`: список — один адрес), `:244`, `:364`; `flow_artifacts.py:328–375` (`compute_spec_delta`) | Изменение даёт адрес `models.X.values` / `models.X.ordered`; резолвер находит модули-потребители | Учитывается | Учитывается |

**Важное расхождение (10 и 10b).** Боевой промпт генератора и промпт, который
задают раунды «Почемучки» (contradictions), выводят enum по-разному: по
алфавиту имён и в порядке `values` соответственно. Модель генератора порядка
`values` не видит вовсе. Этот факт не зависит от Q9-a, но значим для контракта
`data_closure`: раунд проверяет промпт, который отличается от боевого.

---

## 3. Таблица совместимости

| Компонент | Принимает `ordered`? | Отвергает `ordered` вне enum? | Отвергает не-bool? | Отвергает дубликаты `values`? | Сохраняет порядок? | Использует порядок как смысл? |
|---|---|---|---|---|---|---|
| WB `spec_projection_workbench._project` | Да, молча | Нет | Нет | Нет | Да | Нет |
| WB `model_surface_workbench` | Игнорирует | Нет | Нет | Нет | — | Нет |
| WB notes gate | Игнорирует | Нет | Нет | Нет | — | Нет |
| FA `validate_spec` | Игнорирует | Нет | Нет | Нет | — | Нет |
| FA `type_resolver` | Игнорирует | Нет | Нет | Нет | — | Нет |
| FA `normalize_spec` | Передаёт | — | — | — | Да | Нет |
| FA `build_local_spec` | Передаёт | — | — | — | Да | Нет |
| FA `generate_models_draft.emit_enum` | Игнорирует | Нет | Нет | Нет: создаёт алиас `OPEN_2` | Только без `members`, без `{NAME: value}` и без существующего `models.py` | Нет |
| FA `generate_agent` (боевой промпт) | Не выводит | — | — | — | **Нет**: сортировка по имени | Нет |
| FA `generate_agent` (запасной путь) | Не выводит | — | — | — | Да | Нет |
| FA `persistence_ir._enum_members` (`:1248–1258`), `http_router_ir._enum_members` (`:178–188`) | Игнорируют | — | — | — | Нет: множество | Нет |
| FA `data_code_seam` (`:324–334`, `:341–346`) | Игнорирует | — | — | — | Нет: множество | Нет |
| FA `assembly_agent_reproduce` (`:335–350`) | Игнорирует | — | — | — | Да, выводит `values` | Нет |
| FA `draft_acceptance` / `spec_data_reachability` | Учитывает как данные | — | — | — | Учитывает | Нет |

**`member_names`, явные имена и `StrEnum`.**

- `member_names` и `members` не описаны ни в одной копии `SPEC_STANDARD.md`:
  §5 в Workbench и Factory совпадает (`:315` — «перечисление с закрытым
  списком значений»).
- Их не используют ни Cabinet Kernel (`git grep member_names` по
  `origin/agent/cabinet-kernel` пуст), ни проекты в `code-factory/projects`.
- Они поддерживаются только эмиттером Factory (`:232–247`). При `ordered`
  формы 9a и 9c противоречат `values`.

---

## 4. Эксперименты

Все сценарии — на копии `global_spec.json` Cabinet Kernel; меняется только
`models.DisclosureClass`.

### 4.1 Эмиссия, промпт, delta (`exp.py`)

| Сценарий | Ошибки `validate_spec` / `type_resolver` | Эмиссия (`emit_enum`) | `list(Enum)` | Боевой промпт | Запасной промпт | `changed_data_addresses` |
|---|---|---|---|---|---|---|
| S0 без `ordered` | 0 / 0 | `open, OPEN, business_confidential, …` | `open, business_confidential, personal_data` | `BUSINESS_CONFIDENTIAL, OPEN, PERSONAL_DATA` | `'open', 'business_confidential', 'personal_data'` | `[]` |
| S1 `ordered: true` | 0 / 0 | как S0 | как S0 | как S0 | как S0 | `models.DisclosureClass.ordered` |
| S2 ordered + переставленные `values` | 0 / 0 | `personal_data, …, open` | `personal_data, business_confidential, open` | **как S0** (алфавит) | переставлен | `…ordered`, `…values` |
| S3 без `ordered`, переставлены | 0 / 0 | переставлен | переставлен | как S0 | переставлен | `…values` |
| N1 `ordered` на `Port` (не enum) | 0 / 0 | — | — | — | — | `models.Port.ordered` |
| N2 `ordered: "yes"` | 0 / 0 | как S0 | как S0 | как S0 | как S0 | `…ordered` |
| N3 `values: [open, open, personal_data]` | 0 / 0 | `open, OPEN, OPEN_2, personal_data, …` (молчаливый алиас) | `open, personal_data` | `OPEN, OPEN_2, PERSONAL_DATA` | `'open', 'open', 'personal_data'` | `…values` |
| M1 `member_names` списком | 0 / 0 | `OPEN, BUSINESS_CONFIDENTIAL, PERSONAL_DATA` (без строчных) | порядок `values` | алфавит | порядок `values` | `…member_names` |
| M2 `member_names` `{NAME: value}` в другом порядке | 0 / 0 | `PERSONAL_DATA, OPEN, BUSINESS_CONFIDENTIAL` | **`personal_data, open, business_confidential`** | алфавит | порядок `values` | `…member_names` |

### 4.2 Существующий `models.py` (`exp2.py`)

Сначала в порядке S0 эмитирован старый файл, затем `emit_enum` вызван со
спекой S2 и `runtime_enums` из этого файла. Результат:
`open, OPEN, business_confidential, …` — **порядок старого файла**,
перестановка потеряна. В Factory путь к старому файлу выводится всегда
(`generate_models_draft.py:802`), когда local spec лежит под `specs/` проекта и
`models.py` уже сгенерирован.

### 4.3 Affected-set (`exp2.py`)

`resolve_data_addresses` и `resolve_data_addresses_between` для
`models.DisclosureClass.values` и для `…ordered` дают одинаковое:
`changed_modules = [canonical_values, models, surface]`,
`unresolved_addresses = []`.

### 4.4 Полный путь Factory: normalize → slice → `build_prompt` (`exp3.py`)

Через `factory_slice_workbench.module_prompts`, Factory @ `391c41c`, 14
LLM-модулей:

| Переход | Изменённые промпты |
|---|---|
| S0 → S1 (`ordered: true`) | **0**: атрибут модели не виден |
| S1 → S2 (перестановка) | **13 из 14**: меняется одна строка `- DisclosureClass enum values: …` (запасной путь) |

Резолвер Factory считает затронутыми только 3 модуля (§4.3). В боевом пути
строка промпта не меняется (алфавит), но меняется sha256 `models.py`
(`draft_acceptance.inputs`), и черновики всех модулей с контекстом моделей
пересоздаются.

### 4.5 Workbench: проекция и gate (`exp4.py`)

В scratch-копии изменён `60_model_closure_domain.json` (после прогона
восстановлен):

| Сценарий | Блоки проекции | Результат в `global_spec` | Блоки notes gate |
|---|---|---|---|
| S1 | 0 | `{'kind': 'enum', 'values': […], 'ordered': True}` | 0 |
| N1 (`Port.ordered`) | 0 | `Port.ordered = True` | 0 |
| N2 (`'yes'`) | 0 | `'ordered': 'yes'` | 0 |
| N3 (дубликаты) | 0 | `['open', 'open', 'personal_data']` | 0 |

### 4.6 `StrEnum` и ранжирование (Python 3.13.16, эмиссия Factory)

- `max({OPEN, BUSINESS_CONFIDENTIAL})` → `open` (нормативно —
  `business_confidential`).
- `OPEN < BUSINESS_CONFIDENTIAL` → `False` (нормативно — `True`).
- `max(…, key=list(DisclosureClass).index)` → `business_confidential`.
- `DisclosureClass.open is DisclosureClass.OPEN` → `True`: алиасы не нарушают
  итерацию.

### 4.7 Базовые тесты (без изменений кода)

| Репозиторий | Тесты | Итог |
|---|---|---|
| Factory | `test_models_selected_draft_generator.py`, `test_type_resolver.py`, `test_spec_data_reachability.py`, `test_spec_standard_v2.py`, `test_models_import_smoke.py` | 86 passed, 2 skipped |
| Workbench | `tests/test_factory_slices.py` + тесты проекции и model surface | 41 passed |

---

## 5. Ответы на вопросы задания

1. **Валидаторы и нормализаторы.**
   - Workbench: `spec_projection_workbench._project`, `model_surface_workbench`,
     `notes_workbench.gate`.
   - Factory: `validate_spec`, `type_resolver`, `normalize_spec`,
     `build_local_spec`, `generate_models_draft` (`KNOWN_MODEL_KINDS`,
     `:25–27`).

   Ни один не валидирует форму enum (ключи, тип и уникальность `values`).
   `ordered` все принимают молча (§3).
2. **Путь.** См. §2.
3. **Сохранение порядка.** Порядок сохраняется до эмиссии. Он теряется в
   9a, 9c и 9e и в боевом промпте (10).
4. **Порядок как смысл.** Нигде в Factory. Как порядок сериализации — в
   эмиссии `models.py`, запасном промпте и `assembly_agent_reproduce`.
5. **Хеш, affected-set, кэш, регенерация.** Перестановка и `ordered` меняют
   адреса delta (§4.1, §4.3), sha256 local spec и `models.py`
   (`draft_acceptance`), поэтому черновики пересоздаются. Расхождение:
   affected-set резолвера (3 модуля) против изменённых промптов в
   Workbench-пути (13).
6. **`member_names` / `StrEnum`.** Совместимы только форма списком (9b) и
   форма `{value: NAME}` (9d). Формы `members` (9a) и `{NAME: value}` (9c)
   задают свой порядок.
7. **Helper ранжирования.** Нужен (§4.6). Модель, видящая `StrEnum`,
   естественно пишет `max(...)`, и это даёт неверный нормативный результат.
8. **Отказы валидатора.** Сегодня их нет. Требования — в §6.

---

## 6. Необходимые изменения (не реализованы)

### 6.1 Стандарт (решение владельца; `SPEC_STANDARD.md` не тронут)

- §5 models: `ordered` — необязательный bool только у `kind: enum`.
- Направление: первый член `values` — наименьший.
- Без `ordered` порядок `values` смысла не несёт.
- Указать, как упорядоченный enum ранжируется в коде (имя helper-а
  принадлежит эмиттеру, по аналогии с §15.5.1 о codec-helpers).

### 6.2 Factory

| Где | Что |
|---|---|
| `tools/type_resolver.py`, новая проверка рядом с `check_model_kinds` (`:374`), вызов из `validate_spec_types` (`:537`) | Отказывать:<br>• `ordered` у модели без `kind: enum`;<br>• `ordered` не `true` (или не bool — по решению владельца, §6.4);<br>• пустые `values`;<br>• не-строковые элементы;<br>• дубликаты `values`;<br>• при `ordered` — `members` или `member_names` в форме, задающей иной порядок (9a, 9c). |
| `tools/generate_models_draft.py:276–303`, `:250–264` | При `ordered` порядок брать только из `values`. Порядок `runtime_members_for_spec` разрешать лишь при совпадении **последовательности**, а не множества. Дубликат — отказ, а не алиас `_2`. |
| `tools/generate_models_draft.py` (`emit_enum`) | Для `ordered` эмитировать детерминированный способ ранжирования. Имя и форма — решение владельца, §6.4. |
| `tools/generate_agent.py:442`, `:464–466` | Для `ordered` выводить члены в порядке объявления с пометкой «ordered, lowest → highest» и именем helper-а. |
| `tools/validate_spec.py` (или проверка версии стандарта, §6.4) | Fail-closed для старых спецификаций и старой Factory |
| Тесты | `test_models_selected_draft_generator.py`, `test_type_resolver.py`, тест промпта для `ordered` |

### 6.3 Workbench

| Где | Что |
|---|---|
| Ранняя проверка model closure — новая проверка до проекции или внутри `_project`, `service.py:396–405` | Те же отказы, что в Factory: Workbench сейчас пропускает N1–N3 до сборки |
| `data_closure` | Правило M-E3 (`DATA_CLOSURE_RESEARCH_Q9_Q10_Q11.md`, §5.1):<br>• «declared order of = models.X» законно только при `ordered: true`;<br>• пересказ порядка рядом с адресом — `duplicated_data`;<br>• упорядоченный список без `ordered` — кандидат `missing_structure`. |
| `factory_slice_workbench.module_prompts` | Для раундов State 7 строить промпт с тем же контекстом моделей, что и боевой (`models_code`), иначе раунд проверяет другой текст (§2, 10/10b) |

### 6.4 Решения владельца

- Разрешать ли `ordered: false` или только `true`/отсутствие. Рекомендуется
  только `true`: тогда у одного смысла одна запись (§15.4).
- Форма ранжирования в коде:
  - (a) метод класса `rank(self) -> int`;
  - (b) модульная константа `X_ORDER: tuple[X, ...]`;
  - (c) `__lt__` на enum.

  Вариант (c) меняет строковое сравнение `StrEnum` везде, где оно уже
  используется, и не рекомендуется.
- Fail-closed против старой Factory:
  - повышение `standard_version` (старая Factory отказывает по
    `unsupported_standard_version`, `validate_spec.py:158`);
  - или проверка возможности Factory в Stage 9.

---

## 7. Риски обратной совместимости

| Риск | Откуда | Последствие |
|---|---|---|
| Старая Factory молча игнорирует `ordered` | §3: ни один валидатор его не знает | Код ранжирует по строкам, а спека считается «закрытой» |
| Перестановка `values` не доходит до `models.py` | 9e | Нормативный порядок меняется только в спеке |
| `member_names` / `members` задают другой порядок | 9a, 9c | Два источника порядка в одном объявлении |
| Боевой промпт показывает алфавит | 10 | Модель не узнаёт об упорядоченности, кроме как из notes |
| Появление `ordered` или перестановка пересоздают черновики всех модулей с контекстом моделей | 11 | Цена изменения выше affected-set резолвера (13 промптов против 3 модулей в Workbench-пути) |
| Существующие enum, на порядок которых опираются notes (`80_notes.md:119`, `:125`, `:226` Cabinet Kernel @ `b3bee2e`) | Q9 | После принятия решения они либо получат `ordered: true`, либо notes, опирающиеся на порядок, станут находками `data_closure` |
| Дубликаты `values` уже сейчас молча дают алиас | N3 | Новый отказ может сломать сборку спецификаций с такой ошибкой (в Cabinet Kernel их нет: 33 enum проверены) |

---

## 8. Рекомендация

**`ordered: true` достаточно как форма объявления.** Это необязательный bool
только у `kind: enum`, со значением только `true`. Другие формы хуже:

- `kind: ordered_enum` ломает закрытый реестр `KNOWN_MODEL_KINDS` в
  `type_resolver.py:36` и `generate_models_draft.py:25`. Это дало бы
  fail-closed против старой Factory, но дублирует ветвление всего кода
  `kind == "enum"` (десятки мест, §3).
- Отдельная карта рангов `{value: int}` вводит второй источник порядка
  рядом с `values` (против §15.4).
- Строковое `order: "ascending"` добавляет направление, но направление
  можно зафиксировать в стандарте один раз.

Однако **одной формы недостаточно**. До того как `data_closure` начнёт
опираться на `ordered`, нужны:

1. валидация в обоих репозиториях (§6.2, §6.3);
2. эмиссия, при которой `values` главнее существующего `models.py`;
3. сгенерированный эмиттером способ ранжирования;
4. явный вывод упорядоченности в боевой промпт;
5. fail-closed против Factory, не знающей атрибута.

Без пунктов 2–5 атрибут объявлял бы порядок, который не доходит до кода.
