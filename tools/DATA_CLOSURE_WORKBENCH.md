# Data Closure Workbench — контракт режима `data_closure` (Stage 7)

## Статус

Технический контракт этапа 11.1 плана «Stage 7 — Data Closure Assurance».
Кода режима ещё нет: документ фиксирует входы, схему находок, вердикты,
fail-closed условия, модель актуальности, инструменты, точки интеграции и
порядок закрытия **до** изменения промптов и маршрутизации Stage 7. Пока
контракт не реализован, он не является гейтом: `authoring.py next` и Stage 9
работают как раньше.

Все ссылки `файл:строка` даны по `origin/main` @ `9cde0aa`. Нормативная основа —
`skills/spec-authoring/SPEC_STANDARD.md` §15 (строки 1749–2334 в той же ревизии);
пункты цитируются номерами (`§15.3`, `§15.11`), стандарт этим документом не
меняется.

### Почему документ лежит здесь

`tools/<NAME>_WORKBENCH.md` — место, где репозиторий держит технические
контракты инструментов: схемы отчётов, коды находок, точки входа
(`tools/FACTORY_ADMISSION_WORKBENCH.md`, `tools/MODULE_REVIEW_WORKBENCH.md`,
`tools/VALUE_FLOW_WORKBENCH.md`). Контракт ещё не реализованной работы тоже
живёт здесь: `tools/RUNTIME_CLOSURE_WORKBENCH.md` начинается со «Status:
Proposed work». Методика «Почемучки» для оператора лежит в
`skills/spec-authoring/QUESTIONS.md`, и `authoring next` выдаёт её как
материал для чтения по фазам (`authoring_sequence.json`, поле `docs`). Туда этот
документ не кладётся: пока режима нет, правка `skills/` поменяла бы то, что
оператор читает уже сейчас. Раздел для оператора появится в `QUESTIONS.md` на
этапе 11.4 (авторский цикл). Документ не добавлен ни в один список `docs`
секвенсера. Оба пути (`tools/`, `skills/`) меняются только на `main` через ветку
`tools/*` (`AGENTS.md`, «Tool ownership»).

---

## 1. Нормативная база: пункты §15, на которые опирается режим

| Пункт | Что берёт режим |
|---|---|
| §15, вводная (стр. 1756–1781) | Четыре механизма: `derivation`, `placement`, `lowering`, `legacy recovery`. Без отдельной ячейки обходится только `derivation`, и только если результат доказуем из объявлений и версии backend (стр. 1778–1781). На этом основан вердикт `DERIVED`. |
| §15.1 (стр. 1785–1802) | В спеке только значения времени сборки. Иллюстративные значения запрещены. Значения внешней системы не попадают в спеку даже как примеры формата. Основание категории `illustrative_value` и проверок 1–2 процедуры §15.2. |
| §15.2 (стр. 1916–1939) | Ровно один дом. Процедура тотальна: неразмещённое значение — дефект, а не повод для прозы. Чем отличаются проверки 3/4 и 4/5. Основание категорий `missing_structure`, `missing_mapping`, `home_undecided`. |
| §15.3 (стр. 1943–1959) | Note обращается к данным только адресом. Воспроизводить содержимое блока в note запрещено. Ссылка резолвится и указывает на наименьший узел. Основание категорий `duplicated_data` и `invalid_reference`. |
| §15.3.1 (стр. 1961–1994) | Три законных пути значения к коду: `= models.*`, константа поставщика (`the imported X constant`), поле настроек. Какие `= rules.*` / `= config.*` законны. Адрес без `=` невалиден. По этим правилам проверяется вердикт `CLOSED`. |
| §15.4 (стр. 1999–2023) | Дублировать лист в двух домах запрещено. Если значения обязаны совпадать, у них один дом. Основание `duplicated_data`. |
| §15.5.1 (стр. 2071–2130) | Выводимые ограничения не повторяются, codec принадлежит backend-у. Основание `DERIVED` для storage-следствий. |
| §15.9 (стр. 2227–2259) | Модель не видит значений. Literal-check ловит протечку через notes. Fail-closed на обеих сторонах. |
| §15.10 (стр. 2263–2298) | `NOT_APPLICABLE` бывает только результатом выполненной процедуры. Неоднозначность не разрешается статистикой. Классы дефектов различаются в диагностике. Основание fail-closed правил и запрета «голосования» рецензентов. |
| §15.11 (стр. 2302–2333) | NOT-list. «inline-данные в notes: таблицы, пороги, allow-list, alias-словари, пути, ставки, коэффициенты» — дефект. «последовательность операций как значение спеки» запрещена, значит, алгоритмическая проза остаётся прозой. Отсюда граница `NOT_DATA`. |

---

## 2. Как «Почемучка» устроена сейчас

### 2.1 Раунд

- Вход в раунд — `service.ask_round(case, state, provider, runs, since, factory_root)`
  (`tools/questions_workbench/service.py:546`). Проект задаётся путём `case`:
  у раунда нет ни канонического ref, ни commit. В `summary.json` попадают только
  дайджесты текстов (`documents`, `service.py:587`); `ref` есть лишь у
  перенесённой closure (`service.py:309`).
- Раунд читает тексты (`state_texts`, `service.py:394–413`), открытые единицы
  (`units.closed`, `service.py:559–562`) и изменённые единицы (`_changed_units`,
  `service.py:563`), затем выполняет `_document_round` (States 0–6,
  `service.py:482–499`) или `_module_round` (State 7, `service.py:502–543`).
  Выбор делает строка `service.py:565`.
- Рецензия — это `_review` (`service.py:66–71`): один вызов провайдера, ответ
  JSON с обязательным `open_points` (`_json_object`, `service.py:49–53`).
  Ответ не в формате JSON останавливает раунд исключением, и раунд не
  записывается.
- Группировка выполняется LLM-вызовом `_group` с промптом `prompts.GROUP`
  (`service.py:74–104`, `prompts.py:89–95`). Пункт, который группировка
  потеряла, становится отдельной темой (`service.py:93–95`).
- State 7 разбирается по модулям: на каждый модуль `runs` рецензий
  (`service.py:520–522`), промпт `prompts.MODULE_ASK` (`prompts.py:50–67`)
  ищет только противоречия, обе цитаты дословно. Каждая тема судится, даже если
  её нашла одна рецензия (`service.py:531–533`).
- Scope состояния берётся из `authoring_sequence.json`, поле `question_scope`
  первой фазы с данным `semantic_state` (`documents.py:56–62`).

### 2.2 Единицы

- States 0–6: одна единица на решение `## Accepted decision Axx`, на каждую
  секцию уровня 2, на преамбулу документа, плюс `context`
  (`units.py:60–96`).
- State 7: одна единица на **генерируемый** модуль, её текст — промпт Фабрики
  (`units.module_units`, `units.py:99–104`). Модули, которые Фабрика эмитит без
  модели, отсекает сама Фабрика (`deterministic_emission_kind`,
  `tools/factory_slice_workbench/service.py:239–280`).
- Дайджест — sha256 текста единицы (`units.py:56–57`). Единица закрыта, если
  два последних раунда, которые её рецензировали, были для неё чистыми на
  том же дайджесте и дайджест с тех пор не менялся (`units.closed`,
  `units.py:137–145`). Блокирующая тема без названной единицы держит открытыми
  все единицы раунда (`units.blocked`, `units.py:148–157`).

### 2.3 Провайдер

- Протокол `Provider.complete(instruction, text)` (`provider.py:17–21`).
- `OpenAIProvider` ходит в Responses API к модели генератора (`provider.py:58–87`);
  файлы читать не умеет.
- `CodexCliProvider` запускает `codex exec` в пустом временном каталоге с
  `--sandbox read-only --ephemeral --ignore-user-config`
  (`provider.py:90–155`). Модели недоступны ни проектные файлы, ни правила,
  ни MCP. Единственное исключение — `complete_with_files`: файлы кладутся в
  `later/` (`LATER_DIR`, `provider.py:24`, `:120–137`), модель может их
  искать и читать, но больше ничего. Признак этой возможности —
  `reads_files = True` (`provider.py:105`).

### 2.4 Судья

- LLM-вызов `_judge` (`service.py:150–200`), промпт `prompts.JUDGE`
  (`prompts.py:105–129`).
- Механическая проверка `judge.check` (`judge.py:59–143`). Цитата ищется
  после нормализации (`_norm` убирает backticks и сжимает пробелы,
  `judge.py:34–38`), минимум 12 символов (`judge.py:41–43`). Если проверка
  свидетельства не прошла, суждение `blocking` (`judge.py:129–140`). Если
  судья ничего не ответил, тоже `blocking` (`judge.py:65–66`).
