# Инвентаризация инструментов и проверок Workbench ↔ Factory (2026-11-08)

Первый шаг решения владельца в #147 от 2026-11-08 (комментарий 6724353913):
каждая практика, доказанная на cabinet-kernel, и каждый гейт Factory, который
сегодня срабатывает только после генерации, становится правилом стандарта и
проверкой на передаче (handoff) слоя-владельца. Документ — список пробелов. Он
ничего не меняет: ни инструменты, ни стандарт, ни кейсы.

## Ревизии

| Что | Ревизия |
|---|---|
| Workbench main (инструменты, skills, SPEC_STANDARD) | `783d8402` |
| cabinet-kernel | `origin/agent/cabinet-kernel` `a6a126b3` |
| client-portal | `agent/client-portal` `e6f08c73` |
| Factory main (чистый чекаут) | `89eaed39` |

SPEC_STANDARD в Workbench (`skills/spec-authoring/SPEC_STANDARD.md`) и в Factory
(`SPEC_STANDARD.md`) побайтно совпадают: 2948 строк, diff пуст.

## Главное

1. **На client-portal все проверки Workbench зелёные.** На `e6f08c73` инструменты
   main дают `design_assembly`: 15/15 ready, 0 errors. Transition States 6–7:
   все проверки `closed`. При этом Route B на `cbcc7537` остановился на
   `expense_intake` с `model_constructor_unknown_field`. Значит, проверки не
   было, а не она была неточной.
2. **Проверка карты полей на уровне спеки существовала и потеряна.** В Spec
   Inspector был `check_model_field_missing` по нотам `[FIELD_ASSIGNMENT]`. Его
   удалил коммит `076193b` (2026-08-21, «replace prose parsing with structural
   admission»). Причина в сообщении: разбор прозы покрывал слишком мало и
   пропускал неизвестную модальность. После этого поле конструктора проверяется
   только после генерации (`draft_static_gates.inspect_model_constructor_fields`).
3. **Полные `[FIELD_ASSIGNMENT]` kernel не были следствием гейта.** Их дали три
   вещи:
   - решение State 6 о типизированных `StoreChange`;
   - ручная первая редакция нот;
   - ручной анализ копий моделей в облачной сессии, на ветке Factory с пометкой
     «never merge», который передали письмами collab.

   Ни одна из них не лежит на main. Подробно — раздел 1.
4. **Спец-опс при выводе потерял по меньшей мере три проверки,** которые экспорт
   Workbench не выполняет (Factory `07eceb4d`, 2026-10-23):
   - очистку удалённых модулей;
   - ограничение области правки (allowlist, `--forbid-contract-edits`);
   - CAS-проверки `expected_*`.
5. **Три инструмента kernel ничто не требует:**
   - FA002 проверяет, что журнал Stage 8.1 есть и хеши срезов свежие, а не что
     review был;
   - FA006 возвращает `NOT_APPLICABLE` без `71_semantic_test_export.json`;
   - поставщик данных нигде не обязателен, а lint L2–L5 «Not a gate yet».
6. **Стандарт ничего не требует от `[FIELD_ASSIGNMENT]`.** У класса есть только
   определение в реестре (§2, строки 175–176): «присваивание/заполнение
   конкретного поля». Полноты карты стандарт не требует.

## Методика и ограничения

- **Inventory 1.** Узлы Route B взяты из `route_b_plan(client_portal_sandbox)`,
  манифест гейтов — из `gate_capability`. Коды прочитаны в коде Factory.
  Каждое утверждение «Workbench ловит» проверено чтением функции Workbench, а не
  по имени.
- **Inventory 3.** Основа — рабочая матрица Workbench
  `tools/standard_matrix/standard_gate_matrix.json`: 413 правил, снимок
  стандарта 2026-09-21. Матрица дополнена историей (`git log -S/-G` в обоих
  репозиториях) и поправками этой инвентаризации. Разделы, добавленные в
  стандарт после 2026-09-21, в матрице отсутствуют: §6.9 v4/v5, §6.10 v2, §6.11,
  §6.12 и переписанный §15.3.1. Их правила здесь разобраны точечно.
- **Свидетельства Factory скудны.** В чистом чекауте `89eaed39` нет ни одного
  `*.spec_handoff.json`, `*coverage_rejected.json` или `*underspec_rejected.json`:
  это сгенерированные и неотслеживаемые файлы. Счёт поэтому собран по двум
  источникам:
  - истории git (144 версии отчётов);
  - рабочему дереву `code_factory_cabinet_flow_runtime` (120 отчётов, из них 5
    `coverage_rejected`).

  Основной чекаут `code_factory` по условию задания не открывался. Отказ
  `expense_intake` не найден ни в одном закоммиченном ref; он взят из #147.
  Счёт — нижняя граница.
- **Нарушения client-portal** измерены существующими инструментами main на
  `e6f08c73` (`design_notes_lint.py`, `design_assembly.py`, `transition.py`,
  MCP `notes_language`) и одноразовыми скриптами вне репозитория. Скрипты
  эвристические, и это помечено у каждой цифры.

---

## 1. Что проверяло kernel

Kernel шёл с теми же инструментами, что и main: на ветке kernel нет ни одного
собственного инструмента. `git diff --diff-filter=A origin/main
origin/agent/cabinet-kernel -- tools skills` пуст, ветка лишь отстаёт от main.
Значит, всё, что kernel сделал сверх гейтов, сделано руками или скриптом вне
`tools/`.

