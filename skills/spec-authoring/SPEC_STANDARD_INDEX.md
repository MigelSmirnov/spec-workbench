# SPEC_STANDARD quick index

Короткий маршрут, чтобы не читать весь стандарт при маленькой правке спеки.

Системная карта документов и маршрутов: [FACTORY_SYSTEM_MAP.md](FACTORY_SYSTEM_MAP.md).
Этот файл отвечает только на вопрос "как правильно менять спецификацию".
Выбор operator path и переход в Route B описан в
`factory_control/ROUTE_B_ENTRYPOINT_ROUTER.yaml`.

## Если правишь одну note

1. Найди scope: `function_name:` или `ClassName.method_name:`.
2. Проверь, что note имеет ровно один primary marker: `[NOTE_CLASS]`.
3. Не добавляй inline-данные в prose. Таблицы, списки, лимиты, пути, TTL, рейтинги и размеры выноси в `config`, `models` или `rules`.
4. Если note ссылается на данные, оставь адрес: `= config.*`, `= models.*`, `= rules.*`.
5. Не расщепляй mixed note механически, если это ухудшает читаемость. Выбирай primary class по semantic impact.

## Как выбрать NOTE_CLASS

- `[BEHAVIOR]` — доменное поведение, когда точнее классифицировать нельзя без продуктовой таксономии.
- `[CONFIG_REFERENCE]` — ссылка на `= config.*`.
- `[MODEL_REFERENCE]` — ссылка на `= models.*`.
- `[RULE_REFERENCE]` — ссылка на `= rules.*`.
- `[FORBIDDEN_ACTION]` — запрет действия: MUST NOT, never, no direct access, no file I/O.
- `[SCHEMA_CONSTRAINT]` — поля, DTO/model shape, required/optional/no extra fields.
- `[VALIDATION_ERROR]` — invalid/unsupported/missing input, raise/reject/error response.
- `[RETURN_SHAPE]` — форма результата или response shape.
- `[FIELD_ASSIGNMENT]` — заполнение конкретного поля.
- `[FIELD_PROJECTION]` — перенос/проекция полей между объектами/слоями.
- `[DETERMINISM_OR_ORDERING]` — порядок, deterministic ids, стабильный результат.
- `[PROVENANCE]` — source_ref, tracking, audit trail.
- `[SECURITY_BOUNDARY]` — auth, owner scoping, access control.
- `[PATH_OR_ARTIFACT_POLICY]` — artifact kind, path safety, file/artifact access.
- `[DEPENDENCY_BOUNDARY]` — imports, layering, dependency direction.
- `[TEST_EVIDENCE]` — fixture/regression/evidence expectation.
- `[FALLBACK]` — degraded behavior, tolerated incomplete input.
- `[ORCHESTRATION]` — route registration, import-and-call, thin wrapper, exception handler.

## Куда выносить данные

- `config` — runtime/product knobs: лимиты, TTL, paths, feature knobs, небольшие списки пользовательских ключей.
- `models` — DTO/schema плюс domain catalogs/mapping tables/upstream-downstream contracts.
- `rules` — read-only policy tables: нормативы, routing/layout/fallback/threshold policy.

Не merge-ить таблицы по похожей форме. Решение только по change-axis: меняются ли они вместе и по одной причине.

## Как замкнуть данные и жизненный цикл