- На State 7 блокирует только `contradiction`, а `consequential_gap` лишь
  записывается (`judge.py:137–140`).
- Прецеденты: проверенные неблокирующие суждения трёх последних раундов,
  цитаты которых всё ещё находятся (`service.py:128–147`,
  `judge.precedent_holds`, `judge.py:46–56`).

### 2.5 История

- Раунды хранятся в `examples/<case>/questions/state<N>/round-<k>/`
  (`rounds_dir`, `_next_round`, `service.py:56–63`): файлы `review-*.json`,
  для State 7 ещё `prompts/<module>.txt` и `summary.json`
  (`service.py:569–610`).
- Схема сводки — `spec_workbench_question_round.v2` (`service.py:39`), поля
  перечислены в `service.py:582–603`.
- `status` (`service.py:627–665`) сравнивает текущие дайджесты с сохранёнными
  и выдаёт открытые и изменённые единицы и `closed_at`.

### 2.6 Проверка изменённых единиц

- `_changed_units` (`service.py:242–255`) находит текст, на котором единица
  закрывалась. Для State 7 это `prompts/<module>.txt` прошлых раундов
  (`service.py:219–225`), для остальных — история git
  (`service.py:226–239`). `units.change_regions` (`units.py:118–130`)
  возвращает diff и затронутые области.
- Рецензенту передаётся только diff (`prompts.MODULE_CHANGE`,
  `prompts.py:70–83`). Пункт, который цитирует неизменённый фрагмент вдали от
  изменения, откладывается (`_set_aside` / `_away_from_change`,
  `service.py:427–453`).

### 2.7 Маршрутизация

- Секвенсер: `_post_state5_step` доходит до `state7_notes` (детерминированный
  `notes_gate.coverage`), затем `decision_witness_resolution`, затем
  `state8_assembly` (`tools/design_authoring_next.py:566–597`). Поверх него
  `_question_gate` (`design_authoring_next.py:189–229`) проверяет каждую фазу
  с `question_scope`, которую цепочка уже прошла. Когда цепочка доходит до
  `state8_assembly`, State 7 проверяется по `service.status(project, 7)`.
- State 7 можно спросить только при собранном и синхронном `global_spec.json`
  (`_spec_out_of_sync`, `service.py:355–378`, отказ в `service.py:403–407`).
  Значит, на деле раунд contradictions выполняется после проекции Stage 8
  (`design_spec_projection.py --apply`), но до гейта `state8_assembly`. Текст
  отказа сам велит запустить проекцию.
- Stage 9: `FA019` (`tools/factory_admission_workbench/service.py:847–885`)
  перебирает `question_documents.question_states()` (`documents.py:65–69`) и
  требует, чтобы каждое состояние было закрыто.

### 2.8 Что режим переиспользует и что ему не подходит

| Механизм | Как с ним поступает `data_closure` |
|---|---|
| `Provider`, `CodexCliProvider.complete_with_files` | Переиспользуется. Нужен параметр каталога вместо зашитого `later/`, см. §10. |
| `_json_object`, `QuestionRoundError` | Переиспользуются как есть. |
| `_spec_out_of_sync`, `_prompts_of` | Переиспользуются: определяют актуальность спеки и множество LLM-модулей. |
| `units._digest`, `units.change_regions` | Переиспользуются для дайджестов и diff фрагментов. |
| `judge._norm` | Переиспользуется для поиска цитат. |
| `_review` (требует `open_points`) | Не подходит, у режима своя схема ответа (§5). |
| `_group` (LLM-группировка) | Не нужен. Находки привязаны к детерминированному `fragment_id` и группируются по нему без модели. |
| `units.closed` (две чистые рецензии) | Не применяется. Режим закрывается по доказанному охвату (§7), см. вопрос Q2. |
| `_precedents`, `judged_before` | Не применяются. Вердикт держится на свидетельствах с дайджестами, а не на прошлых суждениях (§8). |
| `_set_aside` по `unit` | Не применяется. Охват задаётся списком фрагментов, а не самоназванной единицей. |

---

## 3. Входы раунда (п. 6 плана)

| Вход | Откуда берётся сегодня | Что добавить |
|---|---|---|
| Идентификатор проекта, канонический ref | `python tools/workbench.py show <project>`. `authoring_pipeline.project_next` материализует ref (`tools/authoring_pipeline.py:55–84`). `ask_round` получает только `case: Path`. | Новые поля сводки `project` и `canonical_ref`; CLI принимает их из `workbench.py show --json`. |
| Commit / hash входов | `_git_out(case, ...)` (`service.py:208–210`); commit в сводке отсутствует. | Поле `commit` (`git rev-parse HEAD`) и `inputs_clean`: отслеживаемые файлы входов совпадают с `HEAD`. Иначе применяется правило DC-F1. |
| Модуль | Ключи `factory_slice_workbench.module_prompts` (`factory_slice_workbench/service.py:239–280`) через `service._prompts_of` (`service.py:381–391`). | Это же множество — эталон охвата (§7). Своего списка LLM-модулей Workbench не строит. |
| Применимые notes и их исходные строки | `notes_workbench.language.authored_notes` (`tools/notes_workbench/language.py:216–258`) выдаёт `path`, `line`, `scope`, `class`, `text` по всем `80_notes*.md`. Notes gate читает только `80_notes.md` (`notes_workbench/gate.py:312`). | Привязка `scope → module` (инструмент M6, §9). Фрагмент — одна authored note (§4). |
| Собранные notes | `_spec_out_of_sync` проверяет, что каждая note из `80_notes.md` есть в `global_spec.json` (`service.py:371–377`). | Ничего: проверка переиспользуется как fail-closed DC-F2. |
| Канонические `models` | `60_model_closure*.json` (корни моделей загружаются в `gate.py:103–112`), `models` в `global_spec.json`. | Индекс листов и членов перечислений (M1, M2). |
| Канонические `config`, `rules`, data closure | `60_data_closure.json`: секции `config`, `rules`, `persistence`, `properties`, `determinism` (`tools/design_stage6_data.py:28`), `placements` с `source_refs` (`design_stage6_data.py:136–249`); собранные блоки в `global_spec.json`. | Резолвер до листа (M1). |
| Контракты | `60_contracts.json`, `contracts` в `global_spec.json`; срез модуля виден в промпте Фабрики. | Сигнатуры функций модуля входят в дайджест единицы (§4). |
| Адреса deterministic backend-ов | `deterministic_backends(project)` и `backend.structured_addresses(project)` (`gate.py:113–114`, `tools/project_extensions.py`). Реестр — `tools/standard_backends.py:17,173`. | Нужен для `DERIVED`: идентификатор backend-а и его версия. |
| Нормативные требования §15 | `SPEC_STANDARD.md`, от `## 15.` до следующего `## ` (стр. 1749–2335). Навигация — `SPEC_STANDARD_INDEX.md`. | Текст раздела отдаётся рецензенту файлом; в сводку пишется `standard_15_sha256`. |
| Инструменты | Перечень в §9. | Результаты детерминированных инструментов собираются в пакет свидетельств (M7) и отдаются файлами. |
| Ранее проверенные единицы и изменения | Для contradictions: `questions/state7/round-*/summary.json` и `prompts/`. | Своя история `questions/state7_data_closure/` (§10). Зависимости каждого вердикта записываются с дайджестами (§8). |

---

## 4. Единица и фрагмент

**Единица** — один LLM-генерируемый модуль. Ключи единиц те же, что у
contradictions (`module_prompts`), поэтому охват обоих режимов сравним. Плюс
одна единица `global` для межмодульной проверки (п. 8 плана).

**Фрагмент** — одна authored note из `language.authored_notes`:

```text
fragment_id = "F:" + sha256(scope + "\x00" + note_class + "\x00" + normalized_text)[:16]
locations   = [{"source_file": path, "line": line}, ...]
```

Идентификатор не зависит от номера строки: перенос note между файлами или
вставка строк выше не меняют `fragment_id`, а смена текста меняет. Номер
строки хранится как место, но идентичностью не служит. Одинаковые notes в
нескольких файлах дают один фрагмент с несколькими местами.

**Входной дайджест единицы** — sha256 канонического JSON (ключи отсортированы,
UTF-8) из следующих частей:

```json
{
  "module": "<module>",
  "fragments": {"<fragment_id>": "<sha256 текста>"},
  "contracts": {"<name>": "<sha256 сигнатуры>"},
  "addresses": {"<адрес>": "<sha256 узла>"},
  "standard_15_sha256": "<sha256>",
  "tool_versions": {"<инструмент>": "<версия>"}
}
```