| Механизм | Что проверил или вынудил | Свидетельство | Где живёт сейчас | Работает для client-portal? |
|---|---|---|---|---|
| Решение State 6 «Store calls are typed per change» (`60_contracts.md:64`) | Один вариант `StoreChange` на изменение State 5. Он несёт факты вызывающего и ни одного поля, которое назначает store. Поэтому фраза «every other field … comes from the change as given» истинна | WB `712bad8f` (2026-10-03) | Только данные кейса kernel; нормы стандарта нет | Нет. `_build_expense_aggregate` строит записи из intake, типизированного изменения на запись нет |
| Ручная первая редакция нот State 7 | В `record_change` с первой редакции: by-поля из actor, «every other field, times included, comes from the change as given», пер-вариантные «writes X / sets Y» | WB `acb0fbf7` (2026-10-03). Гейт коммита `design_notes --gate` (0 findings) карт полей не требует | Текст kernel | — |
| Анализ копий моделей (ручной, облачная сессия, «never merge») | `inventory.py` нашёл 96 пар почти-копий моделей и неявные проекции Change→record. Задан вопрос Q2: все поля, не назначенные модулем, — одноимённые поля change? Записано, что гейты Factory ловят только выдуманное поле, но не пропущенное необязательное и не перепутанные поля одного типа | CF `8843a670` (2026-10-18), только ветки `origin/analysis/cabinet-kernel-model-copies` и `collab/cabinet-kernel`; `projects/cabinet_kernel/analysis_model_copies/{REPORT.md,inventory.py,copy_sites.py}` | Только ветка анализа; не на main | **Нет** |
| Почта collab и черновики | Письма 001 и 004 и `drafts/track_a_notes.md` N8 дословно предложили ноту «пусто до события». Там же `projections.json`, `build_projections.py` и проект нормы проекций `STANDARD_NORM.md` (§5.2: список полей как данные плюс гейт) | CF `958f7eb8` (2026-10-19), `origin/collab/cabinet-kernel` | Только ветка. Норма проекций не принята ни в WB, ни в CF | **Нет** |
| Решение 35 kernel | Нота «поле, которого нет в change и которое модуль не назначает, пусто до названного позднего изменения». Коммит ссылается на анализ копий | WB `680a052b` (2026-10-19); реэкспорт в CF `8a56cd36` | Текст kernel | Нет |
| Вопросный раунд State 7 (`design_questions.py`, режим противоречий, 3 рецензента) | Раунд 83 нашёл противоречие новой ноты с «every other field … from the change as given». Добавлено «except a field the change does not carry…». Закрытие шло по правилу двух чистых раундов (82–85) | WB `680a052b`, `questions/state7/round-83/summary.json` | Инструмент на main; с #163 (`b2039ae1`) — один раунд на изменение | Да, но ищет только противоречия; отсутствие карты полей он не видит |
| Stage 8.1, ручной состязательный review (`81_module_review.md`, 1019 строк) | Четыре вопроса на срез. Заодно вручную прогнаны `normalize_spec`, `build_local_spec` и `spec_underspec_gate` Factory. Нашлись 28 callable без положительной модальности и коллабораторы, выпавшие из imports; из этого — ремонты нот N00–N13 | WB `fc8d40ba` (2026-10-10), решения 24–57 | Только kernel, вручную. Два найденных класса потом стали гейтами main: `notes_workbench/gate.py` `contract_without_positive_note` (`8322e07a`), FA018 и FA022. Четыре вопроса review не задаёт ни один инструмент | **Нет.** В `81_module_review_status.json` portal: «No separate per-module adversarial review was run» |
| Семантические тесты и `71_semantic_test_export.json` | По тесту-свидетелю на решение A01–A21; ручной мутантный review 135 свидетелей (`tests/semantic/review/*.md`); байт-точный экспорт | WB `43f502a9`, `0568dfe3`, `941a094c`, `46b2d9b9`, `d006ced3`, `6076ec23`; CF `verification/configs/cabinet_kernel.yaml` | Кейс kernel; FA006 — только «когда объявлено» | **Нет**: ни `71_*`, ни `tests/` |
| Поставщик данных (`70_data_provider_closure.json`) | 28 литералов вынесены из нот, закрыта тема «Literal values» в `60_data_closure.json`. Константы решения 58 построены скриптом только kernel | WB `346041b3` (2026-10-03), решения 56 (`42696042`) и 58 (`60c6b7db`) | Выбор кейса. Скрипты `experiments/cabinet-kernel/build_tool_schemas.py`, `build_store_persistence.py`, `build_global_spec_skeleton.py` на main не попали как инструменты | **Нет** |
| Гейты Factory `model_constructor_unknown_field` / `model_field_missing` | На `record_change` kernel не срабатывали: ни в одном ref CF нет такого отказа для kernel. У kernel на Route B срабатывали `clock_representation_mismatch` (`9f9345ea`), `reflective_attribute_access` (письмо 008) и `model_constructor_missing_required_field` в `run_graph` (письмо 015) | CF `tools/draft_static_gates.py:1648`, `tools/code_invariant_gates.py` | CF main | Да, и именно он остановил portal |
| Паритет draft/linker (все 7 кодов, которые есть только у linker, перенесены в draft gate) | Закрыл бы класс «draft принят, linker отверг» | CF `e6d04cb1` (2026-10-20), письмо 016 | **Только ветка `origin/fix/draft-linker-parity`, не влита** | Нет |
| Исправления linker из collab kernel (PR #129–#131) | Типизация полей моделей в draft и linker, доминирующее связывание, вложенные области | CF `2a8db70c`, `dfa2b045`, `654065b0` | CF main | Да |

**Что из этого следует.** Перенесено было только то, что стало гейтом:
модальность нот, срезы, imports. Не перенесено то, что жило в анализе на ветке,
в почте collab, в ручном review или в скрипте кейса. Поэтому следующее
приложение ничего этого не получило:

- полнота карты полей;
- норма проекций;
- поставщик данных как обязательный путь значения;
- состязательный review;
- семантические тесты;
- паритет draft/linker.

---

## 2. Таблица 1. Гейты Factory от `normalize_and_generate_models` до `semantic_predeploy_guards`

### Что в Factory уже размечено

Каждый код draft-гейта несёт `repair_class` (`tools/gates/draft_static_table.py`):

- `spec` — «в спеке не хватает факта». `generate_agent.classify_errors`
  отправляет такие находки в `write_spec_handoff`;
- `mechanical` — дефект формы кода.

Классификация передачи одна: `kind=generation_spec_handoff`,
`classification=generation_revision_required`, `repair_allowed=false`,
маршрут `spec_editor`.

### Какие инструменты Factory admission запускает до экспорта

- FA005 — `validate_spec`;
- FA015 — Spec Inspector;
- FA018 — нормализатор, нарезку и `data_in_model_context`.

Ничего из узлов 4–8 admission на коде не запускает.

### Шкала классов

- **C** — covered, проверка Workbench ловит до экспорта;
- **P** — partial;
- **M** — missing;
- **N** — не принадлежит Workbench: это форма кода, а не факт спеки.

### Таблица

| # | Код(ы) | Factory file:function | Что отвергает | Слой-владелец | Проверка Workbench до экспорта | Класс |
|---|---|---|---|---|---|---|
| 1 | `normalization_exception`, `normalization_integrity_warning` | `tools/normalize_spec.py:finding_from_normalization` | Спека не нормализуется | State 8 | FA018 `factory_slice_workbench/service.py:probe` запускает нормализатор | C |
| 2 | `models_selected_draft_coverage_failed`, `models_import_smoke_failed` | `rebuild_module.py:write_models_coverage_report`; `draft_static_gates.py:inspect_models_import_smoke` | Модуль models без класса или не импортируется | State 6, замыкание моделей | `model_closure_validation.py` проверяет только формы enum; models собираются для подсказок FA019, но не импортируются | P |
| 3 | `unknown_model_kind`, `model_emission_error` | `tools/generate_models_draft.py:generate_selected_draft` | Форма модели, которую эмиттер не умеет | State 6 | FA005 (`unknown_model_kind` — код валидатора) | C |
| 4 | `models_surface_*` (11 кодов) | `tools/model_surface_gate.py:validate_model_surface_code` | Поверхность сгенерированных models расходится со спекой | — | — | N (дефект эмиттера) |
| 5 | `function_contract_without_semantic_note` | `tools/spec_underspec_gate.py:run_gate` | У функции нет положительной семантической ноты | State 7 | `notes_workbench/gate.py` `contract_without_positive_note` и `missing_callable_note` в assembly (FA003) | C |
| 6 | `constant_export_without_semantic_note` | там же | У экспортируемой константы нет ноты | State 7 / State 6, поставщик | Нет: зеркало `notes_workbench/language.py` копирует правило только для функций | M |
| 7 | `scoped_notes_without_required_markers` (WARN) | там же | Нота без семантического маркера | State 7 | `language.factory_coverage` | C |
| 8 | `stub body:` → spec handoff | `generate_agent.py:validate_generated_coverage`, `classify_errors` | Функция-заглушка без покрывающей ноты | State 7 | Как №5 (есть ли нота) | C |
| 9 | `missing contract …`, `missing exported symbol`, `missing concrete …`, `concrete interface mismatch` | `generate_agent.py:validate_generated_coverage` | Генератор пропустил контрактную поверхность | — | FA010 и FA015 проверяют сторону спеки | N |
| 10 | `policy implementation owns an executable boundary` | `validate_generated_coverage` → `policy_module_io_findings` | Реализация политики делает I/O | State 6, binding backend | FA005 `policy_implementation_owns_executable_boundary` (только спека) | P |
| 11 | `forbidden_import_module`, `forbidden_import_name`, `forbidden_local_definition` | `generate_agent.py:_forbidden_constraints_from_notes` | Код нарушает «MUST NOT import/define» из ноты | State 7 / imports | FA022 проверяет кандидатов из нот; сам запрет не проверяется | P |
| 12 | `internal_call_contract_mismatch` (spec) | `generate_agent.py:_validate_internal_call_contracts` | Вызов не соответствует контракту вызываемого | State 6 + 7 | FA015 `call_argument_type_mismatch` / `missing_callee` — только для вызовов, названных в ноте | P |
| 13 | `interface_instantiation` | `code_invariant_gates.py:interface_instantiation_findings` | Создан экземпляр интерфейса | State 6, obligations | FA010 / FA015 требуют конкретный класс; notes gate, проверка 9 | P |
| 14 | `wrong import source`, `local symbol redefinition` | `validate_generated_coverage` | Форма импорта | imports | FA018 `import_shadows_own_parameter`, `models_imports_operation` | P |
| 15 | **`model_constructor_unknown_field`** (spec) | `draft_static_gates.py:inspect_model_constructor_fields` | Конструктор модели с несуществующим полем | State 6 (список полей) + State 7 (карта полей) | value-flow `lenses.inputs` судит только функции, которые штампуют момент времени, и против объединения полей всех моделей (стр. 86–94, 150). Нота, делегирующая карту генератору, не проверяется. Проверка на уровне спеки (`check_model_field_missing` Spec Inspector) **удалена** в `076193b` | **M** (формально P) |
| 16 | `model_constructor_field_type_mismatch`, `model_constructor_positional_arguments` | там же | Неверный тип или позиционные аргументы | State 6 / 7 | value-flow `outputs` — только поля-моменты | P |
| 17 | `model_attribute_unknown` (spec) | `inspect_model_attribute_reads` | Чтение несуществующего поля | State 6 + 7 | `model_surface_workbench/attributes.py:findings` (`note_attribute_unknown`) — только если нота пишет `value.attr` через точку | P |
| 18 | `frozen_model_attribute_assignment` | там же | Запись в frozen-модель | State 6 + 7 | Нет | M |
| 19 | `model_iterated_as_collection` (spec) | там же | Одиночная модель перебирается как коллекция | State 6 + 7 | Нет | M |
| 20 | `enum_member_unknown` (spec) | `unknown_member_finding` | Несуществующий член перечисления | State 1/6 + 7 | Перечисления в `model_surface_workbench/index.py` для attributes lens; L4 lint (не гейт) | P |
| 21 | `enum_member_alias_used` | `alias_finding` | Используется alias члена | — | — | N |
| 22 | `service_method_unknown` (spec) | `inspect_service_method_calls` | Метод вне объявленной поверхности | State 6 + 7 | notes gate `unresolved_structured_reference`; FA015 `dangling_ref_hard` — только если нота называет метод | P |
| 23 | `port_method_unknown` | `inspect_port_method_calls` | То же для порта | — | — | N |
| 24 | `owned_port_method_unused` (spec) | `inspect_owned_port_method_usage` | Метод репозитория никто не вызывает | Persistence-замыкание / State 7 | `flow_closure.py` — только возможности, названные шагом потока | M |
| 25 | `owned_transaction_call_outside_begin`, `owned_transaction_reentrant_call` | `inspect_owned_transaction_bracketing`, `inspect_owned_transaction_reentry` | Скобки транзакции | — | — | N |
| 26 | `note_prescribed_call_missing` (WARN) | `inspect_note_prescribed_calls` | Предписанного нотой вызова нет | — | Генерация следует ноте | N |
| 27 | `note_forbidden_local_definition` (spec) | `inspect_note_forbidden_local_definitions` | Определено то, что нота запрещает | State 7 | Нет | M |
| 28 | `workbench_label_literal` (spec) | `inspect_workbench_label_literals` | Метка дизайна (M02, A03) стала значением в коде | State 7 | Нет: в L2–L5 нет правила про метки | M |
| 29 | `stale_assumption_string`, `manual_appliance_warning_exact_text` | `inspect_forbidden_stale_assumptions`, … | Литералы PanelForge | — | — | N |
| 30 | `unresolved_generated_symbol` (spec) | `inspect_unresolved_generated_symbols` | Неразрешённый символ в полях models | State 6 | FA005 `unknown_type_name` | C |
| 31 | Форма импортов и кода: `required_import_*`, `unknown_top_level_import`, `forbidden_models_root_import`, `model_symbol_wrong_source`, `spec_data_address_core_models_import`, `local_symbol_redefinition`, `export_symbol_missing`, `imports_only_output`, `annotation_forward_reference`, `syntax_error`, `reflective_attribute_access`, `ordered_enum_compared_as_text`, `required_constructor_keyword_missing` | `draft_static_gates.inspect_*`, `code_invariant_gates.reflective_access_findings` | Форма кода; все факты уже есть в подсказке | — | FA022 и FA018 на стороне решений imports | N |
| 32 | `naive_datetime_now`, `local_timezone_dependent_projection` | `inspect_naive_datetime_now`, `inspect_local_timezone_dependence` | Наивное или локальное время в коде | State 2, источник времени | transition `time_source` / `ambient_time` — только уровень спеки | P |
| 33 | Источник времени на LLM-модулях: `undeclared_wall_clock_access`, `undeclared_elapsed_clock_access`, `alternate_wall_clock_source`, `clock_dependency_bypassed`, `clock_representation_mismatch`, `*_sample_count_mismatch`, `wall_clock_used_for_elapsed_duration`, `elapsed_reading_used_as_instant`, `disallowed_elapsed_clock_primitive`, `authority_module_missing`, `time_source_policy_invalid` | `tools/python_time_source_gate.py:run_gate` из `draft_static_gates.inspect_time_source_conformance` и `code_invariant_gates.time_source_findings` | Чтение часов вне объявленного авторитета | State 2 → 6 / 7 | FA005 гоняет `inspect_source` только на выходе детерминированных эмиттеров; transition проверяет спеку; `design_diagnose.factory_code_check` — диагностика, а не гейт | P |
| 34 | `layer_forbidden_import`, `layer_unlisted_import`, `module_size_lines_exceeded`, `module_size_functions_exceeded`, `router_function_too_long` | `tools/architecture_gates.py` | Нарушение политики архитектуры | State 3 (слои) / State 6 (инвентарь) | Нет. Политика — ручной файл Factory `specs/base/architecture_policy.json`; экспорт его не порождает | M |
| 35 | `cabinet_kernel_canonical_values_witness_failed` | `tools/gates/products/cabinet_kernel/_canonical_values:inspect_draft` | Продуктовый свидетель формата чисел | State 2, свидетель | `design_decision_witness.py` проверяет, что свидетель есть, а не что проходит | P |
| 36 | `draft_static_gate_failed`, `build_static_gate_failed`, `assembler_output_rejected_by_static_gates`, `deterministic_draft_producer_mismatch`, `*_compatibility_gate_failed`, `module_build_failed`, `models_build_failed`, `models_surface_gate_failed` | `rebuild_module.py:run_draft_static_gate` и др. | Обёртки над кодами выше; дефекты ассемблера | — | — | N |
| 37 | Граница импорта `domain/` (только печать) | `rebuild_module.py:validate_import_boundary` | `domain/` импортирует запрещённый пакет | State 3 | Нет | M |
| 38 | Арность вызова (`missing_required`), синтаксис | `linker.py:LinkerTransformer.visit_Call`, `validate_python_syntax` | Не хватает обязательных аргументов | State 6 | FA015 для вызовов из нот | P |
| 39 | `internal_import_provider_missing`, `internal_import_missing_provider_symbol`, `internal_import_unknown_internal_module`, `declared_export_missing` | `linker.py:check_internal_import_exports`, `check_declared_exports` | Межмодульные дыры импорта и экспорта | imports / State 6 | FA022 (`imports_symbol_unknown`, `imports_provider_wrong`), FA018 | P |
| 40 | `forbidden_member_access`, `static_rules_schema` | `linker.py:check_static_rules` (`specs/local_specs/static_rules.json`) | Проектные статические правила | Нет владельца (файл Factory) | Нет | M |
| 41 | `model_field_missing`, `model_surface_undeclared`, `frozen_model_mutation` | `code_invariant_gates._check_model_accesses_and_mutations` | То же, что №17–18, на линковке | State 6 / 7 | attributes lens (частично) | P |
| 42 | `model_constructor_missing_required_field`, `model_field_type_mismatch` | `code_invariant_gates._check_constructor_arguments` | Обязательное поле не передано, или тип неверен | State 6 / 7 | Нет: источник значения для необязательных моментов не проверяется вовсе | M |
| 43 | `data_literal_leak` | `data_code_seam.code_data_literal_findings`; `code_invariant_gates._data_provider_literal_leaks` | Значение данных вшито в код | State 6, поставщик / State 7 | FA005 `note_data_literal_leak`, FA018 `data_in_model_context` — на нотах; L2 не гейт | P |
| 44 | `transaction_guard_too_narrow` | `code_invariant_gates._check_transaction_guards` | Охват транзакции | — | — | N |
| 45 | `constructed_write_model_dropped` | `code_invariant_gates.dropped_write_model_findings` | Запись построена и не сохранена | State 4 / 7 | `flow_closure.py` (назван вызываемый, но не использование) | P |
| 46 | `contract_signature_mismatch` | `code_invariant_gates.contract_signature_findings` | Параметры определения ≠ контракту | — | — | N |
| 47 | `must_function_collapsed_to_stub` (BLOCK при неизменных нотах) | `factory_control/out_of_slice_regression.py:evaluate_baselines` | MUST-функция схлопнулась в заглушку | State 7 | Notes gate гарантирует, что нота есть, но не предотвращает схлопывание | P |
| 48 | `must_function_shrunk`, `module_shrunk` (WARN), `out_of_slice_changed_without_focused_sensor` (INFO) | там же | Усыхание или изменение без датчика | State 2, свидетель | `design_decision_witness.py` / transition `witness_material` | P |
| 49 | Отсутствует или чужая baseline | `semantic_predeploy.main` | — | — | — | N |
| 50 | Продуктовые predeploy (`cabinet_kernel check_build`, panelforge) | `tools/gates/hosted.py:contributions` | — | Продукт | — | N |
| 51 | 99 кодов `core.spec.validate`, включая `data_code_seam` (`note_data_literal_leak`, `note_unresolved_symbol`, `inline_note_value_template` …) | `tools/validate_spec.py` | Допустимость спеки | разные | FA005 — тот же валидатор | C |
| 52 | Классы Spec Inspector (`module_type_surface_incomplete`, `interface_implementation_disposition_missing`, `concrete_interface_contract_incomplete`, `contradictory_notes`, `call_argument_type_mismatch`, `dangling_ref_hard` …) | `vendor/spec_inspector/src/checks.py:check_*` | Граф спеки | State 6 / 7 | FA015 — тот же раннер | C |
| 53 | `model_registry_copy_import`, `class_surface_amplification`, `unproven_explicit_model_import` | `tools/spec_import_hygiene.py` (зарегистрирован, ни один узел Route B не вызывает) | Гигиена импортов | imports | FA022 частично | P |
| 54 | `strict_routing_unresolved_notes`, `deprecated_module_hints_present` | `tools/note_module_resolution_gate.py` (зарегистрирован, не вызывается Route B) | Ноту нельзя отнести к модулю | State 7 | notes gate `unknown_note_scope` | C |

**Итог по классам** (54 строки, коды одной проверки сгруппированы):

| Класс | Строк |
|---|---|
| covered | 9 |
| partial | 21 |
| missing | 11 |
| not owned | 13 |

### Свидетельства (нижняя граница, см. «Методика»)

| Код | Находок | Где |
|---|---|---|
| `note_prescribed_call_missing` (WARN) | 210 | cabinet_flow 144; эксперименты docs 66 |
| `enum_member_unknown` | 96 | panelforge_sandbox |
| `internal_import_provider_missing` | 60 | эксперименты docs |
| `reflective_attribute_access` | 7 | cabinet_flow |
| `model_attribute_unknown` | 6 | cabinet_flow |
| `model_iterated_as_collection` | 3 | cabinet_kernel |
| `model_field_type_mismatch` | 2 | cabinet_kernel |
| `model_constructor_unknown_field` | 1 + отказ `expense_intake` | cabinet_flow; client_portal (#147) |
| `model_field_missing`, `data_literal_leak`, `unknown_top_level_import` | по 1 | cabinet_flow |
| `generation_revision_required` (spec handoff), `linker_failed` | по 1 | cabinet_kernel |

---

## 3. Таблица 2. Инструменты cabinet-kernel

| # | Инструмент | Опора в стандарте или инструменте | Что требует сегодня | client-portal | Предлагаемое правило + проверка (слой) |
|---|---|---|---|---|---|
| K1 | Stage 8.1, состязательный review модулей (`81_module_review.md`, 4 вопроса на срез) | `module_review_workbench/service.py:build_slice` (`review_protocol`, 4 вопроса); `MODULE_REVIEW_WORKBENCH.md` | FA002 `_review_check` (`service.py:161`) блокирует, если журнала нет, `status≠closed`, счётчики не сходятся, модуль не `PASS` или `slice_sha256` устарел. `review_record` и ответы **не читает**. Четыре вопроса не задаёт ни один инструмент; раунд State 7 задаёт только вопрос о двух поведениях (`questions_workbench/service.py:171`), то есть Q1 | Журнал 37/37 PASS, review не было. 19 LLM-модулей ссылаются на `questions/state7/round-NN`, 18 детерминированных — на `spec/80_assembly.md` | Структурная запись (`81_module_review.json`): по каждому LLM-модулю ответы на 4 вопроса, привязанные к `slice_sha256`. FA002 блокирует, если записи нет или если `review_record` указывает на раунд State 7. **Stage 8.1** |
| K2 | Семантические тесты (`71_semantic_test_export.json`, `tests/semantic/`) | `export_to_factory.py:export_semantic_tests`; `semantic_test_subject.subject_errors`; FA006 `_semantic_check`; на стороне Factory `otk_audit.semantic_test_execution_visibility` | Ничего: FA006 = `NOT_APPLICABLE` без манифеста | Нет. 61 тег `[witness: verification:*]` на проверки Factory; 54 частичных вердикта перенесены в code-factory#189 | Решение, чья проверка Factory утверждает инвариант частично или проверки нет, получает тест-свидетель Workbench (`decision_id` в `71`). Блокирует `decision_witness_resolution` / State 8. **State 2 Required tests → State 8** |
| K3 | Поставщик данных (`70_data_provider_closure.json`, §6.10) | §6.10, §15.2, §15.3.1, §2 «Что НЕ включать»; `design_stage6_data.py` (читает файл, если он есть); `notes_authoring/lint.py` L2/L3 | Ничего: все проверки условны на наличие файла; L2–L5 — «Not a gate yet» | Нет. Отложено (`SOURCE.md`, 16 групп значений). В принятой спеке Factory `459ac96c` было 189 нот с 227 адресами `= rules.` (213 не-backend). `97533fe1` их снял, `a7d1fe9a` вернул 30 значений словами | Значение, которое читает сгенерированный код, — константа поставщика (`the imported X constant`). Лист `rules.*`/`config.*` не-backend без пути к коду блокирует на State 6. L2/L3 становятся гейтом State 7 после калибровки (см. G06). **State 6, данные; State 7** |
| K4 | Разбиение замыкания моделей (domain/operations/store/values) | Glob `60_model_closure_*.json` | Только существование замыкания (`model_closure`) | Своё разбиение: domain 32 + contracts 64 | Правило не нужно: это организация файлов |
| K5 | `STAGE7_TASK.md` | Нет (runbook 2026-10-12 для раундов Codex CLI по правилу двух чистых раундов) | Ничего | Нет | Правило не нужно: правило двух раундов отменено #163 |
| K6 | Полные карты `[FIELD_ASSIGNMENT]` / `[FIELD_PROJECTION]` (`record_change`: 9 нот FA) | §2, строки 175–176: только определение класса | Ничего | Частично (измерения ниже). Одна явно делегирующая нота `_build_expense_aggregate` | Callable, строящий запись модели M, называет источник каждого поля M (правило и проверка — G01). **State 7** (список полей владеет State 6) |
| K7 | `findings/`, `FACTORY_REQUEST_*`, `FACTORY_EXPERIMENT_REQUEST_*`, `REGISTRY_REQUEST_*` | Нет | Ничего | Другая форма: `90_factory_target.factory_checks_issue` + `spec/HANDOFF.md` | Открытое межрепозиторное обязательство — в структурное поле, которое читает admission. Необязательно. **Stage 9** |
| K8 | Анализ копий моделей и норма проекций (CF `8843a670`, collab `STANDARD_NORM.md` §5.2) | Нет | Ничего | Нет | Норма проекции как данные плюс гейт (входит в G01). **State 6/7** |
| K9 | Вопросный раунд State 6 (`questions/state6/round-01`) | У State 6 нет `question_scope` | Ничего | Нет | Отдельного правила не нужно, если G01 и G06 закроют механически |
| K10 | Ручной прогон `spec_underspec_gate` / `normalize_spec` / `build_local_spec` | — | Сейчас гейт: `contract_without_positive_note` (`8322e07a`), FA018, FA022 | Да (через гейт) | Уже закрыто |

### Сравнение по `[FIELD_ASSIGNMENT]`

| | kernel | client-portal |
|---|---|---|
| Ноты `[FIELD_ASSIGNMENT]` | 26 | 77 |
| Ноты `[FIELD_PROJECTION]` | 23 | 39 |
| Форма карты | Источник поля назван полем, правилом «из change как есть, кроме …» и **тотальным правилом по умолчанию** («поле, которого нет в change и которое модуль не назначает, пусто до …») | Поля перечислены частично; одна нота делегирует генератору («exactly the fields that record's model declares») |
| Построения с полной картой (эвристика по 14 «новым» сущностям) | — | 3 из 14 |

### Адреса значений в нотах (обе спеки — редакция 2)

| | kernel | client-portal |
|---|---|---|
| `= models.` | 54 | 0 |
| «the imported X constant» | 90 (45 различных) | 0 |
| `= config.` | 0 | 23 (имена таблиц persistence, законно) |
| `= rules.` | 0 | 0 |
| `data_provider_backend` | есть, 52 константы | нет; 32 namespace `rules` |

---

## 4. Таблица 3. Нормативные правила стандарта и что их проверяет

### 4.1 Сводка по матрице правил (снимок 2026-09-21)

Учтены правила типов `spec_validity` и `tool_obligation`, 351 правило;
`authoring_guidance` не учитывается. Точка проверки:

- **WB** — гейт Workbench;
- **F-pre** — проверка Factory, которую экспорт запускает через FA005 / FA015 /
  FA018;
- **F-post** — проверка Factory только на Route B;
- **нет** — ничего.

| Раздел | Правил | WB | F-pre | F-post | нет |
|---|---|---|---|---|---|
| 0–1 | 10 | 6 | 2 | 0 | 2 |
| 2 notes | 17 | 14 | 1 | 0 | 2 |
| 4–5 | 31 | 9 | 15 | 2 | 5 |
| 6 rules / backend IR | 101 | 49 | 4 | 33 | 15 |
| 7 imports | 13 | 0 | 7 | 2 | 4 |
| 8–14 | 30 | 6 | 21 | 0 | 3 |
| 15 данные | 121 | 36 | 9 | 12 | **64** |
| Чек-лист | 28 | 18 | 6 | 0 | 4 |
| **Всего** | **351** | **138** | **65** | **49** | **99** |

Матрица оценивает §2 «Inline-данные в notes запрещены» как F-pre
(`validate_spec:110`). На деле `data_code_seam.note_data_findings` ловит только
литерал, равный уже объявленному значению. Значение без дома не ловится; см. R3.

### 4.2 Статус по правилам, относящимся к нотам, размещению данных, полям, адресам, imports и замыканию данных

Статус:

- **сейчас** — проверяется сейчас (кем и где);
- **потеряно** — проверялось раньше, проверка удалена или обойдена;
- **никогда** — не проверялось никогда.

| Id | Правило (раздел) | Статус | Чем и где | Предлагаемая проверка (слой) |
|---|---|---|---|---|
| R1 | Точный префикс ноты (§2) | сейчас | WB `notes_workbench/gate.py` `unknown_note_scope`/`invalid_note_shape` (FA003); CF `normalize_spec` (Route B). Проверка spec-ops `patch_ops._op_add_note` ушла с `07eceb4d`, но её покрывают две названные | — |
| R2 | Положительная модальность на LLM-callable (§2) | сейчас | WB `contract_without_positive_note` (`8322e07a`, FA003); CF `spec_underspec_gate.run_gate` (генерация) | Добавить константы (G11) |
| R3 | Нет inline-данных в нотах; значение имеет дом и допустимый путь к коду (§2, §15.3.1, §15.11; исключения разобраны в §5.1) | частично | CF `validate_spec._check_note_data_literals` → `data_code_seam.note_data_findings` (`9b97372e`): только литерал, равный объявленному значению (FA005). WB L2 `literal_with_home` (`90c6cce2`) только в `notes_authoring/accept.py` и MCP `check_note_draft`, на экспорте нет. Значение без дома не проверяется | L2/L3 — гейт State 7 после калибровки (G06) |
| R4 | Адрес `= …` разрешается (§15.3) | сейчас | CF `spec_address.resolve` / `_check_config` / `_check_rules` (FA005); WB `unresolved_structured_reference` | — |
| R5 | Каждый лист данных достижим (§15.3) | частично | CF `data_code_seam.note_symbol_findings` `data_symbol_unreachable` — только символы поставщика. Общая достижимость листа никогда не проверялась | Достижимость любого листа `rules`/`config` от модуля (State 6, данные) |
| R6 | Адрес на наименьший узел (§15.3) | частично | Только редакция 3, `models_address_below_model` | Проверка для редакции 2 в notes gate |
| R7 | Ред. 3: в ноте законен только `= models.*` (§15.3.1) | сейчас | CF `spec_address._closed_form`; WB с `b70a87aa` | — |
| R7a | **Значение, которое читает код, должно иметь допустимую форму доступа (§15.3.1)** | никогда | — | Простое упоминание policy/config словами не доставляет значение. Константа называется импортируемым символом, настройка — полем settings, enum/schema — `= models.X`; в редакции 2 дополнительно разрешены адреса backend IR и перечисленные persistence leaves. Не заменять prose произвольным `= rules.*`. Ручной разбор: §5.1; связано с G06 |
| R8 | Политика/константа доходит до кода через поставщика; настройки и enum/schema имеют свои пути (§6.10–6.11, §15.3.1) | сейчас, но условно | CF `note_unresolved_symbol` и др. (FA005); WB `undereferenced_data_address`. Срабатывает только если поставщик объявлен; обязательности допустимого пути для каждого читаемого значения нет | G06; §5.1 отличает константы от settings и backend-owned данных |
| R9 | Литерал поставщика не встречается в коде потребителя (§15.9) | сейчас, после генерации | CF `code_invariant_gates._data_provider_literal_leaks` (linker) | На спеке это R3 |
| R10 | Модель без `kind` имеет `identity` (§15.1.1) | сейчас (только WB) | WB `identity_workbench` (FA003), `design_lint`. CF намеренно не вооружён (`experimental/identity_gate_probe.py`) | — |
| R11 | `identity` × `persistence` (§15.1.1) | частично (WB) | WB `design_stage6_data.lint` (`f01bab39`): только master и mirrored | Полная таблица совместимости |
| R12 | `issued` хранит значения, не ссылки (§15.5) | никогда | — | State 6, persistence-замыкание |
| R13 | Фиксированная точность, не `float` (§15.8) | никогда (только по построению поставщика) | — | Поле денег/количества типа `float` блокирует (State 6, модели) |
| R14 | expand/contract, ревизия схемы (§15.7) | никогда / частично | `schema_version` только при наличии; формы миграции нет (#147, комментарий 14:42) | Шаг ревизии N→N+1 с операциями в Workbench и эмиттере (State 6 persistence) |
| R15 | `module_internal` — только прямые runtime-импорты; тип связан полной строкой (§7, §12) | сейчас (частично) | CF `_check_imports_internal`, `type_resolver`; inspector; WB FA022. Минимальность не доказывается | — |
| R16 | `module_order`: зависимости раньше (§9) | никогда | `_check_module_order` проверяет дубли и models-первым | Топологическая проверка (State 8) |
| **R17** | **Поля конструктора / `[FIELD_ASSIGNMENT]` существуют у модели** | **потеряно на уровне спеки** | Spec Inspector `check_model_field_missing` удалён в `076193b` (2026-08-21): разбор прозы покрывал слишком мало и пропускал неизвестную модальность. Осталось только `model_constructor_unknown_field` после генерации | G01 |
| R17a | Карта полей полна: каждое поле построенной модели имеет источник | никогда; нормы нет | Стандарт не требует (§2, 175–176). Была предложена в collab `STANDARD_NORM.md` §5.2 — не принята | G01 |
| R18 | Иллюстративные значения запрещены (§15.1) | никогда | — | Детектор «например/e.g. + литерал» в notes gate (State 7) |
| R19 | Каноническая форма блоков (§15.4) | частично | По построению эмиттеров; WB `array_position_reference` | — |
| R20 | Исключительное владение файлом (§15.9) | по построению | `deterministic_emission_kind` | — |
| R21 | Удалённый модуль: его производные артефакты удаляются (lineage; Route B `accepted_removed_module_cleanup`) | **потеряно** | spec-ops `spec_ops_apply.remove_module_artifacts` + BLOCK `remove_module_artifact_cleanup_incomplete`. Экспорт пишет `removed_modules: []` и нет `artifact_cleanup` (`07eceb4d`). Ручной ремонт `2640caf1` | G02 |
| R22 | Правка спеки ограничена объявленной областью | **потеряно** | spec-ops `validate_bounded_structural_operations`, `--forbid-contract-edits`, CAS `expected_*`; хук allowlist. Экспорт — замена спеки целиком, `allowed_ops: ["accept_external_canonical_spec"]` | G03 |
| R23 | Spec Inspector проходит на принятой линии (MCP `CHANGE_LINE`, шаг 6) | **расхождение** | `tools/verify_workbench_handoff.py:verify` инспектор не проверяет и принимает `WARNINGS_ONLY` (стр. 100), а FA005 требует `PASS` | G05 |

### 4.3 Что проверяет, что MUST из ноты дошёл до кода

| Проверка | Что проверяет | Когда | На маршруте экспорта Workbench сегодня? |
|---|---|---|---|
| CF `tools/spec_underspec_gate.py:run_gate` (`7445bcbc`; модальность с `808b2610`) | У функции и экспортируемой константы есть нота с семантическим маркером и положительной модальностью. Только наличие | Factory, перед вызовом провайдера; обходится `--allow-underspecified` | Неявно в узле `generate_affected_selected_drafts`. Не в экспорте |
| WB `notes_workbench/gate.py:coverage` (`contract_without_positive_note`, `missing_callable_note`) | То же правило, только функции | State 7 и assembly | **Да** (FA003) |
| CF `generation_microscope`, линза 2 «цепочка хранения обязательства» (`0b8d26f5`) | Обязательство вызова, названное в ноте (символ), прослеживается: объявлено → срез → подсказка → реализовано в N кандидатах. Свободный MUST прозы не прослеживается | По запросу (MCP); «not wired into any route» | **Нет** |
| CF `generate_agent.validate_generated_coverage` → `.coverage_rejected.json` | Наличие моделей, контрактов и экспорта; не-заглушки; отрицательные обязательства («MUST NOT import X») | После генерации | Route B, терминально. Положительный MUST по смыслу не проверяет |
| CF правило «покрытая заглушка» + `out_of_slice_regression.stub_collapse_severity` | Функция с положительной нотой не должна выйти заглушкой | Генерация и predeploy | Route B |
| WB `71_semantic_test_export.json` + FA006; CF `otk_audit.semantic_test_execution_visibility` | Тесты существуют и привязаны к потоку или решению (не к ноте); OTK требует прогона pytest, привязанного к хешу | Экспорт и OTK | Да, но только если кейс объявил тесты (portal — нет) |
| WB `design_decision_witness.coverage` | Инвариант решения разрешается в `verification:` или `[TEST_EVIDENCE]` | Assembly | Да (FA003) |
| WB `notes_workbench/obligations.py`, `tools/obligations.py` | Обязательства разделов дизайна; `suspected_stub` | Только чтение, «index, not a gate» | Нет |
| Гейт вида `note_obligation` | — | — | Не существует ни в одном репозитории |

Вывод: всё, что проверяет MUST ноты, структурно (есть нота, есть символ, не
заглушка). Смысловой положительный MUST не проверяет ничто, кроме тестов-свидетелей.
У client-portal их нет.

---

## 5. Измерения client-portal (`e6f08c73`, инструменты main)

| Что | Результат | Чем |
|---|---|---|
| Assembly | 15/15 ready, 0 errors | `tools/design_assembly.py --json` |
| Transition State 6 / 7 | `model_closure`, `time_source`, `flow_steps`, `ambient_time`, `flow_reachability` — все `closed` | `tools/transition.py --state 6/7` |
| Проверка `fields` в assembly | `models_compared 0`, `models_unparsed 32`, `ready: true` — **непроверяемое выдано как pass** (State 1 теперь проза; `model_surface_workbench/fields.py` не судит прозу) | `design_assembly` |
| Lint данных нот L2–L5 | 1090 нот: блокирующих находок 179 (L2 `literal_with_home` 19, L3 `uncovered_data_signal` 146, L5 `diverged_copies` 14); 7028 сообщений `shared_prose`. Код возврата 0 (не гейт) | `tools/design_notes_lint.py --json` |
| Для сравнения kernel | 520 нот: блокирующих находок 200 (L2 30, L3 169, L4 1) | то же |
| Делегирующая карта полей | 1 нота (`_build_expense_aggregate`: Expense названо 3/14 полей, ExpenseDocument 5/9, ExpenseAllocation 4/9) | скрипт, точное совпадение фразы |
| Построения без полного источника полей | 11 из 14 «новых» сущностей (эвристика: «fresh/new id» + имя модели; поля сопоставлены по имени во всех нотах scope). Примеры: `_build_approved_snapshot` 2/16, `_build_import_record` 6/12, `publish_progress_photo` 5/12, `ensure_manual_budget` 5/11 | скрипт; часть полей может быть подразумеваема аргументом |
| Константы поставщика / `= models.` | 0 / 0 при 32 namespace `rules` и 25 перечислениях | скрипт |
| Stage 8.1 | 0 из 19 LLM-модулей прошли состязательный review | `81_module_review_status.json` |
| Семантические тесты | 0; 54 частичных вердикта перенесены в code-factory#189 | кейс |
| Языковой гейт Factory (MCP `notes_language`, канонический ref) | 2 block `contract_without_positive_note` (`system_clock.utc_now`, `monotonic_seconds`), 12 warn `note_without_positive_modal`, 7 warn `ambiguous_dependency_binding` | MCP `notes_language` |
| Метки дизайна в нотах (`workbench_label_literal`) | 0 (у kernel 62 ноты с метками A/M — проверить, не попадают ли они в код) | скрипт |

MCP `closure_diagnostics(client-portal)` на каноническом ref показывает 46
`ambient_time_note` и 35 `fresh_timestamp_without_source`, а локальный
`design_assembly` main на `e6f08c73` — 0 и 0. Расхождение не разбиралось.
Вероятная причина — разная версия инструментов шлюза MCP. Это отдельный
вопрос.

### 5.1 Ручной реестр структур данных в notes client-portal

Разбор готовой сборки на том же снимке `e6f08c73bf6240bbe1ab13ab8a632d707af2a644`:
[global_spec.json](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/global_spec.json) и
[80_notes.md](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md).
Все **1090** строк `notes` точно найдены в State 7. Номер #N ниже означает
`global_spec.json /notes/(N-1)`, например #1 — `notes[0]`; ссылки ведут на
точную строку неизменяемого снимка State 7.

**Результат: 30 групп данных в 46 уникальных notes.** Это классификация
содержимого, а не 30 доказанных нарушений или 46 блоков: среди групп есть
backend-owned дубли и случаи, требующие решения о форме данных. Несколько
групп могут ссылаться на одну note. Эти числа **не складываются** со 179
сообщениями L2–L5 или 165 сообщениями L2/L3 из таблицы выше: у подсчётов разные
единицы. Автоматические проверки в ходе этого ручного разбора заново не
запускались; их результаты выше остаются отдельным свидетельством.

Применён стандарт через
[SPEC_STANDARD_INDEX.md](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/skills/spec-authoring/SPEC_STANDARD_INDEX.md):
§2, §6.10, §15.1–15.3.1, §15.9 и §15.11
[SPEC_STANDARD.md](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/skills/spec-authoring/SPEC_STANDARD.md).
Редакция спеки — **2**; запреты только редакции 3 к ней не применялись.
Blob стандарта на main и canonical ref одинаков:
`8ea002ff039d20b7b60bae08f327614e639bd35a`.

#### Реестр

«Дом» — существующий узел либо явно отмеченный пробел. Это не новые
утверждённые адреса и не предложение объединить похожие таблицы: дом
определяется change-axis §15.2. Номер группы локален этому реестру.

| ID | Структура / значения в прозе | Точные notes | Дом и разбор |
|---|---|---|---|
| D01 | **Денежная валюта**. EUR | [#95 `validate_eur_amount`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L105); [#746 `_validate_snapshot_publication`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L819); [#759 `_validate_snapshot_publication`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L832); [#811 `correct_expense`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L890); [#878 `register_work_payment`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L963); [#898 `register_work_payment`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L983) | rules.money_policy.currency. Значение продуктовой политики; в notes остаётся вызов проверки, валюта приходит как константа. |
| D02 | **Точность и округление денег**. 2 fraction digits; ROUND_HALF_UP | [#95 `validate_eur_amount`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L105); [#96 `calculate_completed_work`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L106); [#100 `_quantize_money`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L110); [#898 `register_work_payment`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L983) | rules.money_policy.fraction_digits; rules.money_policy.rounding. Формулы вычислений остаются поведением; шаг/точность/режим — значения политики. |
| D03 | **Знак баланса → метка**. positive → COMPLETED_AHEAD_OF_PAYMENTS; negative → UNUSED_ADVANCE_PAYMENT; zero → BALANCED | [#99 `calculate_work_balance`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L109) | models.WorkBalanceLabel — только варианты; отдельной таблицы соответствия нет. Соответствие выбирает член перечисления, а не действие. Нужен дом таблицы; enum сам таблицу не заменяет. |
| D04 | **Имя переменной окружения Registry**. REGISTRY_BASE_URL | [#518 `validate_project_reference`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L567); [#521 `get_project_context`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L570); [#524 `_registry_url`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L573); [#528 `list_active_projects`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L577) | config.registry_endpoint_env_name. Имя — build-time значение; фактический URL — runtime-настройка. Не хранить конкретный URL. |
| D05 | **Шаблоны путей Registry**. projects/{project_id}/validate; projects/{project_id}/context; projects | [#518 `validate_project_reference`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L567); [#521 `get_project_context`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L570); [#528 `list_active_projects`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L577) | config.registry_request_paths. Пути перечислены прозой при уже имеющемся структурном доме. |
| D06 | **Таймаут Registry**. 5 seconds | [#518 `validate_project_reference`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L567); [#521 `get_project_context`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L570); [#528 `list_active_projects`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L577) | config.registry_timeout_seconds. Значение зависит от эксплуатационной настройки; доставлять через настройки/поставщик согласно §15.3.1. |
| D07 | **Ошибка Registry → категория**. invalid identifier → INVALID_UUID; unknown → NOT_FOUND; inactive → ARCHIVED; timeout → TIMEOUT; transport → TRANSPORT_ERROR; HTTP → HTTP_ERROR; body → SCHEMA_MISMATCH; other project → IDENTITY_MISMATCH | [#525 `_translate_registry_failure`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L574) | rules.registry_failure_translation; models.RegistryFailureKind. Закрытая таблица значений; логика обнаружения ошибки может оставаться прозой. |
| D08 | **Категория significant mutation**. Перечисленный набор AuditAction, для которого rejected требует reason_code | [#534 `_validate_audit_intent`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L589) | models.AuditAction; rules.audit_result_reason_policy — правило reason, без набора significant. Подмножество enum — данные прямо по §2. Нужна явная классификация членов; reason-validation остаётся поведением. |
| D09 | **Права по типу principal/роли**. operator; administrator additions; viewer; estimate_producer → наборы Capability | [#542 `authorize_access_management`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L600); [#546 `_require_capability`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L604); [#555 `authorize_access_management`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L613) | rules.principal_capability_sets; models.Capability. Наборы enum и их принадлежность — данные. Объединение operator + additions — операция, остаётся требованием. |
| D10 | **Таблица переходов staff**. active → suspended/disabled; pending_verification → active; suspended → active/disabled; disabled → ∅ | [#571 `change_staff_status`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L632); [#593 `change_staff_status`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L654) | rules.status_transitions.staff. Отношение между членами enum — табличные данные. Каскад отзыва сессий — поведение. |
| D11 | **Таблица переходов principal**. active → disabled; disabled → active | [#691 `change_service_principal_status`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L761) | rules.status_transitions.principal. Переходы — отношение enum; отзыв credentials и запись аудита — поведение. |
| D12 | **Границы длины пароля**. 12..128 code points inclusive | [#577 `_validate_new_password`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L638) | rules.staff_identity_input_policy.credential_min_codepoints; credential_max_codepoints. Пороговые значения — данные; запрет trim/normalize и отклонение control characters — поведенческая часть. |
| D13 | **TTL staff session**. 12 hours | [#584 `authenticate_staff`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L645); [#605 `authenticate_staff`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L666) | config.staff_session_ttl_hours. В #605 уже сказано configured timedelta, но в #584 значение встроено. TTL имеет отдельный дом; выбор config/rules пересмотреть по change-axis §15.2. |
| D14 | **TTL viewer session**. 30 days | [#682 `enter_viewer_access`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L749) | config.viewer_session_ttl_days. Тот же класс утечки значения; получение created_at и прибавление срока — поведение. |
| D15 | **Энтропия credential**. issue_verification_secret(session_id, 32) | [#623 `authenticate_staff`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L684) | config.credential_entropy_bytes; rules.credential_security_backend. 32 — значение данных; вызов и связывание идентичности — поведение. Python-подобный вызов отдельно противоречит запрету микро-синтаксиса. |
| D16 | **Поддерживаемые версии внешних контрактов**. snapshot [1]; OCR [1] | [#746 `_validate_snapshot_publication`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L819); [#859 `create_expense_from_recognition`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L941) | rules.supported_external_contract_versions.snapshot; .ocr. Закрытые allow-lists. Это разрешённые номера версий контракта, а не runtime-экземпляры внешних данных. |
| D17 | **ImportOutcome → audit result/reason**. ACCEPTED/IDEMPOTENT_REPLAY → SUCCESS + no reason; INTEGRITY_CONFLICT → REJECTED + outcome code; rejection → reject reason | [#758 `import_snapshot`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L831) | models.ImportOutcome; models.AuditResult; rules.audit_result_reason_policy — частичное покрытие. Соответствие значений и категория outcomes — данные. Порядок записи import record/audit остаётся поведением. |
| D18 | **Причина content rejection → ImportRejectReason**. unsupported version; wrong currency; invalid sections; incomplete content → четыре кода reason | [#759 `_validate_snapshot_publication`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L832) | models.ImportRejectReason; полной таблицы соответствий в rules нет. Выбираемый код — значение; само условие проверки входа и raise — поведение. |
| D19 | **Тип исключения → причина отказа импорта**. ArchivedProjectRejected → ARCHIVED_PROJECT; ScopedNotFoundError → UNKNOWN_PROJECT; AuthorizationRejected → SCOPE_DENIED | [#760 `import_snapshot`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L833) | models.ImportRejectReason; отдельной таблицы этих трёх соответствий нет. Не таблица callable-ов: результатом выбора является код enum. Возможность представления ключа-исключения текущим DSL требует отдельного решения; не придумывать строковый DSL. |
| D20 | **Диапазон процента готовности**. integer 0..100; reject bool | [#877 `set_section_progress`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L962); [#883 `_validate_completion_percent`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L968) | models.SectionProgress / ProgressSectionView — форма; явный диапазон надо закрепить у владельца schema/policy. Границы валидации — build-time ограничения. Формулу percent/100 не выносить механически: это семантика процента. |
| D21 | **BinaryObjectKind → disposition**. expense document → attachment; progress photo → inline | [#981 `viewer_read_expense_document_endpoint`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L1075); [#982 `viewer_read_progress_photo_endpoint`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L1076); [#1058 `staff_read_expense_document_endpoint`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L1155); [#1059 `staff_read_progress_photo_endpoint`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L1156) | rules.binary_delivery_policy.response.content_disposition. Таблица значений уже есть. Часть scopes принадлежит deterministic backend/router: отдельно проверять его владение, не объявлять автоматически утечкой в LLM. |
| D22 | **Заголовки binary response**. Cache-Control: no-store; X-Content-Type-Options: nosniff; имена Content-Type/Length/Disposition | [#983 `_binary_content_response`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L1077) | rules.binary_delivery_policy.response. Фиксированные значения и имена — данные/протокол; перенос runtime payload.content и length — FIELD_PROJECTION, не статическая таблица. Scope в api_irregular. |
| D23 | **Cookie: имя и атрибуты**. __Host-portal_viewer_session; Secure; HttpOnly; SameSite=strict; Path=/; no Domain | [#961 `viewer_enter_endpoint`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L1055); [#970 `viewer_logout_endpoint`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L1064) | rules.http_transport_policy.browser_session; rules.viewer_cookie_transport_backend. Данные присутствуют, но эти scopes отданы backend-у api_irregular. Нужна проверка канонической эмиссии; не предлагать параллельного владельца поверх backend. |
| D24 | **Префикс API и mount paths**. /api; / | [#1073 `_canonical_path`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L1173); [#1087 `create_runtime_app`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L1193) | rules.http_transport_policy.public_api_prefix; .inner_fastapi_prefix. Адресные значения отличаются от операции strip/mount. Сами порядок mount и снятие ровно одного сегмента остаются поведением. |
| D25 | **Allow-list путей no-store**. /auth/viewer/enter; /auth/viewer/session; /auth/viewer/logout; /auth/staff/login; /auth/staff/logout; /auth/credential/issue; /auth/credential/revoke | [#1076 `_requires_no_store`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L1176) | rules.http_transport_policy.security_headers — значение no-store есть; exact path set отдельно не объявлен. Явный закрытый набор путей — данные. Его связь с route catalog проверять семантически, не по похожим строкам. |
| D26 | **Transport condition → HTTP status**. host 400; allowed preflight 204; origin refusal 403; oversized body 413; rate limit 429 | [#1072 `install_transport_guards`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L1172) | rules.http_transport_policy; rules.http_router_backend.error_policy не покрывает эту guard-таблицу. Числовые ответы — соответствия значений. Порядок guard-ов, first failure и вызов next ровно один раз — поведение, не данные. |
| D27 | **Таблица security headers**. X-Content-Type-Options=nosniff; X-Frame-Options=DENY; Referrer-Policy=no-referrer; Permissions-Policy=geolocation=(), microphone=(), camera=(); Cache-Control=no-store | [#1080 `_apply_security_headers`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L1180) | rules.http_transport_policy.security_headers. Фиксированные строки уже дублируют policy. X-Request-Id получает runtime request id; само его значение в спеку не переносить. |
| D28 | **Health: пути и фиксированный status**. /health/live; /health/ready; status='ok' | [#1085 `liveness_endpoint`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L1191); [#1087 `create_runtime_app`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L1193) | rules.http_transport_policy.health; models.HealthStatus.status: str. Пути имеют дом. 'ok' не замкнут enum/default-ом HealthStatus; закрепить допустимую форму у schema или константу, не угадывать новую продуктовую таксономию. |
| D29 | **Исход bootstrap CLI → exit code**. created 0; mismatch 1; rejected identity 2; already completed 3 | [#1088 `run_bootstrap_cli`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L1197) | Упомянута bootstrap command outcome table, в config/models/rules соответствующей таблицы нет. Это явная таблица integer-значений; текст называет несуществующий доступный коду источник. Не выносить сами команды/обработчики как данные. |
| D30 | **Формат transport log record**. labels rid, method, path, status; этот порядок; '='; single spaces | [#1081 `_transport_log_record`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L1181) | rules.http_transport_policy.logging — есть redaction policy, точного формата нет. Статические labels/сепараторы/порядок формата требуют решения владельца; runtime request values остаются runtime. Для шаблонов §15.11 запрещает свободный DSL. |

#### Исключения и границы: что не считать inline-таблицей автоматически

| Случай | Решение по стандарту / точные примеры |
|---|---|
| Enum → значение или категория членов | Таблица и подмножество enum — данные по §2/§15.2. Упоминание enum рядом не размещает таблицу. Для полного покрытия применима форма `record_tuple` v2 с enum-столбцом, `key`, `total` (§6.10), когда типы её ячеек это допускают. D03, D08–D11, D17 — калибровочные примеры. |
| Условие выбирает действие кода | Остаётся прозой по §2: например, [#741 `issue_service_credential`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L811) отказывает в выпуске credential неактивному principal; [#805 `activate_budget_version`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L881) отказывает в активации при unresolved allocations. Проверки, raise, вызовы и порядок guard-ов не следует механически превращать в lookup-таблицу. В [#1072 `install_transport_guards`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L1172) порядок pipeline — поведение, но выбранные числовые HTTP statuses выделены как D26. |
| Член enum → функция/метод | Это контракт или правило backend-а, не данные (§6.10). Не добавлять свободный реестр callable-ов, строковый микро-DSL или последовательность операций в данные (§15.11). |
| DTO / проекция полей | Форма принадлежит `models`; перенос полей уже объявленной модели остаётся `FIELD_PROJECTION`/`RETURN_SHAPE`. [#968 `_viewer_session_view`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L1062), [#1021 `_viewer_view`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L1118), [#1024 `_service_principal_view`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L1121) перечисляют поля безопасной проекции; это не основание завести второй policy-allow-list полей поверх DTO. Полнота источников полей — отдельный G01. |
| Runtime-экземпляры и математические операции | UUID, timestamps, пользовательские значения и внешний token не являются build-time данными (§15.1). Формула баланса [#98 `calculate_material_balance`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L108), runtime-проекция сумм и отсутствие измерения не выносятся как экземпляры в config/rules. Деление процента на 100 в [#96 `calculate_completed_work`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L106) — семантика формулы; выбор точности/округления отдельно выделен D02. |
| Протокольные константы | [#1074 `_normalized_origin`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L1174) содержит 443/https и 80/http; [#603 `_normalize_staff_email`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L664) — синтаксис email; [#1077 `_body_within_limit`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L1177) — правило Content-Length. Это требует проверки выводимости из выбранного протокола/backend-а, а не автоматического создания изменяемых продуктовых настроек. |
| Сортировка runtime-результатов | Требование сортировки может оставаться поведением. [#517 `list_active_projects`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L566), [#881 `list_project_payments`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L966), [#933 `build_payment_view`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L1024), [#938 `_project_photos`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L1029), [#939 `_ordered_project_items`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L1030) надо сверять с `project_list_ordering`, `derived_view_ordering` и persistence IR. Repository и публичная view могут законно иметь разные ключи; не сливать их по форме. |
| Разрешённые persistence-ссылки редакции 2 | **23** ссылки `= config.persistence.*` в **11** notes (#101, #108, #124, #134, #155, #166, #185, #197, #256, #257, #511) подпадают под §15.3.1. Не считать все 23 нарушениями. В [#134 `create_budget_schema`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L156) рядом с разрешёнными адресами отдельно повторены значения `budget_versions` и `section_plans`: законность адреса не легализует воспроизведение значения. |
| Schema, codec, фиксированная семантика backend-а | Canonical model + IR задают схему; выводимые PK/UNIQUE/nullability/codecs не должны получать второй ручной дом (§15.9). [#398 `PersistenceError.__init__`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L441) с `persistence_error`, [#285 `PortalStore.begin`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L328) с порядком создания схем/accessors и [#170 `SqliteExpenseRepository.get_expense_aggregate`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L198) с positional decoding сначала проверяются как derivation/backend-owned, а не как новые runtime knobs. D21–D23 требуют такой же проверки владения. |

**Отдельный ссылочный дефект:** [#959 `build_project_overview`](https://github.com/MigelSmirnov/spec-workbench/blob/e6f08c73bf6240bbe1ab13ab8a632d707af2a644/examples/client-portal/80_notes.md#L1050) содержит `= rules` на весь
корень. Это не минимальный узел и не разрешённая редакцией 2 ссылка на
конкретный backend IR (§15.3/§15.3.1); само поведение обработки недоступной
части overview следует оценивать отдельно от дефекта ссылки.

#### Что реестр добавляет к G06 / R3 / R7a / R8

В notes нет ни `= models.*`, ни `the imported X constant`; в сборке нет
`rules.data_provider_backend`. Само отсутствие этих форм не делает каждую
note ошибочной: настройка может читаться через settings, а deterministic
модуль получает IR своим путём. Но реестр показывает конкретных потребителей
значений — financial_policy, registry_gateway, authorization_guard,
staff_identity, transport_guard и CLI — для которых одного присутствия
policy в `rules` недостаточно.

Для калибровки предлагаемого G06 нужны разные ожидаемые исходы:

- **Данные с уже имеющимся домом:** D01/D02, D05/D06, D09–D16, D27.
  Проверять дублирование значения и реальный допустимый путь к consumer-у.
- **Данные с неполным/необъявленным домом:** D03, D08, D17–D19, D25,
  D28–D30. Сначала решение владельца и представимая форма DSL; не придумывать
  отсутствующую таблицу и не подавать её значение в LLM-контекст.
- **Backend-owned и разрешённые ссылки:** persistence-ссылки, derivation,
  D21–D23. Проверять через canonical backend ownership, не вводить второй
  поставщик поверх существующего эмиттера.
- **Допустимое поведение и пограничные случаи:** условия выбора действий,
  DTO-проекции, сортировки, формулы и протокольные значения из таблицы выше.
  Нужны отрицательные примеры, чтобы новый gate не блокировал любую подробную
  note или любое число.

Реестр — свидетельство для проектирования и калибровки проверки. Он не
меняет стандарт, инструменты, case design states или `global_spec.json` и
не объявляет результаты существующего lint подтверждёнными вручную.

---

## 6. Расхождения документов и инструментов

1. **FA002 и документация.** `FACTORY_ADMISSION_WORKBENCH.md:40` говорит «when
   present», а код (`service.py:170`) блокирует при отсутствии журнала.
   Перечисленный статус `PASS_INTERNAL_VARIATION` тоже блокирует, потому что код
   требует ровно `PASS`.
2. **Шаг 6 MCP и `verify_workbench_handoff`.** `CHANGE_LINE` шаг 6
   (`experimental/factory_mcp/spec_change.py`) обещает «passing inspector».
   `tools/verify_workbench_handoff.py:verify` инспектор не проверяет и
   принимает `WARNINGS_ONLY`.
3. **Журнал Stage 8.1 client-portal и решение владельца.** Журнал ссылается на
   «#147/#163» как на основание считать раунд State 7 review Stage 8.1. Решение
   владельца от 2026-11-08 называет review отсутствующим. Нужно решение
   владельца до того, как писать правило K1.
4. **Not-checkable как pass.** Проверка assembly `fields` при 32/32
   неразобранных моделях отвечает `ready` — нарушение правила #147 «not
   checkable ≠ pass».

---

## 7. Приоритетный список пробелов

Сначала идут потерянные проверки, затем пробелы по силе свидетельства: отказ
генерации наблюдался или вероятен, неверный код. Колонка CP — нарушает ли
client-portal сейчас. Размер:

- **S** — до дня;
- **M** — 2–3 дня;
- **L** — неделя и больше.

| Id | Пробел | Слой-владелец | Предлагаемая проверка (детерминированная, где возможно) | Размер | CP (`e6f08c73`) |
|---|---|---|---|---|---|
| **G01** | **Карта полей построения** (потеряно: `076193b`; норма отсутствует). Прямой пре-образ `model_constructor_unknown_field`, `model_constructor_missing_required_field` и `model_field_type_mismatch` | Норма: §2, раздел о `[FIELD_ASSIGNMENT]`. Проверка: State 7 notes gate; список полей — State 6 model closure | Две части. (а) Каждое поле, названное в нотах FA/FP scope рядом с моделью M, существует у M. (б) Callable, который строит M (нота FA с глаголом построения + имя M, или возврат новой сущности), называет источник каждого поля M одной из закрытых форм: поле → источник; «каждое поле X, кроме …», где у X те же поля; тотальное правило по умолчанию с названными исключениями. Фразы, делегирующие выбор полей модели («fields the model declares»), блокируют. Обобщить `value_flow_workbench/lenses.inputs` до пер-модельного сопоставления вместо объединения полей. Калибровать на kernel: его формы должны проходить | M | **Да**: 1 делегирующая нота; 11/14 построений без полного источника (эвристика) |
| **G02** | Очистка удалённых модулей при экспорте (потеряно: `07eceb4d`) | Stage 9, экспорт | `export_to_factory.stage9_lineage_manifest` вычисляет `removed_modules` как разность `module_functions` между принятой и новой спекой и пишет `change_summary.artifact_cleanup`. FA-проверка: удалённый модуль без записи очистки блокирует | S | Да: 3 модуля (`staff_challenges`, `email_delivery_gateway`, `email_delivery_repository`), исправлено вручную в CF `2640caf1` |
| **G03** | Ограничение области правки (потеряно: `07eceb4d`) | Stage 9, экспорт | Экспорт сравнивает `project_spec_delta` с областью изменения, объявленной в кейсе (затронутые модули и контракты). Изменения вне области блокируют без явного «owe_global» | M | Не измеримо (свойство маршрута) |
| **G04** | Паритет draft/linker не влит (CF `e6d04cb1`, только ветка) | Factory | Решение о слиянии `origin/fix/draft-linker-parity` | S | Косвенно: класс «draft принят, linker отверг» |
| **G05** | `verify_workbench_handoff` не проверяет инспектор и принимает `WARNINGS_ONLY` (расхождение с MCP) | Factory, intake | Привести verify к FA005/FA015 (`PASS`, отчёт инспектора привязан к SHA) или исправить текст MCP | S | Нет данных |
| **G06** | Поставщик данных не обязателен; значения словами | State 6 данные (размещение) + State 7 (lint) | (1) Читаемое сгенерированным кодом значение без допустимого пути §15.3.1 блокирует на State 6: константа поставщика, поле settings или enum/schema; backend-owned данные проверяются по их IR. (2) Нота, воспроизводящая значение или заменяющая доступ простым упоминанием policy/config (R3/R7a), блокирует; условия выбора действий не превращаются в таблицы. (3) L2/L3 — гейт State 7 **после калибровки**: kernel, образцовый по данным, сам даёт 199 блоков L2/L3 | L | **Да**: 0 констант, 32 namespace `rules`; L2+L3 = 165 блоков; в принятой спеке Factory было 213 не-backend адресов. Отдельный ручной реестр §5.1: 30 групп в 46 notes, с backend-owned и пограничными случаями; это не число ошибок lint |
| **G07** | Stage 8.1 не требует review | Stage 8.1 | Структурная запись ответов на 4 вопроса по LLM-модулю, привязанная к `slice_sha256`. FA002 читает её и блокирует при отсутствии или при ссылке на раунд State 7. Вопросы Q2–Q4 (тривиальная реализация, локализуемость эффектов, поведение без источника) — в инструмент `module_review_workbench` | M | **Да**: 0/19 |
| **G08** | Семантические тесты не требуются | State 2 (Required tests) → State 8 | Инвариант с частичной или отсутствующей проверкой Factory получает тест-свидетель Workbench в `71`; иначе `decision_witness_resolution` блокирует. FA006 без манифеста при таких инвариантах — BLOCK, а не N/A | L | **Да**: 0 тестов; 54 частичных вердикта |
| **G09** | Поверхность моделей в нотах: поля, члены перечислений, frozen, коллекции | State 7 (против State 6) | Расширить attributes lens: не только `a.b` через точку, но и «field X of M», «M.X»; член перечисления в ноте ⊆ членов; запись в frozen-модель и итерация одиночного значения — по классам нот | M | Не измерено (`enum_member_unknown` — самый частый код в свидетельствах, 96) |
| **G10** | Not-checkable как pass в `fields` | State 1/6, assembly | При `models_compared == 0` и `models_unparsed > 0` — `not_checked`, а не `ready`; сравнивать замыкание с контрактами, а не с прозой State 1 | S | **Да**: 32/32 неразобраны |
| **G11** | Underspec для констант не зеркалирован | State 7 / State 6 поставщик | Добавить `constant_export_without_semantic_note` в `notes_workbench/language.py` и gate | S | 0 (констант в контрактах нет) |
| **G12** | Источник времени на LLM-модулях только после генерации | State 2 → 7 | Transition `time_source` применяет правила elapsed гейта Factory к нотам (направление #147); код-гейт явно `not_checked` до генерации | M | 0 по assembly main; 2 блока языкового гейта на `system_clock` |
| **G13** | Политика архитектуры без владельца в Workbench | State 3 | Экспорт порождает `architecture_policy.json` из слоёв State 3, или FA-проверка сверяет файл Factory со State 3 | M | Не измерено |
| **G14** | Неиспользуемый метод порта (`owned_port_method_unused`) | Persistence-замыкание / State 7 | Каждый метод репозитория в контрактах имеет потребителя в нотах или потоках | S | Не измерено |
| **G15** | Запрещённое нотой определение (`note_forbidden_local_definition`) и метки дизайна в коде (`workbench_label_literal`) | State 7 | Метки A/M/INV в нотах — report; запрет определения прослеживается в срезе | S | 0 меток |
| **G16** | Правила §15 без проверок: `issued` хранит значения (R12), без `float` для денег (R13), иллюстративные значения (R18), `module_order` (R16) | State 6 / 7 / 8 | По проверке на правило; см. таблицу 4.2 | S каждое | Не измерено |
| **G17** | Миграция схемы не выражается (R14, #147 14:42) | State 6 persistence + эмиттер Factory | Объявленный шаг ревизии N→N+1 с операциями | L | **Да**: удаление `email_deliveries` вручную |
| **G18** | Расхождение FA002 с документацией и `PASS_INTERNAL_VARIATION` | Stage 9 | Привести документ и код к одному | S | — |

### Первые 10 (по вероятности отказа генерации или неверного кода)

1. **G01** — карта полей. Потеряно в `076193b`; это наблюдаемый отказ
   `expense_intake`. CP: 1 делегирующая нота и 11/14 построений.
2. **G02** — очистка удалённых модулей. Потеряно в `07eceb4d`; в Route B
   остаётся мёртвый код. CP: 3 модуля (ручной ремонт).
3. **G03** — область правки. Потеряно в `07eceb4d`. CP: не измеримо.
4. **G06** — поставщик данных и значения словами: неверные значения в коде.
   CP: 0 констант, 165 блоков L2/L3.
5. **G09** — поверхность моделей в нотах (`enum_member_unknown`,
   `model_attribute_unknown` — самые частые коды). CP: не измерено.
6. **G07** — Stage 8.1 review. CP: 0/19.
7. **G08** — семантические тесты. CP: 0 тестов, 54 частичных вердикта.
8. **G10** — `fields` выдаёт непроверяемое за pass. CP: 32/32.
9. **G05** — handoff verify и инспектор. CP: —.
10. **G12** — источник времени на LLM-модулях. CP: 2 блока на `system_clock`.

### Порядок работ (предложение)

Сначала G01 вместе с нормой стандарта о карте полей: это единственный пробел,
который уже остановил Route B. Затем G02 и G10 — небольшие, чинят ложный pass
и потерю при экспорте. G06 и G07 — до пересборки client-portal, потому что
решение владельца требует её именно под этими проверками. G03, G08 и G09
можно вести параллельно.