Полная нормативная процедура: [раздел 15](SPEC_STANDARD.md#15-данные-замыкание-размещение-жизненный-цикл).

1. Для каждой runtime-модели без `kind` получи продуктовое решение
   `identity: value|entity`; не выводи его из `id`, CRUD, ORM или способа
   хранения.
2. Размести каждое build-time значение тотальной процедурой 15.2 и оставь в
   notes только точные адреса `= config.*`, `= models.*`, `= rules.*`.
3. Объяви `persistence.class` для самостоятельно хранимых моделей и проверь
   совместимость с `identity`; отсутствие записи означает `derived`.
4. Проверь `schema_version` в `config`, `models`, `rules`, историчность
   значений для `issued` и expand/contract для несовместимых миграций.
5. Не передавай значения данных в контекст LLM: генератор данных владеет
   своими файлами эксклюзивно, а код получает только адрес и тип.

### Рабочий цикл миграции legacy persistence

До изменения старой спеки инвентаризируй не только notes, но и существующий
код с тестами: predicates, ordering, literals, storage conversions,
`CHECK`/`UNIQUE`/index semantics. Код является evidence, а не нормой.

Различай четыре механизма:

- `derivation` — результат единственно выводится из модели и версии backend;
- `placement` — продуктовое значение получает дом по процедуре 15.2;
- `lowering` — domain/storage-пара замыкается единственным codec backend-а;
- `legacy recovery` — probe обнаруживает потерянное решение, которому нужен
  владелец либо доказательство выводимости/случайности.

Codec registry принадлежит deterministic backend-у. Не добавляй
`_parse_*`, `_row_to_*` и свободные encode/decode-фрагменты в проектные
contracts, notes или persistence-данные. Если projection, query kind,
predicate или method shape не замкнуты, diagnostic emitter возвращает
`DEFECT`; он не выбирает конвенцию по большинству.

Не фиксируй полноценный persistence IR по одному проекту. Сначала прогони цикл
`legacy project → probe → missing decisions → spec → emitter → DEFECT/success`
на нескольких разных проектах и собери повторяющиеся классы незамкнутости.

## Если router собирается детерминированно

Нормативная схема: [раздел 6.1](SPEC_STANDARD.md#61-http_router_backendv1).

- `rules.http_router_backend` хранит backend declaration, route catalog,
  error policy, wiring и irregular ownership.
- Route row не содержит `signature`: canonical Python signature берётся только
  из `contracts[handler]`.
- Аргументы вызовов — только typed refs (`slot`, `credential`, `parameter`,
  `enum`, scalar `literal`), не строки с Python-выражениями.
- Project-specific state names, capability members и companion module
  задаются данными IR; backend их не прошивает.
- Присутствующий, но невалидный IR блокирует сборку. LLM fallback допустим
  только когда IR для модуля отсутствует.

## Архитектура

- Предпочитай глубокие модули с ясной ответственностью.
- Старый файл можно разделить на несколько `module_paths`, если это уменьшает связность.
- `api` остаётся тонким роутером: HTTP/auth/request-response boundary. Бизнес-логика, guards, storage, rendering и policy checks живут отдельно.
- Узкий потребительский порт описывай моделью `kind: interface` и полными
  `InterfaceName.method` contracts; interface не содержит `fields`.
- В deterministic structural spec ops создавай такой порт через
  `add_model_interface`, затем отдельно добавляй method contracts и физический
  export owner. Не создавай временное фиктивное поле через `add_model`.

## Как заполнять module_internal

- `imports.internal[provider]` — полный публичный export surface provider-а.
- `imports.module_internal[consumer][provider]` — только минимальный набор
  символов, которые consumer прямо импортирует для contracts, adapters,
  classified notes или иного явно объявленного module-local поведения.
- Не копируй в consumer весь `imports.internal[provider]` и не добавляй весь
  реестр `models` «на всякий случай»: явные записи расширяют dependency graph,
  affected-set и prompt context.
- Для `models` прямой runtime-import и транзитивный model-context различаются:
  типы полей/variants входят в context closure, но не в Python-import, пока
  consumer не обращается к ним непосредственно.
- Если прямых импортов из provider-а нет, ребро provider-а отсутствует.

Проверка импортной поверхности (read-only, без переписывания спеки):

```bash
python tools/spec_import_hygiene.py \
  --spec projects/<project>/specs/base/global_spec.json \
  --project-root projects/<project>
```

`model_registry_copy_import` имеет verdict `BLOCK`: перенос почти всего реестра
моделей не является минимальной зависимостью.
`unproven_explicit_model_import` имеет verdict `WARN`: отсутствие имени в
contracts/notes ещё не доказывает отсутствие необходимого runtime-импорта;
для существующего проекта это уточняется чтением принятого source tree.
`class_surface_amplification` пока остаётся `WARN`: это сигнал широкого порта,
но не автоматическое доказательство неверной архитектуры.
Для принятого существующего проекта `--operations-out <path>` может записать
read-only proposal формата `spec_ops`; он содержит только удаления с кодом
`unproven_explicit_model_import` и всё равно требует штатных check/apply gates.

## Как читать срез note перед правкой

Для bounded-чтения связанных нот используй `tools/spec_note_slice.py`:

```bash
python tools/spec_note_slice.py \
  --project panelforge_sandbox \
  --scope <function_or_model_scope> \
  --max-notes 40 \
  --max-records 40
```

- `--scope` — входная ручка; tool сам находит owner-модуль через `module_functions`.
- Срез включает exact raw notes, nearby notes owner-модулей и parsed facts из Spec Inspector report.
- Добавь `--json`, если срез читает агент/LLM.
- Добавь `--refresh-inspector`, если `specs/working/spec_inspector_report.json` устарел.

Инструмент нужен для чтения и advisory review. Он не заменяет `validate_spec`,
Spec Inspector gates, Route B verify или ручное принятие diff.

## Как оценить blast radius перед правкой

Чтобы за один вызов узнать «кого задену, если трону этот узел» (а не искать по
спеке кусками), используй `tools/spec_dep_slice.py`:

```bash
python tools/spec_dep_slice.py \
  --project panelforge_sandbox \
  --scope <function_or_model> \
  --markdown   # без флага — JSON для агента
```

- `--scope` — функция или модель; `--module` — взять все символы модуля целью.
- Срез строится поверх графа Spec Inspector (`build_graph`/`run_checks`), не из
  сырого JSON.
- `used_by` — обратные рёбра (контракты, модели-владельцы поля, адаптеры,
  caller-ноты): кто сломается при изменении.
- `affected_modules` — owner-модули всех потребителей: кандидаты на rebuild/deploy.
  Закрывает Route B-косяк «регенерить не весь набор затронутых модулей».
- `uses` — что узел тянет вниз (типы, вызовы, адаптер).
- `findings` — разрывы/висяки Spec Inspector, отфильтрованные по scope: видно,
  создаёт ли зона правки уже существующую проблему.

Рёбра между модулями выводятся из ссылок (тип в сигнатуре, поле модели,
call-факт), а не из `imports.internal`. Это advisory-инструмент, не gate.

## Мини-чеклист перед commit

1. `notes[]` не содержит новых inline-таблиц/лимитов/allow-lists.
2. Новый marker не продуктовый (`CIRCUIT_LOGIC`, `RENDERING_RULES` и т.п. не добавлять).
3. Адреса `= config/models/rules.*` реально существуют.
4. `module_order`, `imports.internal`, `module_internal`, `module_paths`
   обновлены, если добавлен модуль; `module_internal` не шире прямых runtime-зависимостей.
5. API не стал владельцем бизнес-логики.