`addresses` — узлы, которые фрагменты модуля адресуют (`= …`, `the imported X
constant`, поле настроек), плюс узлы, на которые ссылаются вердикты прошлого
результата (§8).

---

## 5. Схема находки, вердикты, категории

### 5.1 Ответ рецензента

Рецензент обязан вернуть вердикт по **каждому** `fragment_id` из выданного
списка. Пропущенный фрагмент превращается в `UNRESOLVED / coverage_gap` (DC-F7).

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "spec_workbench_data_closure_review.v1",
  "type": "object",
  "required": ["fragments"],
  "additionalProperties": false,
  "properties": {
    "fragments": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["fragment_id", "findings"],
        "additionalProperties": false,
        "properties": {
          "fragment_id": {"type": "string", "pattern": "^F:[0-9a-f]{16}$"},
          "findings": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/finding"}}
        }
      }
    }
  },
  "$defs": {
    "finding": {
      "type": "object",
      "required": ["quote", "section", "category", "verdict", "evidence", "generation_consequence", "operator_action"],
      "additionalProperties": false,
      "properties": {
        "quote": {"type": "string", "minLength": 1},
        "section": {"enum": ["15", "15.1", "15.2", "15.3", "15.3.1", "15.4", "15.5.1", "15.9", "15.10", "15.11"]},
        "category": {"enum": ["addressed", "derived", "not_data", "missing_structure", "missing_mapping",
                               "duplicated_data", "invalid_reference", "illustrative_value", "home_undecided",
                               "coverage_gap", "evidence_failed"]},
        "verdict": {"enum": ["CLOSED", "DERIVED", "NOT_DATA", "DEFECT", "UNRESOLVED"]},
        "canonical_address": {"type": ["string", "null"]},
        "derived_from": {"type": "array", "items": {"type": "string"}},
        "backend": {"type": ["string", "null"]},
        "not_data_basis": {"enum": ["algorithm_step", "behaviour_condition", "explanation", "runtime_field", null]},
        "absence_claim": {
          "type": ["object", "null"],
          "required": ["terms", "namespaces"],
          "properties": {
            "terms": {"type": "array", "items": {"type": "string"}, "minItems": 1},
            "namespaces": {"type": "array", "items": {"enum": ["models", "config", "rules", "contracts"]}, "minItems": 1}
          }
        },
        "evidence": {"type": "array", "items": {"$ref": "#/$defs/evidence"}},
        "alternatives_checked": {"type": "array", "items": {
          "type": "object", "required": ["home", "why_rejected"],
          "properties": {"home": {"type": "string"}, "why_rejected": {"type": "string"}}}},
        "generation_consequence": {"type": "string"},
        "operator_action": {"type": "string"}
      }
    },
    "evidence": {
      "type": "object",
      "required": ["kind", "claim"],
      "properties": {
        "kind": {"enum": ["pack_file", "resolver", "value_index", "provenance", "structure"]},
        "path": {"type": "string"},
        "claim": {"type": "string"}
      }
    }
  }
}
```

### 5.2 Находка в сводке (после проверки)

Сервис дополняет находку полями, которые рецензенту не доверяются:

| Поле | Источник |
|---|---|
| `id` | `DC:<module>:<fragment_id>:<n>` |
| `module`, `fragment_id`, `source_file`, `line` | из списка фрагментов (§4) |
| `reviews` | номера рецензий, давших эту находку |
| `evidence_status` | `verified` / `failed` / `stale` (§6, §8) |
| `failure` | текст первой несработавшей проверки |
| `checked` | результаты инструментов с дайджестами: `{"resolver": {...}, "value_index": {...}, "absence": {"namespaces": {"rules": "<sha>"}, "hits": []}}` |
| `dependencies` | `{"addresses": {...}, "namespaces": {...}}` — на основе этого считается `STALE` |

### 5.3 Вердикты

| Вердикт | Значение (п. 6 плана) | Блокирует | Допустимые категории |
|---|---|---|---|
| `CLOSED` | Структура есть и адресована корректно | нет | `addressed` |
| `DERIVED` | Значение однозначно выводится из канонических объявлений и версии backend | нет | `derived` |
| `NOT_DATA` | Допустимая алгоритмическая или объяснительная проза | нет | `not_data` |
| `DEFECT` | Подтверждённое нарушение §15 | **да** | `missing_structure`, `missing_mapping`, `duplicated_data`, `invalid_reference`, `illustrative_value` |
| `UNRESOLVED` | Свидетельств недостаточно или нужно решение владельца | **да** | любая категория `DEFECT`, а также `home_undecided`, `coverage_gap`, `evidence_failed` |

Нарушение таблицы, например `CLOSED` с категорией `missing_structure`,
считается `evidence_failed`, и находка получает `UNRESOLVED`.

### 5.4 Категории

Закрытый список. Новая категория вводится только правкой этого контракта.

| Категория | Определение | Пункты §15 | Обязательное свидетельство |
|---|---|---|---|
| `addressed` | Фрагмент называет значение законным путём §15.3.1, и путь резолвится в существующий наименьший узел | §15.3, §15.3.1 | `canonical_address`; резолвер (M1) подтверждает узел и законность формы |
| `derived` | Технический факт следует из уже объявленных данных и версии backend; нового решения нет | §15 вводная (механизм 1, стр. 1778–1781), §15.5.1 | `derived_from` (резолвятся), `backend` (есть в реестре) |
| `not_data` | Проза описывает порядок шагов, условие поведения над адресованными данными, пояснение или runtime-поле модели; спека не должна держать это значение | §15.11 («последовательность операций как значение спеки»), §15.1 (runtime-значения) | `not_data_basis`; в цитате нет литерала, совпадающего с объявленным значением (M2) |
| `missing_structure` | Нормативное значение или закрытая форма (порог, путь, ставка, коэффициент, allow-list, список вариантов) записаны только прозой, дома нет | §15.2 (тотальность, проверки 0/3/4/5), §15.11 (inline-данные) | `absence_claim`, по которому поиск M4 пуст |
| `missing_mapping` | Закрытое соответствие `A × B → C` (таблица, alias-словарь, маршрутизация по ключу) записано прозой, без `mapping`/`catalog` или таблицы `rules` | §15.2 проверка 5, §15.11 (таблицы, alias-словари) | `absence_claim` по ключам соответствия; поиск M4 пуст |
| `duplicated_data` | Значение или форма уже имеют дом, и фрагмент воспроизводит содержимое вместо адреса | §15.3 («Воспроизведение содержимого блока данных внутри note запрещено»), §15.4 (дублирование листа), §15.9 (literal-check) | `canonical_address`; M2 находит совпадение литерала из цитаты со значением узла |
| `invalid_reference` | Адрес не резолвится, указывает на родителя вместо листа, использует незаконный `= rules.*`/`= config.*` или записан без `=` | §15.3, §15.3.1 | Отказ резолвера M1 или нарушение формы по §15.3.1 |
| `illustrative_value` | Пример значения, runtime-экземпляр или значение внешней системы в прозе | §15.1, §15.11 (иллюстративные значения) | Цитата содержит литерал; `not_data_basis` к нему неприменим |
| `home_undecided` | Значение нормативно, но выбор дома требует решения владельца (проверки 3/4 или 4/5 §15.2 не различаются по тексту) | §15.2 (различение 3/4, 4/5), §15.10 («Неоднозначность не разрешается статистикой») | `alternatives_checked` содержит не меньше двух домов |
| `coverage_gap` | Ставится сервисом: фрагмент без вердикта или сигнал M3 без находки | §15.10 (`NOT_APPLICABLE` только по итогам выполненной процедуры) | — |
| `evidence_failed` | Ставится сервисом: механическая проверка не прошла | §15 вводная («нарушение является ошибкой валидации») | — |

---

## 6. Судья: что проверяется механически, а что — моделью

### 6.1 Механическая проверка

Механическая проверка — отдельная функция; `judge.check` не меняется (§10).
Каждая находка проходит её до того, как вердикт засчитывается:

1. **Цитата.** После `judge._norm` цитата найдена в тексте **своего**
   фрагмента. Порог в 12 символов (`judge.py:41–43`) здесь не нужен: цитата
   ищется внутри одного фрагмента, а не во всём корпусе.
2. **Таблица вердикт × категория** (§5.3).
3. **`CLOSED`.** Резолвер M1 находит `canonical_address`, узел — наименьший
   из потребляемых (§15.3), форма законна по §15.3.1, а цитата содержит этот
   адрес или имя символа поставщика.
4. **`DERIVED`.** Каждый адрес из `derived_from` резолвится, `backend` есть в
   `standard_backends` или в `deterministic_backends(project)`.
5. **`NOT_DATA`.** `not_data_basis` задан. M2 не нашёл в цитате литерала,
   равного объявленному значению. Если нашёл, вердикт отвергается: это
   свидетельство `duplicated_data`.
6. **`DEFECT/duplicated_data`.** M2 подтверждает совпадение литерала из цитаты
   со значением `canonical_address`.
7. **`DEFECT/missing_*`.** Поиск M4 по `absence_claim` пуст. В `checked`
   записываются дайджесты просмотренных пространств имён.
8. **`DEFECT/invalid_reference`.** Резолвер M1 действительно отказывает, или
   форма действительно нарушает §15.3.1.

Если проверка не прошла, находка становится `UNRESOLVED / evidence_failed` с
полем `failure` и блокирует. Так же устроен `judge.check`, где непрошедшее
свидетельство превращается в `blocking`.

### 6.2 LLM-судья

Модель вызывается только там, где механика бессильна:

- рецензии разошлись по вердикту одного фрагмента;
- `NOT_DATA` или `DERIVED` выставлены фрагменту, в котором M3 нашёл сигнал
  данных;
- `UNRESOLVED`, которое рецензент не обосновал полем `alternatives_checked`.

Судья отвечает по той же схеме (§5.1) и проходит ту же механическую проверку.
Судья не может снять механически подтверждённый `DEFECT`.

### 6.3 Сведение рецензий по фрагменту

Правило следует из принципа 5 плана и §15.10: «алгоритм не голосует».

1. Есть хотя бы один `verified` `DEFECT` → `DEFECT`.
2. Иначе есть `UNRESOLVED`, непрошедшая проверка или расхождение, которое
   судья не снял → `UNRESOLVED`.
3. Иначе все рецензии и судья дали проверенный неблокирующий вердикт →
   этот вердикт. Расхождение между `CLOSED` и `NOT_DATA` решает судья.

Согласие двух рецензентов не требуется ни для дефекта, ни для закрытия
(вопрос Q2).

---

## 7. Fail-closed условия и правило «нет доказанного охвата → нет PASS»

### 7.1 Раунд не выполняется и ничего не пишет

| Код | Условие |
|---|---|
| DC-F1 | Отслеживаемые файлы входов отличаются от `HEAD`, или материализованный ref не совпадает с каноническим (`AGENTS.md`, «Where the work lives»). |
| DC-F2 | `global_spec.json` не собран или не синхронен (`_spec_out_of_sync`, `service.py:355–378`). |
| DC-F3 | Нет Фабрики, или Фабрика отказывается строить срезы (`_prompts_of`, `service.py:381–391`). Множество модулей неизвестно, значит, охват недоказуем. |
| DC-F4 | Провайдер не умеет читать файлы (`reads_files` отсутствует). Пакет свидетельств передать нельзя (вопрос Q4). |
| DC-F5 | В `SPEC_STANDARD.md` нет раздела `## 15.` или не читается файл входа. |
| DC-F6 | Ответ модели не JSON или нарушает схему §5.1 (`_json_object`, `service.py:49–53`). |

### 7.2 Раунд пишется, но вердикт блокирующий

| Код | Условие | Итог |
|---|---|---|
| DC-F7 | Фрагмент не получил вердикта ни в одной рецензии | `UNRESOLVED / coverage_gap` |
| DC-F8 | Сигнал данных M3 в фрагменте не закрыт ни одной находкой, цитирующей его | `UNRESOLVED / coverage_gap` |
| DC-F9 | Механическая проверка §6.1 не прошла | `UNRESOLVED / evidence_failed` |
| DC-F10 | Нужный инструмент недоступен или вернул ошибку | `UNRESOLVED / evidence_failed`: без резолвера нет `CLOSED`, без M4 нет доказательства отсутствия |
| DC-F11 | Неизвестный вердикт или категория | `UNRESOLVED / evidence_failed` |
| DC-F12 | Судья не ответил по фрагменту, где он обязателен (§6.2) | `UNRESOLVED / evidence_failed` |
| DC-F13 | Note с `scope`, который не принадлежит ни LLM-модулю, ни детерминированному модулю | `UNRESOLVED / coverage_gap` в единице `global` |

### 7.3 PASS

- **Единица** проходит, если выполнены все условия:
  1. множество фрагментов её модуля совпадает с выданным рецензентам;
  2. каждому фрагменту выставлен итоговый вердикт;
  3. каждый сигнал M3 покрыт находкой;
  4. все итоговые вердикты из `{CLOSED, DERIVED, NOT_DATA}` и все `verified`;
  5. ни одна зависимость не `STALE` (§8).
- **Модуль без notes.** Результат «фрагментов 0» допустим только как итог
  выполненной процедуры (§15.10): в сводке записаны модуль, его контракты и
  пустой список фрагментов. Отказ «нечего спрашивать», как в `service.py:562`,
  здесь недопустим: модуль присутствует в результате.
- **Режим** проходит, если множество единиц равно `set(module_prompts)`
  текущей спеки, каждая единица проходит и проходит единица `global`.
  Отсутствие находок без выполненных пунктов 1–3 — не PASS (принцип 4 плана).

---

## 8. Модель актуальности: `STALE` и affected-set

### 8.1 Что делает результат `STALE`

Результат — это находка, единица или режим. Он `STALE`, если пересчитанное на
текущем дереве значение хотя бы одной записанной зависимости отличается от
сохранённого:

| Зависимость | Чей результат устаревает |
|---|---|
| sha256 текста фрагмента | этого фрагмента |
| sha256 узла `canonical_address` или адреса из `derived_from` | находок, которые на него ссылаются |
| sha256 пространства имён, просмотренного доказательством отсутствия (`checked.absence.namespaces`) | находок `missing_*` и `NOT_DATA`, опиравшихся на это пространство |
| sha256 сигнатуры контракта модуля | всех фрагментов модуля |
| `standard_15_sha256` | всех результатов режима |
| версия инструмента (M1–M5) | всех результатов, которые он подтверждал |
| множество `module_prompts` | режима: охват пересчитывается |
| `commit` и `canonical_ref` | ничьих по отдельности: это метка происхождения, актуальность решают дайджесты |

`STALE` никогда не даёт PASS (п. 12 плана). Устаревший `CLOSED` по смыслу
равен «не проверено».

### 8.2 Как считается affected-set

Affected-set считается на **текущих** единицах, а не на тех, что были
сохранены:

1. Строятся текущие единицы и фрагменты (§4).
2. Для каждого фрагмента берётся последний итоговый вердикт с тем же
   `fragment_id` из `questions/state7_data_closure/round-*/summary.json`.
3. Фрагмент попадает в affected-set, если для него нет вердикта (новый или
   изменённый текст), если любая зависимость его вердикта `STALE` или если
   его вердикт блокирующий.
4. Единица открыта, если в affected-set есть хотя бы один её фрагмент. Единица
   `global` открыта при любом изменении любой единицы или любого блока данных.
5. Следующий раунд рецензирует только фрагменты из affected-set, но получает
   весь модуль как контекст. Изменённый фрагмент сопровождается diff от
   прошлого текста (`units.change_regions`). Для этого рядом с раундом
   сохраняются тексты фрагментов (`fragments/<fragment_id>.txt`), как
   `prompts/` у contradictions (`service.py:575–579`).

Правка одного листа `rules` устаревает только находки, ссылавшиеся на этот
лист, и доказательства отсутствия по `rules`. Доказательство отсутствия
зависит от всего пространства имён: появление нового правила может закрыть
`missing_structure`, и пропустить это нельзя. Пересчитывается только такой
фрагмент, а не весь проект.

---

## 9. Read-only инструменты

Все инструменты только читают. Ни один не пишет в notes, модели, правила или
контракты. Рецензенту они доступны только как файлы пакета свидетельств:
`codex exec` выполняется без MCP и вне репозитория (`provider.py:96–99`).

### 9.1 Что уже есть

| Инструмент | Что даёт | Ограничение для режима |
|---|---|---|
| `notes_workbench.language.authored_notes` (`language.py:216–258`) | Фрагменты с `path:line` из всех `80_notes*.md` | — |
| `notes_workbench.gate`: `ADDRESS_RE`, `BARE_DATA_ADDRESS_RE`, `POSITIONAL_ADDRESS_RE` (`gate.py:25–30`), `_load_structured_addresses` (`gate.py:88–114`) | Синтаксис адресов, известные корни | `_address_resolves` принимает любого потомка известного адреса (`gate.py:296–299`); модели известны только на уровне корня (`gate.py:103–112`). Для `CLOSED` этого мало. |
| `design_stage6_data` (`design_stage6_data.py:28, 136–249`) | `placements` с `source_refs`: provenance структурированных значений | Проверяет связь «лист → обоснование», но не «значение в прозе → лист» |
| `workbench_mcp.service.provenance` / `design_context` / `closure` (`tools/workbench_mcp/service.py:168–236, 292–302, 247`) | Всё, что корпус говорит об имени: решения, места, waivers, notes | Работает как MCP-инструмент, Codex-рецензенту недоступен; сервис должен вызвать его сам и положить результат в пакет |
| `design_index` (`find_mentions_in_items`, `get_item`, `context_at`; `tools/design_index.py:180–285`) | Навигация по корпусу | — |
| `design_closure_gaps`: `prose_closure_leak` (`tools/design_closure_gaps.py:182`) | Перечисление закрытых значений в прозе поля State 1 | Только State 1 и только для полей не-enum типа |
| `design_field_closure` | Ссылки на атрибуты из notes против объявленных поверхностей | Проверяет форму, а не данные |
| `factory_slice_workbench.module_prompts` / `probe` (`factory_slice_workbench/service.py:239, 283–383`) | Множество LLM-модулей; Фабрика ловит значения в контексте модели (`data_in_model_context`) | Работает через Фабрику; ловит только то, что уже попало в срез |
| `standard_backends` (`tools/standard_backends.py:17, 173`), `project_extensions.deterministic_backends` | Реестр backend-ов и их версий для `DERIVED` | — |
| `tools/semantic_lint.py` S3 | Разрешение `config.*`/`rules.*`/`models.*` в ограниченной грамматике | Экспериментальный, не канонический; на него опираться нельзя |

### 9.2 Чего не хватает

| # | Инструмент | Зачем | Основание |
|---|---|---|---|
| M1 | Резолвер листов по собранной спеке: адрес → узел, вид (лист или поддерево), канонический JSON узла, sha256; проверка наименьшего узла и законности формы по §15.3.1 | `CLOSED`, `invalid_reference`, зависимости §8 | §15.3 требует строить таблицу достижимости «тем же resolver, что и таблицу происхождения типов». Своего такого резолвера у Workbench нет (вопрос Q5). |
| M2 | Индекс значений: нормализованный литерал → адреса (строки, числа, строки фиксированной точности `"21.00"`, члены перечислений). Имена полей моделей и имена контрактов значениями не считаются: note законно называет поля формы (`[FIELD_ASSIGNMENT]`, `[RETURN_SHAPE]`) | `duplicated_data`, опровержение ложного `NOT_DATA` | §15.9 literal-check; у Фабрики `note_data_literal_leak` ловит только строки и только после экспорта (`tools/standard_matrix/standard_gate_matrix.json`, §15.11) |
| M3 | Детектор сигналов данных во фрагменте: числа, строки в кавычках, пути, перечисления от трёх идентификаторов, члены перечислений, стрелки соответствий, табличная разметка | Обязательства охвата (DC-F8). Сигнал — не вердикт. | §15.11 (inline-данные) |
| M4 | Поиск отсутствия: термины → совпадения ключей и значений в `models`/`config`/`rules`/`contracts` + sha256 просмотренных пространств | Доказательство `missing_*` и зависимости §8 | §15.2 (тотальность) |
| M5 | Проверщик свидетельств — аналог `judge.check` для §6.1 | Механический судья | Принцип «недоказанный PASS запрещён» |
| M6 | Привязка `scope note → module` по `module_functions` и `contracts` собранной спеки | Делит фрагменты по единицам, DC-F13 | `note_parser.parse(project, module_symbols, module_name)` (`tools/notes_workbench/note_parser.py:10`) делает это для одного модуля; нужна полная таблица |
| M7 | Сборщик пакета свидетельств: фрагменты, §15, срезы блоков по модулю, выводы M1–M4, provenance | Передача рецензенту через `complete_with_files` | `provider.py:120–137` |

---

## 10. Точки интеграции и изоляция `contradictions`

### 10.1 Где появляется режим

| Место | Изменение (этап 11.2+) |
|---|---|
| `tools/design_questions.py` (`main`, стр. 60–99) | `ask`/`status` получают `--mode {contradictions,data_closure}`, по умолчанию `contradictions`. `data_closure` допустим только с `--state 7`. |
| `service.rounds_dir` (`service.py:56–57`) | Параметр `mode="contradictions"`. Для `data_closure` каталог `questions/state7_data_closure/`, соседний с `questions/state7/`, а не вложенный в него. |
| Новый модуль `tools/questions_workbench/data_closure.py` | `ask_data_closure_round(case, provider, runs, factory_root, *, scope="module"|"global")` и `data_closure_status(case, factory_root)`. Своя схема сводки `spec_workbench_data_closure_round.v1`. Переиспользует только функции из §2.8. |
| `units.py` | Новая функция `data_closure_units(...)` (§4). `module_units`, `closed` и `blocked` не меняются. |
| `judge.py` | Новая функция `check_data_closure(finding, fragment, pack)` (§6.1). `check`, `KINDS` и `BLOCKING` не меняются. |
| `prompts.py` | Новые константы `DATA_CLOSURE_ASK`, `DATA_CLOSURE_JUDGE`. `ASK`, `MODULE_ASK`, `JUDGE`, `GROUP` не меняются. |
| `provider.py` | `CodexCliProvider.complete_with_files(..., directory=LATER_DIR)`: имя каталога становится параметром со старым значением по умолчанию. |
| `skills/spec-authoring/authoring_sequence.json` | Новая фаза `state7_data_closure` (§11) **без** ключа `question_scope`. Scope режима — в отдельном ключе `data_closure_scope`. |
| `tools/design_authoring_next.py` | Новая функция `_data_closure_gate`, которая вызывается рядом с `_question_gate` (`next_step`, стр. 175–186). `_question_gate` не меняется. |
| `tools/factory_admission_workbench/service.py` | Новая проверка `FA020` рядом с `_question_rounds_check` (стр. 1095). `FA019` не меняется. |

### 10.2 Почему `contradictions` не затрагивается

1. **История.** Все чтения истории contradictions идут через
   `rounds_dir(case, 7)`, то есть `questions/state7/`: `_next_round`,
   `_precedents`, `_summaries`, `_unit_text_at`, `_carried`, `_closed_at`
   (`service.py:60–63, 128–147, 203–205, 219–225, 314–343, 614–624`), и
   везде глоб `round-*`. Режим пишет в `questions/state7_data_closure/`,
   который этот глоб не захватывает. Прецеденты и closure contradictions не
   видят находок `data_closure`, и наоборот.
2. **Scope.** `documents.question_scope(7)` возвращает `question_scope`
   **первой** фазы с `semantic_state == 7` (`documents.py:59–61`). Если новая
   фаза получит `question_scope` и встанет раньше `state7_notes`, scope
   промпта `MODULE_ASK` молча сменится. Поэтому `question_scope` у неё запрещён.
   Это же защищает `question_states()` (`documents.py:65–69`), а значит, и
   `FA019`: туда не попадёт второй State 7.
3. **Промпты и судья.** Режим добавляет новые имена и не меняет существующие
   (§10.1). `judge.check` остаётся единственным проверяющим contradictions,
   включая правило «на State 7 блокирует только `contradiction`»
   (`judge.py:137–140`).
4. **Единицы.** `module_units` и `units.closed` не меняются, дайджест единицы
   contradictions по-прежнему считается от промпта Фабрики.
5. **Регрессии.** Тесты contradictions должны остаться зелёными без правок:
   `tests/test_design_questions.py`, `tests/test_design_questions_gates.py`
   (в том числе `:241`, `:255`, `:276`, `:314`, `:330`, `:341`, `:371–422`),
   `tests/test_design_questions_units.py`. На `9cde0aa` они проходят: 85
   passed. Этап 11.2 добавляет тесты: раунд `data_closure` не создаёт и не
   меняет файлов в `questions/state7/`; `question_scope(7)` до и после
   совпадают; `FA019` на фикстуре даёт тот же результат.

---

## 11. Порядок закрытия Stage 7 в текущем секвенсере (п. 9 плана)

Текущая цепочка после State 5: `… → deterministic_backend_binding →
state7_notes → decision_witness_resolution → state8_assembly`
(`design_authoring_next.py:566–597`). Contradictions de facto выполняются
между проекцией Stage 8 и гейтом `state8_assembly` (§2.7).

| Шаг плана | Где в секвенсере | Чем проверяется |
|---|---|---|
| 1. Подготовка и авторство notes | `state7_notes`. Установка §15 уже входит в `docs` фазы (§2, §15.3.1, §15.9 в `authoring_sequence.json`). | `notes_gate.coverage` (без изменений) |
| 2. Локальный `data_closure`, исправление, повтор | Новая фаза `state7_data_closure` **после** `state7_notes`. Требует собранной синхронной спеки (DC-F2), поэтому, как contradictions, выполняется после `design_spec_projection.py --apply`. | `data_closure_status`: все единицы модулей проходят |
| 3. Глобальный `data_closure` | Та же фаза, единица `global` | Единица `global` проходит |
| 4. Детерминированная согласованность и актуальность структур | Существующие гейты: `design_stage6_data`, `notes_gate`, проекция в синхроне (`_spec_out_of_sync`) | Без изменений |
| 5. `contradictions` на актуальных промптах | `_question_gate` для State 7 (без изменений) | `service.status(project, 7)` |
| 6. Согласованность версий и статусов режимов | `_data_closure_gate` при достижении `state8_assembly` | Оба статуса не `STALE` на одном `commit`, и оба вычислены от одного sha256 `global_spec.json` |
| 7. Stage 7 Closure | Переход к `decision_witness_resolution` / `state8_assembly`. На Stage 9 — `FA019` и `FA020`. | Оба режима закрыты, устаревших свидетельств нет |

Порядок «сначала `data_closure`, затем `contradictions`» задаётся так:
`_data_closure_gate` вызывается в `next_step` **перед** `_question_gate`.
Пока `data_closure` открыт, шаг указывает на него, даже если contradictions
тоже открыты. Правка notes по итогам `data_closure` меняет промпты, а значит,
снова открывает соответствующие модули contradictions. Это ожидаемо: так
работает существующая модель изменённых единиц.

---

## 12. План регрессий на кандидатах Cabinet Kernel (п. 10 плана)

### 12.1 Источник

- Ref: `origin/agent/cabinet-kernel` @ `b3bee2e`. Файлы читались только через
  `git show` и `git grep`, без checkout поверх рабочей ветки и без правок.
- Проект: `examples/cabinet-kernel/`. Все notes — в одном файле `80_notes.md`
  (507 notes, секции `## <module>`). Префикс note — голое имя функции:
  `page_records: [BEHAVIOR] …`.
- Список notes в `global_spec.json` поэлементно совпадает со строками notes в
  `80_notes.md`.
- Все четыре модуля генерирует модель: `81_module_review_status.json` →
  `generation_mode: "llm_behavioral"` (`canonical_values` стр. 63,
  `sandbox_runner` стр. 105, `store` стр. 119, `surface` стр. 273). Для
  регрессии единицы всё равно берутся из `module_prompts` (§3).
- Ни в одной из 63 сводок `questions/state7/round-*/summary.json` слова
  `data_closure` нет.

Канонический адрес ниже — адрес в смысле §15.3/§15.3.1: `= models.<Name>`,
символ поставщика, контракт. Если адреса нет, это написано прямо. Вердиктов
раздел **не выносит**: для каждого кандидата перечислено, что режим обязан
проверить, какие исходы контракт допускает и какой исход был бы ошибкой
самого режима. Окончательный вердикт возможен только после реализации
инструментов M1–M4 и решений по §13.

### 12.2 `store.page_records` — соответствие `RecordType × FilterField → StoreRepository`

**Фрагменты:** `80_notes.md:145`, `80_notes.md:147` (модуль `store`). Полная
таблица пар находится у вызывающего: `handle_list_records`,
`80_notes.md:595` (модуль `surface`).

> `80_notes.md:145` — "page_records: [BEHAVIOR] MUST read the rows of
> record_type in store order through StoreRepository and never ask the
> database for a limit, a range or a set condition: with no filter the type's
> whole list (list_slot_rows for slots, list_run_rows for runs, and so for each
> of the fourteen types list_records lists, decision 20 — activation,
> flow_activation, stored_value and spooled_file are never paged, …"

> `80_notes.md:147` — "… which is a position for which the type's find
> operation at that position (find_run_row_at_position for runs, and so for
> each of the fourteen paged types) answers no row, …"

> `80_notes.md:595` — "handle_list_records: [VALIDATION_ERROR] MUST refuse as
> invalid_request, before any read: a record_type that is not listable —
> activation, flow_activation, stored_value or spooled_file; a filter on a
> field not allowed for its type — none for slot and flow, …"

**Канонические адреса, которые есть:**

- `= models.RecordType` (`60_model_closure_operations.json:62`);
- `= models.FilterField` (`60_model_closure_operations.json:93`);
- `ShownRecords` — 14 полей, структурная форма «четырнадцати типов»;
- контракт `page_records` (`60_contracts.json:14`);
- методы `SqliteStoreRepository` в IR `rules.persistence_backend`
  (`70_persistence_closure.json`, например `list_slot_rows` стр. 1186,
  `list_run_rows_by_status` стр. 2297).

**Чего не найдено:** `mapping`/`catalog` или листа `rules`, который задаёт
допустимые пары `RecordType × FilterField`, соответствие тип → метод
репозитория или тип → перечисление статусов. Размещения в
`60_data_closure.json` нет. Таблица в прозе продублирована в
`50_public_apis.md:361–374`.

**Что режим обязан проверить:**

- Есть ли адрес, по которому таблицу можно разыменовать. M4 ищет по
  терминам `RecordType`, `FilterField`, `list_*_rows*`.
- Выводимо ли соответствие тип → метод. Имена неоднородны:
  `binding → operation_binding_rows`, `approval → effect_approval_rows`,
  `executed_implementation → executed_implementation_id`.
- Межмодульный повтор `:595` ↔ `:145`/`:147` — работа единицы `global`.

**Допустимые исходы:**

- `DEFECT/missing_mapping`;
- `UNRESOLVED/home_undecided`;
- `DERIVED` — только если Q6 разрешит вывод из IR без backend-правила, и
  только с `derived_from`, который резолвится.

**Ошибка режима:** `CLOSED` для таблицы пар. Адреса такой таблицы нет,
поэтому проверка M1 обязана его отвергнуть.

**Прошлые раунды contradictions:** `round-01 store:T1` («Allowed
record-type/filter combinations and repository mappings») судом признан
`consequential_gap`, blocking. Закрылся ли он позже, не проверено.

### 12.3 `sandbox_runner.read_runner_report` — закрытая форма wire-сообщений

**Фрагменты:** `80_notes.md:212`, `80_notes.md:213`. Сторона писателя —
`runner_source`, `80_notes.md:204–210`.

> `80_notes.md:212` — "read_runner_report: [BEHAVIOR] The program writes each
> message as one line of UTF-8 JSON ended by a newline, an object whose kind
> is trap (with the trapped name), resource, crashed (with failure, the
> exception's type and message or null) or returned (with is_dict and
> outputs, each port, form, json_text and contents, the bytes
> base64-encoded). read_runner_report MUST decode the lines in order: …"

> `80_notes.md:213` — "read_runner_report: [RETURN_SHAPE] Returns
> RunnerReport with trap_hits, resource_hit, crashed, failure and returned
> (None when no complete returned line was read), each ReturnedOutput's
> json_text set only for form json and contents holding the file's bytes, …"

**Канонические адреса, которые есть:**

- `= models.ReturnedForm` (`60_model_closure_operations.json:1761`);
- `ReturnedOutput` (стр. 1770), `RunnerReturn` (1779), `RunnerReport` (1786);
- контракт `read_runner_report: (message: bytes) -> RunnerReport`
  (`60_contracts.json:12`).

**Чего не найдено:** модели или перечисления `kind` сообщения
(`trap`/`resource`/`crashed`/`returned`), набора полей каждого вида и
кадрирования строк.

**Что режим обязан проверить:**

- Закрытый набор видов сообщения существует только в прозе: проверки 0/5
  §15.2. Протокол внутренний, между двумя функциями одного модуля, поэтому
  исход зависит от Q8.
- Значения `ReturnedForm` в `:213` названы голыми словами (`form json`), без
  `= models.ReturnedForm`. Это правило §15.3.1 или условие поведения — см. Q9.
- Имена полей `RunnerReport` в `:213` — это имена полей формы, а не значения.
  M2 не должен считать их дублированием (§9, M2).
- Политика декодирования («ends the decoding and what follows is ignored») —
  кандидат на `NOT_DATA/algorithm_step` внутри того же фрагмента. Итог
  фрагмента — худший из его находок (§6.3).

**Допустимые исходы для видов сообщения:** `DEFECT/missing_structure` или
`UNRESOLVED/home_undecided`.

**Ошибка режима:** `NOT_DATA` для всего фрагмента `:212`. Сигналы M3 (четыре
вида в перечислении) тогда остались бы непокрытыми (DC-F8).

**Прошлые раунды:** раундов о форме wire-сообщений нет; `round-50
sandbox_runner:T1` касается другого вопроса.

### 12.4 `surface.answer_request` — повторённый реестр 30 обработчиков и однозначность маршрутизации

**Приоритетный кандидат.** Фрагменты: `80_notes.md:481` (таблица акторов),
`:484` (реестр обработчиков), `:487` (порядок каталога), `:490` (коды
JSON-RPC).

> `80_notes.md:484` — "answer_request: [ORCHESTRATION] MUST call the handler
> of the named operation, whose name is handle_ followed by the operation
> name — exactly one of handle_accept_binding, handle_activate_flow_version,
> handle_add_trial_case, handle_cancel_run, handle_capture_…"

> `80_notes.md:481` — "answer_request: [SECURITY_BOUNDARY] Actor table, the
> only one: owner only — accept_binding, decide_effect_approval,
> resolve_unknown_outcome, cancel_run, grant_standing_approval,
> revoke_standing_approval, read_spooled_file, read_fixture_file; …"

> `80_notes.md:487` — "answer_request: [FIELD_PROJECTION] tools/list lists
> one tool per catalogue operation in State 5 catalogue order, …"

> `80_notes.md:490` — "… a body over the size ceiling is -32600
> invalid_request; …"

**Канонические адреса, которые есть:**

- 30 контрактов `handle_*` (`60_contracts.json:93–122`);
- `answer_request` (`60_contracts.json:89`);
- `the imported RELEASE_CEILING_* constant`, `MCP_*`
  (`70_data_provider_closure.json`, например стр. 51, 86, 126).

**Чего не найдено:**

- перечисления операций каталога;
- соответствия операция → класс актора;
- константы порядка каталога;
- констант кодов JSON-RPC;
- router IR (`60_contract_plan.json:3`: «no operation is externally exposed
  through the HTTP router»).

Каталог с колонкой актора лежит прозой в `50_public_apis.md:310–347`, а этот
документ не входит в `global_spec.json`.

**Что режим обязан проверить:**

- Список в `:484` поимённо совпадает с 30 ключами `handle_*` контрактов.
  Проверено вручную при подготовке: 30 имён `handle_<op>` в note и 30
  контрактов. Кандидат на `duplicated_data` (§15.3) против `DERIVED` по
  правилу `handle_` + имя — см. Q6.
- Однозначна ли маршрутизация: «exactly one of» плюс правило имени.
  Однозначность не делает реестр законным домом данных.
- `:481` — закрытая таблица операция → актор, только прозой. Кандидат на
  `missing_mapping`.
- `:487` ссылается на «State 5 catalogue order», а генератор этот текст не
  получает. Кандидат на `missing_structure` или `invalid_reference` — см. Q7.
- `:490` — коды внешнего протокола: проверка 1 §15.2 или константы поставщика
  — см. Q8.

**Отрицательный пример в той же единице:** `80_notes.md:482` адресует
`the imported RELEASE_CEILING_IMPLEMENTATION_CODE_BYTES_MAX constant` и другие
константы. Они есть: `70_data_provider_closure.json:86, 126`. Ожидаемый исход —
`CLOSED`. Если режим заблокирует этот фрагмент, это регрессия.

**Прошлые раунды:** `round-01 surface:T43` («Mapping catalogue operations to
request models») — `answered`: «The handle_ naming rule combined with the
exact handler signatures gives the operation-to-request-model mapping».
Contradictions сочли отображение выводимым, но не проверяли, где лежит
реестр.

### 12.5 `canonical_values.content_identity` — ключи сортировки: алгоритм или данные

**Контрольный неоднозначный случай.** Фрагменты: `80_notes.md:114`; повтор в
другом LLM-модуле — `record_change`, `80_notes.md:135` (модуль `store`).

> `80_notes.md:114` — "content_identity: [DETERMINISM_OR_ORDERING] Before
> hashing, lists whose order carries no meaning MUST be sorted so that the
> same content in another order has the same identity: ports by (direction,
> name), flow nodes by node_id, flow edges by (to_node, to_port, from_node,
> from_port), flow constants by (to_node, to_port), all compared as text by
> Unicode code point; …"

> `80_notes.md:135` — "record_change: [DETERMINISM_OR_ORDERING] A content
> record is written with its order-free lists in the order content_identity
> sorts them before hashing — ports by (direction, name), flow nodes by
> node_id, flow edges by (to_node, to_port, from_node, from_port), flow
> constants by (to_node, to_port) — …"

**Канонические адреса, которые есть:**

- контракт `content_identity: (subject: IdentitySubject) -> str`
  (`60_contracts.json:5`);
- `IdentitySubject` (`60_model_closure_operations.json:220–232`);
- `Port`, `FlowNode`, `FlowEdge`, `FlowConstant` в доменной closure.

**Чего не найдено:** метаданных порядка в моделях и `rules.<backend>`
«рецепта канонического дайджеста» (§15.3.1). У `global_spec.rules` нет такого
backend-а. Источники в прозе: `02_rules_functions.md:19–23` (A01),
`02_rules_flows.md:25` (A05), `60_contracts.md:184–188`.

**Что режим обязан проверить:**

- Ключи сортировки — это шаги алгоритма канонизации над существующими полями
  или закрытая таблица «поле-список → кортеж ключей». §15.11 запрещает делать
  последовательность операций значением, а §15.3.1 допускает рецепт дайджеста
  только как лист зарегистрированного детерминированного backend-а
  (вопрос Q10).
- Межмодульный повтор `:114` ↔ `:135` — работа единицы `global`. Два
  LLM-модуля обязаны совпасть, и это выполняется только потому, что текст
  скопирован.

**Допустимые исходы:**

- `NOT_DATA/algorithm_step` для `:114` — с ответом единицы `global` о повторе;
- `UNRESOLVED/home_undecided`;
- `DEFECT/missing_structure` — если владелец решит, что таблица ключей —
  данные.

**Ошибка режима:**

- `CLOSED`: адреса нет;
- `DERIVED` без зарегистрированного backend-а.

**Прошлые раунды:** `round-01 canonical_values:T16` (ничьи при равных ключах)
и `round-01 store:T56` — `consequential_gap`, blocking. Закрылись ли они, не
проверено.

### 12.6 Дополнительные отрицательные примеры (этап 11.6)

| Фрагмент | Почему он нужен | Ожидаемый класс исхода |
|---|---|---|
| `80_notes.md:109` — "fit_port_value: [DEPENDENCY_BOUNDARY] Like every function of its module it is pure: it reads no file, no clock, no environment and no store, writes nothing, and decides nothing about what a failed fit or a refused value means for its caller." | В фрагменте нет сигналов данных | `NOT_DATA`. Блокировка — регрессия. |
| `80_notes.md:482` — `answer_request` с константами `RELEASE_CEILING_*` | Законный путь §15.3.1 | `CLOSED`. Блокировка — регрессия. |
| `80_notes.md:125` — "highest_disclosure_class: [BEHAVIOR] MUST return the highest member of classes by the declared order of = models.DisclosureClass (open, then business_confidential, then personal_data) …" | Адрес есть, но члены перечисления повторены в скобках | Граничный случай. Исход зависит от Q9, тест фиксирует решение. |

### 12.7 Как регрессия выполняется

1. Фикстура — копия собранного `global_spec.json` и `80_notes.md` с
   `b3bee2e`. Копия лежит в тестовых данных `tests/`, ветку проекта она не
   трогает.
2. Провайдер подменяется, как в `tests/test_design_questions_gates.py`. Тест
   проверяет только детерминированную часть: фрагменты, сигналы M3, проверки
   §6.1, сведение §6.3 и `STALE` §8. Он не проверяет качество модели.
3. На каждый кандидат три теста:
   - подставленный ошибочный вердикт из строки «Ошибка режима» отвергается
     механически;
   - каждый допустимый исход проходит механическую проверку, если его
     свидетельства верны;
   - правка одного узла (например, `ReturnedForm`) делает `STALE` только
     зависящие от него находки.
4. Живой прогон на Cabinet Kernel — отдельный шаг после этапа 11.3. Его итог
   записывается на ветке проекта, не на `main`.

---

## 13. Открытые вопросы владельцу

Q1, Q4 и Q5 исследованы по коду и экспериментами в
`tools/DATA_CLOSURE_RESEARCH_Q1_Q4_Q5.md`: проверенные факты, варианты,
рекомендации и решения владельца.
Q9, Q10 и Q11 исследованы на notes Cabinet Kernel в
`tools/DATA_CLOSURE_RESEARCH_Q9_Q10_Q11.md`: формы упоминания enum,
ключи сортировки, межмодульные повторы и механические правила.
Решение Q9-a (необязательный `ordered: true` у enum) проверено на
совместимость с Factory в `tools/DATA_CLOSURE_SPIKE_Q9A_ORDERED_ENUM.md`.

Здесь собраны места, где план противоречит коду или §15, и места, где нужно
продуктовое решение. До ответа контракт принимает fail-closed вариант,
указанный в каждом пункте.

### Где план расходится с кодом

- **Q1. Stage 7 зависит от сборки Stage 8.**
  - *План:* п. 9 ставит `data_closure` внутрь Stage 7.
  - *Код:* единицы — это множество LLM-модулей, а его даёт Фабрика по
    собранному и синхронному `global_spec.json` (`service.py:355–413`).
    Contradictions уже работают после `design_spec_projection.py --apply`
    (§2.7).
  - *Вопрос:* принять ту же зависимость или строить `data_closure` по
    authored-артефактам (`60_*.json`, `80_notes*.md`) без сборки? Во втором
    случае Workbench сам решал бы, какие модули генерирует модель, а это
    повторяет логику Фабрики (`factory_slice_workbench/service.py:239–249`).
  - *По умолчанию:* та же зависимость, что у contradictions.
- **Q2. Правило закрытия.**
  - *Код:* единица contradictions закрывается двумя чистыми раундами на одном
    тексте (`units.py:137–145`).
  - *План:* принципы 4–5 требуют доказанного охвата и признают один дефект
    достаточным, но о числе раундов для PASS молчат.
  - *Вопрос:* хватает ли одного проверенного раунда с полным охватом (§7.3),
    или нужны два, как у contradictions?
  - *По умолчанию:* один, потому что каждый неблокирующий вердикт обязан
    пройти механическую проверку (§6.1).
- **Q3. LLM-группировка не используется.**
  - *План:* п. 7 перечисляет группировку среди переиспользуемого.
  - *Контракт:* сводит находки по детерминированному `fragment_id` (§6.3), а
    LLM-группировку (`service.py:74–104`) отбрасывает: она способна склеить
    или потерять находки.
  - *Вопрос:* подтвердить отказ и число рецензий по умолчанию. Сейчас
    `DEFAULT_RUNS = 3` (`service.py:40`).
- **Q4. Провайдер и «инструменты» для Codex.**
  - *Код:* читать файлы умеет только `CodexCliProvider`, и это не модель
    генератора (`QUESTIONS.md`, «Another model through the Codex CLI»).
    `codex exec` запускается без MCP и без репозитория
    (`provider.py:96–99, 139–147`), поэтому интерактивно вызвать резолвер он
    не может. Контракт отдаёт ему заранее посчитанный пакет свидетельств (M7).
  - *Вопросы:* устраивает ли это? Нужен ли read-only MCP внутри песочницы?
    Допустим ли `OpenAIProvider` с пакетом, вставленным в текст?
  - *По умолчанию:* только `reads_files` (DC-F4).
- **Q5. Резолвер.**
  - *Стандарт:* §15.3 требует строить таблицу достижимости «тем же resolver,
    что и таблицу происхождения типов».
  - *Код:* у Workbench такого резолвера нет. Notes gate принимает любого
    потомка известного адреса (`gate.py:296–299`). У Фабрики есть
    `spec_data_reachability`, но, по `standard_gate_matrix.json` (§15.3),
    её `_overlaps` считает ссылку на родителя законной.
  - *Вопрос:* M1 — это вызов резолвера Фабрики через subprocess (так уже
    работает `factory_slice_workbench`) или собственный резолвер Workbench?
    Если резолвер Фабрики, то как быть с допуском ссылки на родителя?

### Где нужно продуктовое или нормативное решение

- **Q6. Границы `DERIVED`.**
  - *Стандарт:* §15 (стр. 1778–1781) допускает отсутствие ячейки, только
    если «компилятор обязан уметь доказать результат из уже объявленных
    данных и версии backend».
  - *Случай:* у LLM-модуля компилятора нет. Правило `handle_` + имя операции
    (`surface`) и соответствие тип → метод репозитория из persistence IR
    (`store`) выводятся из контрактов и IR, но ни один backend их не
    доказывает.
  - *Вопрос:* это `DERIVED` или нет?
  - *По умолчанию:* без зарегистрированного backend-а `DERIVED` не
    проверяется и получает `UNRESOLVED`.
- **Q7. Ссылки notes на проектную прозу вне спеки.**
  - *Случай:* `80_notes.md:487` («in State 5 catalogue order») указывает на
    `50_public_apis.md`, которого генератор не получает.
  - *Вопрос:* к какой категории это отнести — `missing_structure`,
    `invalid_reference` или отдельной?
- **Q8. Протоколы.**
  - *Случаи:* (а) внутренний wire-формат между двумя функциями одного модуля
    (`read_runner_report`); (б) константы внешнего стандарта (коды JSON-RPC в
    `answer_request`).
  - *Вопрос:* (а) — закрытая форма для `models` или поведение модуля?
    (б) — проверка 1 §15.2 («значением владеет внешняя система») или
    константа поставщика? По тексту §15.1/§15.2 проверка 1 говорит о
    runtime-значениях внешней системы, а не о константах протокола.
- **Q9. Члены перечисления в прозе.**
  - *Случаи:* `80_notes.md:125` повторяет порядок
    `= models.DisclosureClass` в скобках. `:213` пишет `form json` без адреса.
  - *Вопрос:* считается ли дублированием (§15.3) упоминание одного члена как
    условия? А перечисление всех членов рядом с адресом? Без ответа M2 либо
    блокирует почти каждую note с условием на перечисление, либо пропускает
    повтор целого списка.
- **Q10. Рецепт канонического дайджеста у LLM-модуля.**
  - *Стандарт:* §15.3.1 называет рецепт дайджеста законным листом
    `= rules.<backend>.*` только для зарегистрированного детерминированного
    backend-а.
  - *Случай:* `canonical_values` — LLM-модуль. Его ключи сортировки
    (`80_notes.md:114`) скопированы в `store` (`:135`).
  - *Вопрос:* это допустимая алгоритмическая проза (§15.11), данные без дома
    или повод завести backend?
- **Q11. Повтор между notes без структурного дома.**
  - *План:* п. 8 называет «повторения нормативных значений в разных notes»
    дефектом.
  - *Стандарт:* §15.4 запрещает дублирование листа в двух домах, а notes
    домом не являются.
  - *Вопрос:* повтор прозы в двух LLM-модулях (`:114` ↔ `:135`) — это
    `missing_structure` единицы `global` или допустимо, если каждый повтор
    по отдельности `NOT_DATA`?
- **Q12. Какие файлы notes читаются.**
  - *Код:* notes gate читает только `80_notes.md` (`gate.py:312`), и
    `_spec_out_of_sync` сверяет со спекой только его (`service.py:371–377`).
    `authored_notes` читает все `80_notes*.md` (`language.py:216–218`).
  - *Контракт:* берёт все файлы.
  - *Вопрос:* выровнять ли существующие гейты? Это отдельная задача, не
    часть режима.
- **Q13. Установка §15 до написания notes.**
  - *Секвенсер:* `docs` фазы `state7_notes` содержат §2, §15.3.1, §15.9
    (`authoring_sequence.json`), но не §15.2 (процедура размещения) и не
    §15.11 (NOT-list).
  - *План:* п. 4A и п. 12 требуют установку §15 до notes.
  - *Вопрос:* добавлять ли §15.2/§15.11 в `docs` этой фазы на этапе 11.4?
    Это изменит то, что `authoring next` выдаёт оператору.
- **Q14. Словарь категорий.**
  - *План:* перечисляет `missing_structure`, `missing_mapping`,
    `duplicated_data`, `invalid_reference`, `derived`, `not_data` и
    разрешает «другую строго определённую категорию».
  - *Контракт:* добавляет `addressed`, `illustrative_value`,
    `home_undecided`, `coverage_gap`, `evidence_failed` и связывает
    категории с вердиктами (§5.3).
  - *Вопрос:* утвердить закрытый список.
