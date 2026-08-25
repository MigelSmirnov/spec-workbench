# Cabinet Backend — разведка локальной платформы

Дата проверки: 2026-08-02
Область: фактические контракты Registry, PresuPro, Holded-интеграции и локального межсервисного взаимодействия.
Метод: сначала Factory MCP (`list_factory_projects`, затем `factory_state` и scope diagnostics), после этого — ограниченная проверка исходного кода, тестов и SQLite-файлов релевантных проектов. Код приложений не изменялся.

Статусы выводов:

- `confirmed` — подтверждено исполняемым кодом, схемой хранения и/или проходящим тестом;
- `partial` — существует только часть требуемого контракта либо разные источники расходятся;
- `not_found` — контракт или механизм не найден в проверенной области.

## 1. Repository map

Finding: Registry найден как Factory-проект `registry_sandbox` внутри основного git-репозитория Code Factory; это не отдельный git-репозиторий.
Status: confirmed
Repository: `/home/smirnov/jestor_VBC/exp_vbc/demo/code_factory` (branch `agent/client-portal`)
Path: `projects/registry_sandbox`
Symbol: Factory project `registry_sandbox`
Evidence: Factory `list_factory_projects` вернул `registry_sandbox`; `factory_state` указал project root `/home/smirnov/jestor_VBC/exp_vbc/demo/code_factory/projects/registry_sandbox`; `git rev-parse --show-toplevel` для этой области вернул корень Code Factory.
Implication for Cabinet Backend: фактический Registry-контракт нужно брать из `projects/registry_sandbox`, но версионируется он вместе с Code Factory.

Finding: PresuPro найден как Factory-проект `PresuPro_sandbox` внутри основного git-репозитория Code Factory; это не отдельный git-репозиторий.
Status: confirmed
Repository: `/home/smirnov/jestor_VBC/exp_vbc/demo/code_factory` (branch `agent/client-portal`)
Path: `projects/PresuPro_sandbox`
Symbol: Factory project `PresuPro_sandbox`
Evidence: Factory `list_factory_projects` вернул `PresuPro_sandbox`; `factory_state` указал project root `/home/smirnov/jestor_VBC/exp_vbc/demo/code_factory/projects/PresuPro_sandbox`.
Implication for Cabinet Backend: модели сметы и встроенная Holded-интеграция находятся здесь.

Finding: существующий Cabinet является отдельным вложенным git-репозиторием.
Status: confirmed
Repository: `/home/smirnov/jestor_VBC/exp_vbc/demo/code_factory/projects/Cabinet_web` (branch `agent/invoice-presupro-alignment`)
Path: `projects/Cabinet_web`
Symbol: repository root
Evidence: `git -C projects/Cabinet_web rev-parse --show-toplevel` вернул сам каталог `projects/Cabinet_web`; в нём есть собственный `.git`.
Implication for Cabinet Backend: существующие Cabinet-документы и инструменты принадлежат отдельному репозиторию; в этой разведке они использованы только для проверки наличия интеграционных точек.

Finding: `client_portal_sandbox` содержит уже реализованные Registry gateway и приём snapshot-данных, поэтому он является релевантным примером общей локальной платформы, но не частью Cabinet и не источником PresuPro-модели.
Status: confirmed
Repository: `/home/smirnov/jestor_VBC/exp_vbc/demo/code_factory`
Path: `projects/client_portal_sandbox/adapters/registry_gateway.py`; `projects/client_portal_sandbox/application/snapshot_import.py`; `projects/client_portal_sandbox/api/router.py`
Symbol: `get_project_context`, `validate_project_reference`, `import_snapshot`, `publish_snapshot_endpoint`
Evidence: Registry gateway выполняет HTTP GET (`registry_gateway.py:51-84,121-151`); snapshot endpoint смонтирован как `POST /integrations/estimate-snapshots` (`api/router.py:136-137,307-317`).
Implication for Cabinet Backend: это доказательство существования HTTP и snapshot-паттернов в локальной платформе, но не готовый Cabinet-адаптер.

Finding: в рабочем дереве доступны реальные SQLite-файлы с локальными данными.
Status: confirmed
Repository: `/home/smirnov/jestor_VBC/exp_vbc/demo/code_factory`
Path: `projects/registry_sandbox/data/registry.sqlite3`; `projects/PresuPro_sandbox/data/estimate_prices.sqlite3`
Symbol: read-only SQLite inspection
Evidence: Registry DB: таблицы `projects`, `rooms`, `artifacts`, одна запись проекта со статусом `active`; PresuPro DB: две сметы со статусом `accepted`, одна содержит непустой `registry_project`. Проверка выполнена через SQLite URI `mode=ro` без изменения данных.
Implication for Cabinet Backend: локальные данные существуют, но прямой доступ к этим БД не является опубликованной межсервисной границей.

## 2. Registry findings

Finding: каноническая хранимая модель карточки проекта называется `ProjectRecord`; подробный HTTP-ответ называется `ProjectResponse`, а компактные проекции — `ProjectSummary`, `ProjectReference` и `ProjectContext`.
Status: confirmed
Repository: Code Factory / `registry_sandbox`
Path: `projects/registry_sandbox/core/models.py`
Symbol: `ProjectRecord`, `ProjectResponse`, `ProjectSummary`, `ProjectReference`, `ProjectContext`
Evidence: `ProjectRecord` определён в строках 66-73; `ProjectSummary` — 76-81; `ProjectResponse` — 84-86; `ProjectReference` — 111-114; `ProjectContext` — 117-122.
Implication for Cabinet Backend: нельзя называть одну из компактных проекций полной карточкой; поля зависят от выбранного endpoint.

Finding: идентификатор проекта — Python/Pydantic `UUID`; по HTTP он сериализуется как каноническая UUID-строка, а в SQLite хранится как `TEXT PRIMARY KEY`.
Status: confirmed
Repository: Code Factory / `registry_sandbox`
Path: `projects/registry_sandbox/core/models.py`; `projects/registry_sandbox/infra/registry/sqlite_repository.py`
Symbol: `ProjectRecord.id`, `ProjectReference.project_id`, `projects.id`
Evidence: `core/models.py:66-73,111-114`; SQLite DDL `sqlite_repository.py:12-21`; сериализация и чтение UUID `sqlite_repository.py:241-250,279-287`.
Implication for Cabinet Backend: безопасный тип на границе — UUID, передаваемый в JSON как строка; произвольная строка не соответствует Registry-контракту.

Finding: полная карточка `ProjectRecord` требует `id`, `name`, `address`, `status`, `created_at`, `updated_at`; `customer_ref` необязателен. Модель запрещает лишние поля и является immutable.
Status: confirmed
Repository: Code Factory / `registry_sandbox`
Path: `projects/registry_sandbox/core/models.py`
Symbol: `_FrozenModel`, `ProjectRecord`
Evidence: `core/models.py:8-9,66-73`.
Implication for Cabinet Backend: отображаемое имя — `name`; адрес/контекст — обязательный `address`; ссылка на заказчика — nullable `customer_ref` без доказанного внешнего типа или FK.

Finding: на платформенной компактной границе отображаемое имя называется `display_name`, а временной маркер изменения Registry — `registry_updated_at`.
Status: confirmed
Repository: Code Factory / `registry_sandbox`
Path: `projects/registry_sandbox/core/models.py`; `projects/registry_sandbox/services/registry/project_service.py`
Symbol: `ProjectReference`, `ProjectContext`, `get_project_context`
Evidence: поля `core/models.py:111-122`; проекция `name -> display_name`, `updated_at -> registry_updated_at` в `project_service.py:64-76`.
Implication for Cabinet Backend: для интеграционного контекста можно безопасно использовать `project.project_id`, `project.display_name`, `address`, `customer_ref`, `created_at`, `registry_updated_at`.

Finding: Registry допускает ровно два статуса проекта: `active` и `archived`.
Status: confirmed
Repository: Code Factory / `registry_sandbox`
Path: `projects/registry_sandbox/domain/registry/rules.py`; `projects/registry_sandbox/infra/registry/sqlite_repository.py`
Symbol: `ALLOWED_PROJECT_STATUSES`, `projects.status`
Evidence: allowlist `rules.py:17-20`; SQLite CHECK `sqlite_repository.py:13-20`.
Implication for Cabinet Backend: `active` означает активный проект; `archived` — архивный и неактивный. Отдельных `closed` и `deleted` статусов нет.

Finding: закрытый и удалённый статусы, soft-delete marker и delete endpoint не найдены.
Status: not_found
Repository: Code Factory / `registry_sandbox`
Path: `projects/registry_sandbox/domain/registry/rules.py`; `projects/registry_sandbox/api/runtime.py`; `projects/registry_sandbox/infra/registry/sqlite_repository.py`
Symbol: status policy and registered `/projects` routes
Evidence: status allowlist содержит только `active`, `archived` (`rules.py:17-20`); HTTP routes `runtime.py:54-104` не содержат delete; таблица `projects` не содержит deleted/closed поля (`sqlite_repository.py:13-21`).
Implication for Cabinet Backend: нельзя выводить семантику closed/deleted из текущего Registry.

Finding: архивирование изменяет существующую запись на `status="archived"` и обновляет `updated_at`; отдельная историческая revision не создаётся.
Status: confirmed
Repository: Code Factory / `registry_sandbox`
Path: `projects/registry_sandbox/infra/registry/project_store.py`
Symbol: `archive_project_record`
Evidence: `project_store.py:53-57` выполняет `model_copy(update={"status": "archived", "updated_at": utc_now()})`, затем replace/upsert.
Implication for Cabinet Backend: архивирование наблюдается как обновление текущей карточки, не как новая версия.

Finding: у карточки проекта есть `created_at` и `updated_at`, но нет revision, version или content hash.
Status: confirmed
Repository: Code Factory / `registry_sandbox`
Path: `projects/registry_sandbox/core/models.py`; `projects/registry_sandbox/infra/registry/sqlite_repository.py`
Symbol: `ProjectRecord`, `projects` table
Evidence: модель `core/models.py:66-73` и DDL `sqlite_repository.py:13-21` содержат только две временные метки; version/hash отсутствуют. Поле `version` существует только у другой модели `ProjectArtifact` (`core/models.py:97-108`).
Implication for Cabinet Backend: `updated_at`/`registry_updated_at` — единственный доступный признак изменения карточки, но это не monotonic revision и не content hash.

Finding: список проектов доступен через `GET /projects`; по умолчанию архивные исключены, `include_archived=true` возвращает и их. Порядок — `updated_at` по убыванию, затем строковый UUID.
Status: confirmed
Repository: Code Factory / `registry_sandbox`
Path: `projects/registry_sandbox/api/runtime.py`; `projects/registry_sandbox/infra/registry/project_store.py`; `projects/registry_sandbox/services/registry/project_service.py`
Symbol: `list_projects`, `list_project_records`
Evidence: route/query `runtime.py:58-60`; фильтр и сортировка `project_store.py:82-87`; проекция ответа `project_service.py:97-108`.
Implication for Cabinet Backend: обычный список не является полным историческим перечнем; для архивных требуется явный `include_archived=true`.

Finding: все активные проекты доступны отдельным endpoint `GET /projects/active` с ответом `list[ProjectReference]`.
Status: confirmed
Repository: Code Factory / `registry_sandbox`
Path: `projects/registry_sandbox/api/runtime.py`; `projects/registry_sandbox/services/registry/project_service.py`; `projects/registry_sandbox/tests/test_project_identity_boundaries.py`
Symbol: `list_active_projects`, `list_active_projects_endpoint`
Evidence: route `runtime.py:62-64`; точный фильтр `status == "active"` и проекция `project_service.py:79-89`; HTTP-тест ответа `test_project_identity_boundaries.py:108-116`.
Implication for Cabinet Backend: это существующая узкая граница для получения всех активных карточек без дополнительной фильтрации.

Finding: фильтрации списка по пользователю, компании, клиенту или произвольному статусу нет; поддержан только `include_archived: bool`, плюс отдельный active endpoint.
Status: not_found
Repository: Code Factory / `registry_sandbox`
Path: `projects/registry_sandbox/api/runtime.py`; `projects/registry_sandbox/api/registry/router.py`; `projects/registry_sandbox/infra/registry/project_store.py`
Symbol: `list_projects`, `list_projects_endpoint`, `list_project_records`
Evidence: сигнатуры `runtime.py:58-60`, `router.py:48-50`, `project_store.py:82-87` принимают только `include_archived`; иных условий нет.
Implication for Cabinet Backend: user/company/status filters нельзя считать частью Registry API.

Finding: отсутствующий проект имеет две фактические формы результата: detail/context endpoint возвращает HTTP 404 `{"detail":"Project not found: <uuid>"}`, а validate endpoint возвращает HTTP 200 с `exists=false`, `status=null`, `is_active=false`, `failure="not_found"`.
Status: confirmed
Repository: Code Factory / `registry_sandbox`
Path: `projects/registry_sandbox/infra/registry/project_store.py`; `projects/registry_sandbox/api/runtime.py`; `projects/registry_sandbox/services/registry/project_service.py`; `projects/registry_sandbox/tests/test_project_identity_boundaries.py`
Symbol: `get_project_record`, `handle_lookup_error`, `validate_project_reference`
Evidence: LookupError `project_store.py:75-79`; 404 mapping `runtime.py:42-44`; validate shape `project_service.py:154-164`; HTTP assertions `test_project_identity_boundaries.py:147-155`.
Implication for Cabinet Backend: not-found handling зависит от выбранного endpoint; validate нельзя трактовать как 404-only контракт.

Finding: существующий архивный проект исчезает из обычного списка, но остаётся в текущей таблице, доступен по id и возвращается при `include_archived=true`; отдельной истории изменений нет.
Status: partial
Repository: Code Factory / `registry_sandbox`
Path: `projects/registry_sandbox/infra/registry/project_store.py`; `projects/registry_sandbox/infra/registry/sqlite_repository.py`
Symbol: `list_project_records`, `get_project_record`, `_upsert_project`
Evidence: обычный список отбрасывает `archived` (`project_store.py:82-87`), get читает ту же запись (`project_store.py:75-79`), upsert перезаписывает текущее состояние (`sqlite_repository.py:120-133`). Исторической таблицы/revision log нет.
Implication for Cabinet Backend: «исчез из обычного списка» возможно при архивировании; «остаётся в истории» подтвердить нельзя — он остаётся только текущей архивной записью.

## 3. PresuPro findings

Finding: фактическая модель сметы называется `Estimate`; `estimate_id` — поле `Estimate.id` типа `str`.
Status: confirmed
Repository: Code Factory / `PresuPro_sandbox`
Path: `projects/PresuPro_sandbox/core/models.py`; `projects/PresuPro_sandbox/backend/core/config.py`
Symbol: `Estimate`, `make_id`
Evidence: `Estimate.id: str` (`core/models.py:77-90`); генератор создаёт `est_<8 hex>` (`backend/core/config.py:39-43`), но create request также разрешает caller-supplied `id: str | None` (`core/models.py:122-131`).
Implication for Cabinet Backend: `estimate_id` надо сохранять как opaque string; UUID-гарантии у PresuPro нет.

Finding: поля `Estimate` — обязательные `id`, `client_name`, `project_type`, `created_at`, `updated_at`; `zones` default `[]`, `status` default `draft`, `iva_percent` default `21.0`, `notes` default empty, `client`/`invoice_ref`/`registry_project` nullable, `locked` default false.
Status: confirmed
Repository: Code Factory / `PresuPro_sandbox`
Path: `projects/PresuPro_sandbox/core/models.py`
Symbol: `Estimate`
Evidence: `core/models.py:77-90`; frozen/extra-forbid policy `core/models.py:8-9`.
Implication for Cabinet Backend: это текущая точная форма сметы; totals не встроены в `Estimate` и запрашиваются/считаются отдельно.

Finding: связь с Registry не хранится как отдельное поле `Estimate.project_id`; она сохраняется внутри nullable `Estimate.registry_project: RegistryProjectSnapshot`, где `project_id` имеет тип `str`.
Status: confirmed
Repository: Code Factory / `PresuPro_sandbox`
Path: `projects/PresuPro_sandbox/core/models.py`; `projects/PresuPro_sandbox/backend/storage/estimates.py`
Symbol: `Estimate.registry_project`, `RegistryProjectSnapshot`, `upsert_estimate`
Evidence: `core/models.py:77-90,194-201`; snapshot JSON сериализуется в колонки `registry_project` и `registry_project_json` (`storage/estimates.py:109-120,124-167`).
Implication for Cabinet Backend: нельзя строить SQL/API-предположение о first-class `project_id` в смете; текущая связь — immutable embedded snapshot.

Finding: при создании связанной сметы публичный request принимает `project_id: UUID | None`; сервер валидирует Registry и сам формирует snapshot. Клиентский `registry_project` запрещён.
Status: confirmed
Repository: Code Factory / `PresuPro_sandbox`
Path: `projects/PresuPro_sandbox/core/models.py`; `projects/PresuPro_sandbox/backend/api/routes.py`; `projects/PresuPro_sandbox/backend/adapters/registry.py`
Symbol: `CreateEstimateRequest`, `create_estimate_endpoint`, `resolve_registry_project`
Evidence: request fields `core/models.py:122-132`; server-side enforcement `routes.py:73-89`; validate/context calls и snapshot projection `registry.py:10-101`; tests `tests/test_registry_project_integration.py:54-92,94-114`.
Implication for Cabinet Backend: связь создаётся только в момент создания сметы и фиксирует контекст Registry на тот момент.

Finding: один Registry-проект структурно может иметь несколько смет: primary key — только `estimates.id`, а snapshot project_id не уникален и хранится в JSON.
Status: confirmed
Repository: Code Factory / `PresuPro_sandbox`
Path: `projects/PresuPro_sandbox/backend/storage/schema.py`; `projects/PresuPro_sandbox/backend/storage/estimates.py`
Symbol: `estimates` table, `upsert_estimate`
Evidence: DDL `storage/schema.py:50-68` объявляет только `id TEXT PRIMARY KEY`; `registry_project` — обычный TEXT без UNIQUE/FK; upsert конфликтует только по `id` (`storage/estimates.py:124-148`).
Implication for Cabinet Backend: нельзя предполагать отношение project→single estimate или автоматически выбирать одну смету.

Finding: backend гарантирует только начальный `draft` и допуск к Holded-конвертации только из `accepted`; поле status технически является неограниченным `str`.
Status: partial
Repository: Code Factory / `PresuPro_sandbox`
Path: `projects/PresuPro_sandbox/core/models.py`; `projects/PresuPro_sandbox/backend/services/estimates.py`; `projects/PresuPro_sandbox/backend/services/invoicing.py`
Symbol: `Estimate.status`, `estimate_from_request`, `_ALLOWED_STATUS_FOR_CONVERSION`
Evidence: `status: str = 'draft'` (`core/models.py:82`); create принудительно ставит `draft` (`services/estimates.py:71-92`); update принимает любое `str` (`core/models.py:134-142`, `services/estimates.py:94-116`); conversion allowlist — только `accepted` (`services/invoicing.py:8-9,76-83`).
Implication for Cabinet Backend: `draft` и `accepted` имеют подтверждённое поведение; полный enum не обеспечивается backend validation.

Finding: UI и accepted spec перечисляют `draft`, `sent`, `accepted`, `rejected`, `archived`, но backend не валидирует этот список. Отдельных «current», «working», «approved» или «published» признаков у `Estimate` нет.
Status: partial
Repository: Code Factory / `PresuPro_sandbox`
Path: `projects/PresuPro_sandbox/frontend/engine.js`; `projects/PresuPro_sandbox/specs/base/global_spec.json`; `projects/PresuPro_sandbox/core/models.py`
Symbol: `ESTIMATE_STATUSES`, `rules.estimate_statuses`, `Estimate.status`
Evidence: frontend `engine.js:7-19`; spec `global_spec.json:842-848`; backend field остаётся unrestricted `str` (`core/models.py:77-90`). Поиск моделей и сервисов не нашёл current/working/approved/published flag.
Implication for Cabinet Backend: нельзя безопасно определять «текущую/рабочую/утверждённую/опубликованную» смету сверх факта `accepted`; выбор среди нескольких смет не определён.

Finding: у сметы есть строковые ISO-like `created_at` и `updated_at`, но нет revision, version или content hash; update перезаписывает одну строку.
Status: confirmed
Repository: Code Factory / `PresuPro_sandbox`
Path: `projects/PresuPro_sandbox/core/models.py`; `projects/PresuPro_sandbox/backend/services/estimates.py`; `projects/PresuPro_sandbox/backend/storage/estimates.py`
Symbol: `Estimate`, `estimate_from_request`, `upsert_estimate`
Evidence: поля `core/models.py:77-90`; update сохраняет `id`/`created_at` и обновляет `updated_at` (`services/estimates.py:94-116`); SQLite `ON CONFLICT(id) DO UPDATE` (`storage/estimates.py:124-167`).
Implication for Cabinet Backend: `updated_at` — лишь изменяемая метка времени; стабильной ревизии/хеша для проверки сохранённой ссылки нет.

Finding: модель зоны называется `EstimateZone` и содержит `name`, nullable `area_m2`, nullable `wall_m2`, `items`; стабильного zone ID/code нет.
Status: confirmed
Repository: Code Factory / `PresuPro_sandbox`
Path: `projects/PresuPro_sandbox/core/models.py`; `projects/PresuPro_sandbox/backend/storage/mappers.py`
Symbol: `EstimateZone`, `row_to_estimate`
Evidence: `core/models.py:70-74`; mapper восстанавливает только эти поля `storage/mappers.py:46-54`.
Implication for Cabinet Backend: имя и индекс зоны — локаторы, не стабильная идентичность между обновлениями.

Finding: модель позиции называется `EstimateItem`; обязательны `type`, `qty >= 0`, `unit`; `name`, `material_id`, `unit_price`, `source_store`, `iva_percent` nullable; waste/margin/discount default `0.0`. Поля description и item ID нет.
Status: confirmed
Repository: Code Factory / `PresuPro_sandbox`
Path: `projects/PresuPro_sandbox/core/models.py`; `projects/PresuPro_sandbox/backend/storage/mappers.py`
Symbol: `EstimateItem`, `row_to_estimate`
Evidence: точные поля `core/models.py:56-67`; mapper `storage/mappers.py:27-44` не добавляет идентификатор или description.
Implication for Cabinet Backend: `material_id` — ссылка на материал, а не идентификатор строки; сохранить безопасную ссылку на конкретную позицию между обновлениями нельзя.

Finding: totals вычисляются отдельно в `EstimateTotals`: materials/labor subtotals, discount, margin, taxable subtotal, IVA total/breakdown и grand total.
Status: confirmed
Repository: Code Factory / `PresuPro_sandbox`
Path: `projects/PresuPro_sandbox/core/models.py`; `projects/PresuPro_sandbox/backend/services/estimates.py`
Symbol: `EstimateTotals`, `calculate_estimate_totals`
Evidence: модель `core/models.py:93-102`; формула учитывает qty+waste, скидку, margin, per-line или estimate IVA (`services/estimates.py:17-68,119-130`).
Implication for Cabinet Backend: итоговые суммы следует читать через существующий totals endpoint, а не ожидать их внутри Estimate или суммировать только `qty * unit_price`.

Finding: получить все сметы можно `GET /estimates`, с опциональными точными фильтрами `client_name` и `status`; получить одну — `GET /estimates/{estimate_id}`.
Status: confirmed
Repository: Code Factory / `PresuPro_sandbox`
Path: `projects/PresuPro_sandbox/backend/api/routes.py`; `projects/PresuPro_sandbox/backend/storage/estimates.py`
Symbol: `list_estimates_endpoint`, `get_estimate_endpoint`, `list_estimates`, `get_estimate`
Evidence: endpoint functions `routes.py:69-70,92-96`; mounted routes `routes.py:225-230`; SQL filters/order `storage/estimates.py:24-53`.
Implication for Cabinet Backend: существующая HTTP-граница поддерживает lookup по estimate_id и общий список, но не project-scoped lookup.

Finding: endpoint/фильтр списка смет по `project_id` отсутствует.
Status: not_found
Repository: Code Factory / `PresuPro_sandbox`
Path: `projects/PresuPro_sandbox/backend/api/routes.py`; `projects/PresuPro_sandbox/backend/storage/estimates.py`; `projects/PresuPro_sandbox/mcp/presupro_mcp_server.py`
Symbol: `list_estimates_endpoint`, `list_estimates`, PresuPro MCP tools
Evidence: list принимает только `client_name`, `status` (`routes.py:69-70`; `storage/estimates.py:36-53`); routes `225-235` не содержат project lookup; MCP tools `presupro_mcp_server.py:248-310` не передают/не фильтруют `project_id`.
Implication for Cabinet Backend: поиск смет проекта сейчас потребует чтения общего списка и проверки embedded snapshot на стороне потребителя; опубликованного project-scoped контракта нет.

Finding: отсутствующая смета возвращает HTTP 404 `detail="Estimate not found"`; storage-level `get_estimate` возвращает `None`.
Status: confirmed
Repository: Code Factory / `PresuPro_sandbox`
Path: `projects/PresuPro_sandbox/backend/storage/estimates.py`; `projects/PresuPro_sandbox/backend/api/routes.py`
Symbol: `get_estimate`, `get_estimate_endpoint`
Evidence: `storage/estimates.py:24-31`; `routes.py:92-96`.
Implication for Cabinet Backend: HTTP consumer может нормализовать 404 как отсутствие сметы; пустой список по project_id не определён, потому что такого endpoint нет.

Finding: поведение при нескольких сметах одного проекта не определено; общий список вернёт все записи по `updated_at DESC`, но текущую выбирать не умеет.
Status: not_found
Repository: Code Factory / `PresuPro_sandbox`
Path: `projects/PresuPro_sandbox/backend/storage/estimates.py`; `projects/PresuPro_sandbox/backend/api/routes.py`
Symbol: `list_estimates`, `list_estimates_endpoint`
Evidence: `storage/estimates.py:36-53` возвращает все совпадения общего фильтра и сортирует только по updated_at; нет project filter, uniqueness/current selector.
Implication for Cabinet Backend: автоматический выбор «текущей сметы проекта» не имеет подтверждённого контракта.

Finding: обновление заменяет весь список zones, а item/zone ID отсутствуют; поэтому ссылка на позицию по индексу или имени может сместиться/исчезнуть.
Status: confirmed
Repository: Code Factory / `PresuPro_sandbox`
Path: `projects/PresuPro_sandbox/core/models.py`; `projects/PresuPro_sandbox/backend/services/estimates.py`; `projects/PresuPro_sandbox/backend/storage/estimates.py`
Symbol: `UpdateEstimateRequest.zones`, `update_estimate`, `upsert_estimate`
Evidence: `zones: list[EstimateZone] | None` (`core/models.py:134-142`); нормализация полностью нового списка `services/estimates.py:150-203`; сериализация/replace `storage/estimates.py:82-91,132-147`.
Implication for Cabinet Backend: безопасная долговременная ссылка на конкретную позицию сметы сейчас невозможна; это явный missing contract.

## 4. Holded Gateway findings

Finding: отдельный сервис или спецификация `Holded Gateway` не найдены; существует встроенный PresuPro adapter `backend.adapters.holded` и orchestration `backend.services.invoicing`.
Status: partial
Repository: Code Factory / `PresuPro_sandbox`
Path: `projects/PresuPro_sandbox/backend/adapters/holded.py`; `projects/PresuPro_sandbox/backend/services/invoicing.py`; `projects/PresuPro_sandbox/backend/api/routes.py`
Symbol: `create_holded_document`, `convert_estimate_to_invoice`, `convert_estimate_endpoint`
Evidence: adapter POST implementation `holded.py:40-84`; service orchestration `invoicing.py:76-123`; public PresuPro route `POST /estimates/{estimate_id}/convert` (`routes.py:125-131,232-233`). Repo-wide scoped search по `holded` не обнаружил отдельного gateway package/service вне PresuPro.
Implication for Cabinet Backend: нельзя ссылаться на самостоятельный Holded Gateway как на существующий сервис; доступна только PresuPro-owned интеграция.

Finding: команда публикации — PresuPro `POST /estimates/{estimate_id}/convert` с query-параметрами `doc_type` и `allow_zero_prices`; фактический ответ — обновлённый `Estimate`, не отдельная receipt model.
Status: confirmed
Repository: Code Factory / `PresuPro_sandbox`
Path: `projects/PresuPro_sandbox/backend/api/routes.py`; `projects/PresuPro_sandbox/backend/services/invoicing.py`
Symbol: `convert_estimate_endpoint`, `convert_estimate_to_invoice`
Evidence: сигнатура и mapping ошибок `routes.py:125-131`; route registration `routes.py:232-233`; service returns `upsert_estimate(updated_estimate)` (`invoicing.py:118-123`).
Implication for Cabinet Backend: опубликованный результат надо извлекать из `Estimate.invoice_ref`; общей gateway receipt сейчас нет.

Finding: вход в Holded строится из `Estimate`, `EstimateTotals`, material map и optional contact ID; разрешены doc types `estimate`, `invoice`, `proform`.
Status: confirmed
Repository: Code Factory / `PresuPro_sandbox`
Path: `projects/PresuPro_sandbox/backend/adapters/holded.py`
Symbol: `estimate_to_holded_payload`, `resolve_invoicing_doc_type`
Evidence: doc type allowlist `holded.py:10-17,197-201`; payload fields date/currency/items/contact_id/notes `holded.py:87-124`.
Implication for Cabinet Backend: это PresuPro→Holded payload mapping; оно не является универсальным Cabinet DTO.

Finding: выходная модель ссылки называется `InvoiceRef` и содержит `provider`, `doc_type`, обязательный `external_id`, optional `number`, `url`, `status`, `synced_at`.
Status: confirmed
Repository: Code Factory / `PresuPro_sandbox`
Path: `projects/PresuPro_sandbox/core/models.py`; `projects/PresuPro_sandbox/backend/adapters/holded.py`
Symbol: `InvoiceRef`, `create_holded_document`
Evidence: модель `core/models.py:175-182`; response mapping Holded `id -> external_id` и остальные поля `holded.py:66-84`.
Implication for Cabinet Backend: внешний Holded document ID действительно сохраняется, но только после успешной локальной фиксации обновлённой сметы.

Finding: credential берётся из environment variable `HOLDED_API_KEY` и отправляется как `Authorization: Bearer <key>`.
Status: confirmed
Repository: Code Factory / `PresuPro_sandbox`
Path: `projects/PresuPro_sandbox/backend/adapters/holded.py`
Symbol: `HOLDED_API_KEY_ENV`, `build_holded_headers`
Evidence: `holded.py:10,25-37`. В `/home/smirnov/jestor_VBC/.env` файл существует, но его содержимое не читалось и фактическое наличие ключа не подтверждалось.
Implication for Cabinet Backend: место runtime-чтения credential подтверждено; секрет не принадлежит Cabinet-коду и не должен копироваться в отчёт/модель.

Finding: idempotency key в запросе Holded отсутствует. Реализована только локальная short-circuit идемпотентность, если `estimate.invoice_ref` уже сохранён.
Status: partial
Repository: Code Factory / `PresuPro_sandbox`
Path: `projects/PresuPro_sandbox/backend/services/invoicing.py`; `projects/PresuPro_sandbox/backend/adapters/holded.py`
Symbol: `convert_estimate_to_invoice`, `create_holded_document`
Evidence: existing ref немедленно возвращает estimate (`invoicing.py:89-90`); Holded headers содержат только Accept, Content-Type, Authorization (`holded.py:25-37`), payload/request не содержит idempotency key (`holded.py:40-50,87-124`).
Implication for Cabinet Backend: повтор безопасен только после успешного сохранения `invoice_ref`; сетевой ambiguous outcome не защищён provider idempotency.

Finding: успех — HTTP 2xx с обязательным response `id`; HTTP/URL ошибки становятся `RuntimeError`. Типизированных статусов success/error/unknown outcome или отдельной квитанции нет.
Status: partial
Repository: Code Factory / `PresuPro_sandbox`
Path: `projects/PresuPro_sandbox/backend/adapters/holded.py`
Symbol: `create_holded_document`
Evidence: exception mapping и 2xx check `holded.py:52-68`; успешный `InvoiceRef` `holded.py:70-84`.
Implication for Cabinet Backend: невозможно отличить «Holded точно не принял» от «ответ потерян после принятия» по существующему контракту.

Finding: retry, reconciliation, поиск созданного документа после timeout и durable outbox/state machine не найдены.
Status: not_found
Repository: Code Factory / `PresuPro_sandbox`
Path: `projects/PresuPro_sandbox/backend/adapters/holded.py`; `projects/PresuPro_sandbox/backend/services/invoicing.py`; `projects/PresuPro_sandbox/backend/storage/estimates.py`
Symbol: Holded adapter/invoicing/storage scoped search
Evidence: provider call один (`invoicing.py:99-103`), затем локальное сохранение (`invoicing.py:108-123`); нет retry/reconcile symbols или таблиц попыток. Scoped search по `idempot`, `retry`, `reconcil`, `timeout` в этих файлах не нашёл соответствующего механизма.
Implication for Cabinet Backend: безопасную автоматическую повторную публикацию после неопределённого исхода подтвердить нельзя.

Finding: Holded `urlopen` вызывается без timeout, хотя accepted spec/config декларирует `request_timeout_seconds: 30`.
Status: partial
Repository: Code Factory / `PresuPro_sandbox`
Path: `projects/PresuPro_sandbox/backend/adapters/holded.py`; `projects/PresuPro_sandbox/backend/core/config.py`; `projects/PresuPro_sandbox/specs/base/global_spec.json`
Symbol: `create_holded_document`, `find_or_create_holded_contact`, `Settings.request_timeout_seconds`
Evidence: `urllib.request.urlopen(req)` без timeout в `holded.py:52-56,142-146,177-181`; settings поле/default `backend/core/config.py:10-35`; spec config `global_spec.json:590-594`.
Implication for Cabinet Backend: timeout-after-possible-acceptance не только не reconciled, но и bounded timeout фактически не подключён к Holded document/contact calls.

Finding: исправление или повторная публикация уже созданного документа не реализованы; при наличии `invoice_ref` conversion просто возвращает существующую смету.
Status: not_found
Repository: Code Factory / `PresuPro_sandbox`
Path: `projects/PresuPro_sandbox/backend/services/invoicing.py`; `projects/PresuPro_sandbox/backend/adapters/holded.py`; `projects/PresuPro_sandbox/backend/api/routes.py`
Symbol: `convert_estimate_to_invoice`, Holded routes/search
Evidence: short-circuit `invoicing.py:89-90`; adapter содержит GET/POST contact и POST document, но не update/correct document (`holded.py:40-201`); единственный public action — `/convert` (`routes.py:232-233`).
Implication for Cabinet Backend: correction/republish нельзя считать доступной возможностью.

Finding: текущая ответственность PresuPro — проверить accepted estimate/client/prices, найти/создать Holded contact, создать документ, сохранить `InvoiceRef` и lock сметы. Отдельной Cabinet↔Gateway границы нет.
Status: confirmed
Repository: Code Factory / `PresuPro_sandbox`; Cabinet repository
Path: `projects/PresuPro_sandbox/backend/services/invoicing.py`; `projects/Cabinet_web` scoped search
Symbol: `convert_estimate_to_invoice`
Evidence: orchestration `invoicing.py:76-123`; в Cabinet scoped search нет runtime Holded adapter/gateway.
Implication for Cabinet Backend: фактически существующая граница заканчивается в PresuPro `/convert`; ответственность Cabinet в отношении Holded кодом не определена.

## 5. Local platform integration findings

Finding: PresuPro обращается к Registry по HTTP через специальный adapter, а не через Python imports, файл или общую БД.
Status: confirmed
Repository: Code Factory / `PresuPro_sandbox`
Path: `projects/PresuPro_sandbox/backend/adapters/registry.py`
Symbol: `resolve_registry_project`
Evidence: `httpx.get` к `/projects/{id}/validate` и `/projects/{id}/context` с timeout 5 s (`registry.py:10-58`); response shape/identity validation `registry.py:60-101`.
Implication for Cabinet Backend: Registry уже имеет пригодную внутреннюю HTTP-границу; прямой импорт Registry Python-модулей не требуется.

Finding: Registry discovery в PresuPro — статический base URL из `REGISTRY_API_URL`; service discovery/registry/DNS abstraction нет.
Status: confirmed
Repository: Code Factory / `PresuPro_sandbox`
Path: `projects/PresuPro_sandbox/backend/adapters/registry.py`
Symbol: `resolve_registry_project`
Evidence: `os.getenv("REGISTRY_API_URL")` и ошибка при отсутствии (`registry.py:10-15`).
Implication for Cabinet Backend: существующий способ обнаружения Registry — конфигурация URL, не динамическое service discovery.

Finding: Registry и PresuPro HTTP API не требуют аутентификацию в текущих runtime routes.
Status: confirmed
Repository: Code Factory / `registry_sandbox`, `PresuPro_sandbox`
Path: `projects/registry_sandbox/api/runtime.py`; `projects/PresuPro_sandbox/backend/api/routes.py`; `projects/PresuPro_sandbox/frontend/api.js`
Symbol: `create_app`, request client
Evidence: Registry routes используют только path/query/body и DB dependency (`runtime.py:50-104`); PresuPro routes не устанавливают auth dependency (`routes.py:198-244`); frontend явно omits credentials как single-user local backend (`frontend/api.js:26-38`).
Implication for Cabinet Backend: auth нельзя считать частью этих двух текущих границ; при этом это не разрешение обходить auth в других сервисах.

Finding: PresuPro имеет thin MCP client поверх своего HTTP API; он не импортирует product modules и использует `PRESUPRO_API_URL` с default `http://127.0.0.1:8000`.
Status: confirmed
Repository: Code Factory / `PresuPro_sandbox`
Path: `projects/PresuPro_sandbox/mcp/presupro_mcp_server.py`
Symbol: `_request`, MCP tools
Evidence: module contract `presupro_mcp_server.py:1-10`; base URL `:30-35`; HTTP client `:40-53`; estimate tools `:248-310`.
Implication for Cabinet Backend: существующий reusable transport boundary — PresuPro HTTP; MCP является operator/client wrapper, но не поддерживает project-scoped estimate lookup и даже не передаёт project_id при create.

Finding: Registry frontend также использует HTTP; base URL задаётся `VITE_REGISTRY_API_BASE_URL`, либо запрос идёт same-origin/Vite proxy.
Status: confirmed
Repository: Code Factory / `registry_sandbox`
Path: `projects/registry_sandbox/frontend/src/shared/config.ts`; `projects/registry_sandbox/frontend/src/api/http.ts`; `projects/registry_sandbox/frontend/vite.config.ts`
Symbol: `REGISTRY_API_BASE_URL`, `requestJson`, Vite proxy
Evidence: config `shared/config.ts:1-2`; fetch `api/http.ts:9-34`; proxy `/projects -> http://127.0.0.1:8000` (`vite.config.ts:4-14`).
Implication for Cabinet Backend: HTTP — фактический способ обращения frontend к Registry; порт зависит от конфигурации и сейчас не полностью согласован.

Finding: documented/manual Registry backend port — `8010`; PresuPro `main()` default — `8000`, а отдельные локальные инструкции используют `8017`. Единого портового реестра нет.
Status: partial
Repository: Code Factory / `registry_sandbox`, `PresuPro_sandbox`
Path: `projects/registry_sandbox/README.md`; `projects/registry_sandbox/frontend/vite.config.ts`; `projects/PresuPro_sandbox/backend/main.py`; `projects/PresuPro_sandbox/frontend/README.md`
Symbol: run commands / server configuration
Evidence: Registry README `:7-25` говорит backend `8010`, Vite proxy указывает `8000` (`vite.config.ts:7-12`); PresuPro `main.py:10-11` запускает `8000`, frontend README использует `8017` (`frontend/README.md:5-10`).
Implication for Cabinet Backend: адреса должны поступать из конфигурации; hard-coded «общий локальный порт» не подтверждён.

Finding: общий launcher `projects/start-full-saas.sh` существует, но запускает только Planspec и Panelforge; Registry, PresuPro, Client Portal и Cabinet в него не входят.
Status: partial
Repository: Code Factory
Path: `projects/start-full-saas.sh`; `projects/status-full-saas.sh`; `projects/stop-full-saas.sh`
Symbol: `start_service`, full SaaS scripts
Evidence: start list `start-full-saas.sh:78-109`; status targets `status-full-saas.sh:36-57`; stop работает по PID directory `stop-full-saas.sh:4-24`.
Implication for Cabinet Backend: общего фактического launcher для требуемой цепочки Registry→PresuPro→Cabinet нет.

Finding: Docker Compose, supervisor или systemd unit для совместного запуска Registry/PresuPro/Cabinet не найдены в проверенном workspace.
Status: not_found
Repository: Code Factory and Cabinet repository
Path: workspace scoped file search (`*compose*`, `*launch*`, `*supervisor*`, `*.service`, `*.sh`)
Symbol: runtime launch configuration
Evidence: найденный `deploy/systemd/panelforge-api.service` относится к Panelforge; найденный `projects/start-full-saas.sh` не включает требуемые сервисы; Cabinet Makefile поднимает только static web server.
Implication for Cabinet Backend: готового процесса запуска всей нужной интеграционной цепочки нет.

Finding: Client Portal имеет второй HTTP Registry adapter, настроенный через `REGISTRY_BASE_URL`, с типизированными timeout/transport/schema/identity errors.
Status: confirmed
Repository: Code Factory / `client_portal_sandbox`
Path: `projects/client_portal_sandbox/adapters/registry_gateway.py`; `projects/client_portal_sandbox/core/models.py`
Symbol: `RegistryBoundaryError`, `RegistryFailureKind`, Registry gateway functions
Evidence: URL validation/config `registry_gateway.py:14-32`; GET и failure mapping `:51-84,121-151`; enum failure kinds `core/models.py:134-150`.
Implication for Cabinet Backend: платформа уже демонстрирует явный adapter boundary; готового импортируемого общего SDK при этом нет.

Finding: Python imports между приложениями не являются безопасной общей границей: Registry и PresuPro оба используют top-level package `core`, что вызывает collision при совместной pytest collection.
Status: confirmed
Repository: Code Factory / `registry_sandbox`, `PresuPro_sandbox`
Path: `projects/registry_sandbox/core/models.py`; `projects/PresuPro_sandbox/core/models.py`; imports в обоих приложениях
Symbol: top-level `core.models`
Evidence: совместный запуск тестов из корня загрузил Registry `core.models` для PresuPro и завершился ImportError `cannot import name 'Client'`; раздельный запуск из project roots прошёл (`Registry 2 passed`, `PresuPro 10 passed`).
Implication for Cabinet Backend: прямой in-process import обоих приложений фактически конфликтует; проверенная граница — отдельные процессы/HTTP.

Finding: локальный snapshot exchange уже реализован в Client Portal как authenticated HTTP import с service principal bearer token, version identity и SHA-256 fingerprint.
Status: confirmed
Repository: Code Factory / `client_portal_sandbox`
Path: `projects/client_portal_sandbox/core/models.py`; `projects/client_portal_sandbox/application/snapshot_import.py`; `projects/client_portal_sandbox/api/router.py`; `projects/client_portal_sandbox/adapters/snapshot_import_repository.py`
Symbol: `SnapshotPublication`, `SnapshotImportRecord`, `import_snapshot`, `publish_snapshot_endpoint`
Evidence: models `core/models.py:669-723`; fingerprint `snapshot_import.py:54-90`; replay classification/storage `snapshot_import.py:93-96,198-256`; bearer auth route `api/router.py:307-317`; UNIQUE identity `(project_id, estimate_id, estimate_version)` `snapshot_import_repository.py:13-35`.
Implication for Cabinet Backend: snapshot-механизм существует, но принимает другую, Client-Portal-owned модель и не совпадает с текущим PresuPro `Estimate`.

Finding: текущий PresuPro не публикует `SnapshotPublication` Client Portal: его `Estimate.id` — string, у него нет `estimate_version`, стабильных section IDs/codes и publish endpoint.
Status: not_found
Repository: Code Factory / `PresuPro_sandbox`, `client_portal_sandbox`
Path: `projects/PresuPro_sandbox/core/models.py`; `projects/PresuPro_sandbox/backend/api/routes.py`; `projects/client_portal_sandbox/core/models.py`
Symbol: `Estimate`, PresuPro routes, `SnapshotPublication`
Evidence: PresuPro model `core/models.py:77-90` и routes `routes.py:225-244`; Portal требует UUID `estimate_id`, positive `estimate_version` и section identity (`client_portal_sandbox/core/models.py:669-689`).
Implication for Cabinet Backend: существующий Portal snapshot contract нельзя объявить текущим PresuPro contract или готовым Cabinet integration path.

Finding: в Cabinet runtime-коде нет Registry/PresuPro/Holded client, adapter или gateway; существующая точка размещения интеграционного адаптера не подтверждена кодом.
Status: not_found
Repository: Cabinet
Path: `projects/Cabinet_web/tools`; `projects/Cabinet_web/web`; scoped repository search
Symbol: Cabinet runtime integration boundary
Evidence: scoped search нашёл PresuPro только в документации; `tools/` содержит invoice validation/storage/workflow services, но не external service client; `web/app.js` читает локальный `web/catalog.json`.
Implication for Cabinet Backend: фактически существующей Cabinet integration point нет; указывать конкретный модуль размещения без проектного решения нельзя.

## 6. Confirmed contracts

### Registry: безопасная read-модель для Cabinet

| Endpoint/model | Поле | Тип/формат | Обязательность | Подтверждённая семантика |
| --- | --- | --- | --- | --- |
| `GET /projects/active` / `ProjectReference` | `project_id` | UUID JSON string | required | Registry project identity |
| | `display_name` | string | required | проекция `ProjectRecord.name` |
| | `status` | string | required | для этого endpoint фактически `active` |
| `GET /projects/{id}/context` / `ProjectContext` | `project` | `ProjectReference` | required | identity/display/status |
| | `address` | string | required | адрес/краткий контекст объекта |
| | `customer_ref` | string/null | optional | непрозрачная ссылка на заказчика |
| | `created_at` | datetime JSON string | required | время создания Registry record |
| | `registry_updated_at` | datetime JSON string | required | текущий `ProjectRecord.updated_at` |
| `GET /projects/{id}/validate` / `ProjectValidationResult` | `project_id` | UUID JSON string | required | проверяемая identity |
| | `exists` | boolean | required | существует ли current record |
| | `status` | `active`/`archived`/null | required nullable | null для not found |
| | `is_active` | boolean | required | true только для active |
| | `failure` | null/`not_found`/`archived` | required nullable | нормализованная причина текущей реализации |

### PresuPro: безопасная read-модель сметы

| Model | Поле | Тип/формат | Обязательность | Подтверждённая семантика |
| --- | --- | --- | --- | --- |
| `Estimate` | `id` | string | required | opaque estimate identity; обычно `est_<8hex>`, но caller ID разрешён |
| | `client_name` | string | required | PresuPro-owned display/client name |
| | `project_type` | string | required | тип проекта без backend enum |
| | `zones` | list[`EstimateZone`] | default `[]` | полный mutable список зон |
| | `status` | string | default `draft` | `accepted` требуется для Holded conversion; полный enum runtime не enforced |
| | `created_at`, `updated_at` | string | required | timestamps, не revision |
| | `iva_percent` | float | default 21.0 | default tax rate |
| | `notes` | string | default empty | заметки |
| | `client` | `Client`/null | optional | fiscal/contact data PresuPro, не Registry customer_ref |
| | `invoice_ref` | `InvoiceRef`/null | optional | сохранённая ссылка на Holded document |
| | `locked` | boolean | default false | immutable business fields after conversion |
| | `registry_project` | `RegistryProjectSnapshot`/null | optional | server-resolved immutable snapshot Registry context |
| `RegistryProjectSnapshot` | `project_id` | string containing Registry UUID | required when snapshot exists | связь с Registry |
| | `source` | string default `registry` | default | provenance label |
| | `name`, `address`, `customer_ref`, `registry_updated_at` | string/null | optional | captured Registry context |
| | `snapshot_at` | string | required | capture time |
| `EstimateZone` | `name` | string | required | display name, not stable ID |
| | `area_m2`, `wall_m2` | float/null | optional | zone measures |
| | `items` | list[`EstimateItem`] | default `[]` | mutable ordered positions |
| `EstimateItem` | `type` | string | required | backend totals treats exact `labor` separately; other values fall into materials subtotal |
| | `name` | string/null | optional | display name; no description field |
| | `material_id` | string/null | optional | catalog material reference, not line identity |
| | `qty` | float >= 0 | required | base quantity |
| | `unit` | string | required | unit; backend model has no enum validation |
| | `unit_price` | float/null | optional | explicit unit price or material preferred price fallback |
| | `waste_percent`, `margin_percent`, `discount_percent` | float | default 0.0 | line adjustments |
| | `iva_percent` | float/null | optional | overrides estimate IVA when non-null |
| `EstimateTotals` | `materials_subtotal`, `labor_subtotal`, `margin_total`, `taxable_subtotal`, `iva_total`, `grand_total` | float | required | authoritative backend calculation result |
| | `discount_total` | float | default 0.0 | aggregated discount |
| | `iva_breakdown` | map[string,float] | default `{}` | IVA amount by formatted rate |
| | `currency` | string default `EUR` | default | totals currency |

### PresuPro Holded result

| Model | Поле | Тип | Обязательность | Семантика |
| --- | --- | --- | --- | --- |
| `InvoiceRef` | `provider` | string | required | фактически `holded` |
| | `doc_type` | string | required | `estimate`, `invoice` или `proform` |
| | `external_id` | string | required | Holded response `id` |
| | `number`, `url`, `status`, `synced_at` | string/null | optional | provider metadata; не durable publication receipt |

## 7. Missing contracts

- Registry: closed/deleted statuses, delete semantics, historical project revisions, project revision/version/content hash, user/company/customer/status list filters beyond `include_archived`.
- PresuPro: stable zone ID, stable estimate-item ID, item description, immutable estimate revision, estimate content hash, explicit current/working/approved/published selector, project-scoped estimate endpoint, single-current-estimate rule, behavior for selecting among multiple estimates.
- PresuPro→Client Portal: publisher/adapter from current `Estimate` to `SnapshotPublication`; compatible estimate UUID/version and stable section IDs.
- Holded: standalone Gateway service, idempotency key, durable command/receipt, bounded document-call timeout, unknown-outcome status, retry policy, reconciliation query, outbox/attempt log, correction/update and republish contract.
- Cabinet: implemented Registry client, PresuPro client, Holded client, integration adapter placement, shared launcher/config and local sync persistence.

## 8. Contradictions

Finding: Registry frontend Vite proxy targets port `8000`, while Registry README run command and explicit frontend base URL use port `8010`.
Status: confirmed
Repository: Code Factory / `registry_sandbox`
Path: `projects/registry_sandbox/frontend/vite.config.ts`; `projects/registry_sandbox/README.md`
Symbol: Vite proxy / run configuration
Evidence: `vite.config.ts:7-12` versus `README.md:7-25`.
Implication for Cabinet Backend: Registry address нельзя выводить из одного «стандартного порта»; требуется явно заданный URL.

Finding: Client Portal `list_active_projects()` запрашивает `GET /projects` и парсит элементы как `ProjectReference`, но реальный Registry `GET /projects` возвращает `ProjectSummary` (`id`, `name`, `address`, `status`, `updated_at`).
Status: confirmed
Repository: Code Factory / `client_portal_sandbox`, `registry_sandbox`
Path: `projects/client_portal_sandbox/adapters/registry_gateway.py`; `projects/registry_sandbox/api/runtime.py`; `projects/registry_sandbox/core/models.py`
Symbol: `list_active_projects`, Registry `list_projects`
Evidence: Portal URL/parser `registry_gateway.py:87-118`; Registry response model `runtime.py:58-60`; incompatible model fields `registry core/models.py:76-81,111-114`. Registry имеет совместимый отдельный `/projects/active` (`runtime.py:62-64`), но Portal его не вызывает.
Implication for Cabinet Backend: Client Portal gateway нельзя копировать как заведомо совместимый list client без исправления; это реальная contract mismatch.

Finding: PresuPro accepted spec и frontend перечисляют пять estimate statuses, но backend Pydantic/service принимает любое строковое значение.
Status: confirmed
Repository: Code Factory / `PresuPro_sandbox`
Path: `projects/PresuPro_sandbox/specs/base/global_spec.json`; `projects/PresuPro_sandbox/frontend/engine.js`; `projects/PresuPro_sandbox/core/models.py`; `projects/PresuPro_sandbox/backend/services/estimates.py`
Symbol: `rules.estimate_statuses`, `ESTIMATE_STATUSES`, `Estimate.status`, `update_estimate`
Evidence: spec `global_spec.json:842-848`; frontend `engine.js:7-19`; unrestricted backend `core/models.py:82,134-142`; update projection `services/estimates.py:94-116`.
Implication for Cabinet Backend: frontend/spec enum полезен как intent, но не является enforced runtime contract.

Finding: PresuPro config/spec содержит 30-second Holded request timeout, но Holded `urlopen` calls не передают timeout.
Status: confirmed
Repository: Code Factory / `PresuPro_sandbox`
Path: `projects/PresuPro_sandbox/backend/core/config.py`; `projects/PresuPro_sandbox/specs/base/global_spec.json`; `projects/PresuPro_sandbox/backend/adapters/holded.py`
Symbol: `Settings.request_timeout_seconds`, Holded provider calls
Evidence: default `backend/core/config.py:10-35`; spec `global_spec.json:590-594`; calls `holded.py:52-56,142-146,177-181`.
Implication for Cabinet Backend: нельзя считать Holded timeout policy реализованной.

Finding: PresuPro frontend client при create отбрасывает `project_id`, хотя backend request официально его принимает для server-side Registry linkage.
Status: confirmed
Repository: Code Factory / `PresuPro_sandbox`
Path: `projects/PresuPro_sandbox/frontend/api.js`; `projects/PresuPro_sandbox/core/models.py`; `projects/PresuPro_sandbox/backend/api/routes.py`
Symbol: `estimateCreatePayload`, `CreateEstimateRequest`, `create_estimate_endpoint`
Evidence: frontend allowlist не включает project_id (`frontend/api.js:78-80`); backend field `core/models.py:122-132`; backend use `routes.py:79-83`.
Implication for Cabinet Backend: browser create flow не доказывает отсутствие backend linkage; одновременно он не является готовым UI-путём создания связанной сметы.

Finding: Client Portal snapshot contract требует `estimate_id: UUID`, integer `estimate_version` и stable section identity, чего нет в текущем PresuPro Estimate/Zone.
Status: confirmed
Repository: Code Factory / `client_portal_sandbox`, `PresuPro_sandbox`
Path: `projects/client_portal_sandbox/core/models.py`; `projects/PresuPro_sandbox/core/models.py`
Symbol: `SnapshotPublication`, `SnapshotSectionData`, `Estimate`, `EstimateZone`
Evidence: Portal `core/models.py:669-689`; PresuPro `core/models.py:70-90`.
Implication for Cabinet Backend: модели нельзя смешивать или считать уже соединёнными без отсутствующего producer contract.

## 9. Questions for Cabinet State 1

1. Допускает ли State 1 работу только с явно выбранным `estimate_id`, поскольку project-scoped lookup и правило выбора текущей сметы отсутствуют?
2. Должна ли ссылка Cabinet на строку PresuPro считаться временной/проверяемой при каждом чтении, поскольку zone/item IDs и estimate revision/hash отсутствуют?
3. Как State 1 должен трактовать архивный Registry-проект: исключать из выбора через `/projects/active`, разрешать read-only по `/context`, или это решение пока вне scope?
4. Нужен ли State 1 только read-only доступ к PresuPro, или предполагается вызов существующего `/convert`; второй вариант наследует неподтверждённые timeout/idempotency/reconciliation свойства.
5. Является ли Client Portal snapshot import вообще участником State 1? Если да, требуется отдельное решение владельца контракта, потому что текущий PresuPro не может сформировать требуемую identity/version/sections модель.
6. Какой runtime URL Registry считается эксплуатационным для State 1 (`8010`, proxy `8000` или явно заданное значение), учитывая найденное расхождение?
7. Должен ли Cabinet хранить только opaque `customer_ref`, не пытаясь трактовать его как PresuPro `Client`? Код подтверждает, что это разные данные.
8. Считается ли встроенная PresuPro Holded-интеграция достаточной внешней границей для State 1, или Holded вообще исключён до появления отдельного Gateway-контракта?

## 10. Evidence index

| ID | Repository / path | Lines / symbol | Использовано для |
| --- | --- | --- | --- |
| R1 | `projects/registry_sandbox/core/models.py` | 8-9, 37-86, 111-130 | Registry DTO, обязательность полей, UUID, context/validation |
| R2 | `projects/registry_sandbox/domain/registry/rules.py` | 17-35 | project status allowlist |
| R3 | `projects/registry_sandbox/infra/registry/project_store.py` | 31-50, 53-101 | not found, archive, list filter/order, update |
| R4 | `projects/registry_sandbox/infra/registry/sqlite_repository.py` | 12-51, 98-106, 120-133, 241-287 | SQLite schema, current-state upsert, UUID serialization |
| R5 | `projects/registry_sandbox/services/registry/project_service.py` | 31-89, 97-108, 142-190 | context, active/list projections, validation behavior |
| R6 | `projects/registry_sandbox/api/runtime.py` | 20-48, 50-104 | actual HTTP endpoints, 404/422, no auth |
| R7 | `projects/registry_sandbox/tests/test_project_identity_boundaries.py` | 24-155 | active/archived/missing verified behavior |
| R8 | `projects/registry_sandbox/frontend/src/api/http.ts` | 9-34 | frontend HTTP/error normalization |
| R9 | `projects/registry_sandbox/frontend/vite.config.ts` | 4-14 | Registry dev proxy port |
| R10 | `projects/registry_sandbox/README.md` | 7-25 | Registry documented ports (used only for run-config contradiction) |
| P1 | `projects/PresuPro_sandbox/core/models.py` | 8-14, 56-102, 122-142, 163-201 | Estimate/zone/item/totals/client/invoice/snapshot models |
| P2 | `projects/PresuPro_sandbox/backend/core/config.py` | 10-43 | settings, DB config, estimate ID generator |
| P3 | `projects/PresuPro_sandbox/backend/services/estimates.py` | 17-130, 150-203 | totals, create/update semantics, whole-zone replacement |
| P4 | `projects/PresuPro_sandbox/backend/storage/estimates.py` | 9-55, 58-176 | get/list/upsert/delete, lock, JSON persistence |
| P5 | `projects/PresuPro_sandbox/backend/storage/schema.py` | 50-68, 248-264 | estimate SQLite schema/no project constraint/version |
| P6 | `projects/PresuPro_sandbox/backend/storage/mappers.py` | 23-114 | exact persisted/read zone/item/snapshot fields |
| P7 | `projects/PresuPro_sandbox/backend/api/routes.py` | 69-131, 198-248 | HTTP surface, Registry error mapping, no project list filter/auth |
| P8 | `projects/PresuPro_sandbox/backend/adapters/registry.py` | 10-101 | Registry URL, HTTP validation/context, 5 s timeout, snapshot |
| P9 | `projects/PresuPro_sandbox/tests/test_registry_project_integration.py` | 29-184 | standalone/linked/rejected/error mapping verified behavior |
| P10 | `projects/PresuPro_sandbox/frontend/engine.js` | 7-19, 226-237 | frontend statuses and draft shape |
| P11 | `projects/PresuPro_sandbox/frontend/api.js` | 10-58, 78-84, 110-135 | HTTP client, no auth, create project_id omission, endpoints |
| P12 | `projects/PresuPro_sandbox/mcp/presupro_mcp_server.py` | 1-53, 248-327 | existing HTTP MCP client and estimate tool limits |
| H1 | `projects/PresuPro_sandbox/backend/adapters/holded.py` | 10-84, 87-201 | credentials, provider calls, payload, InvoiceRef, no timeout/idempotency |
| H2 | `projects/PresuPro_sandbox/backend/services/invoicing.py` | 8-10, 33-123 | preview, accepted gate, local short-circuit, publish/persist order |
| H3 | `projects/PresuPro_sandbox/tests/test_invoicing_holded.py` | 12-129 | mocked successful Holded conversion and lock behavior |
| H4 | `projects/PresuPro_sandbox/specs/base/global_spec.json` | 217-218, 347-350, 590-594, 842-860 | documented intent used only to detect runtime contradictions |
| C1 | `projects/client_portal_sandbox/adapters/registry_gateway.py` | 14-32, 51-151 | second Registry HTTP adapter and list mismatch |
| C2 | `projects/client_portal_sandbox/core/models.py` | 134-157, 537-550, 647-723 | Registry failures, service auth context, snapshot contract |
| C3 | `projects/client_portal_sandbox/application/snapshot_import.py` | 16-118, 121-260 | fingerprint, version validation, replay outcomes |
| C4 | `projects/client_portal_sandbox/adapters/snapshot_import_repository.py` | 13-54, 63-170, 174-271 | durable snapshot/import records and unique identity |
| C5 | `projects/client_portal_sandbox/api/router.py` | 128-140, 307-317 | authenticated snapshot HTTP endpoints |
| L1 | `projects/start-full-saas.sh` | 48-109 | existing launcher service set/ports |
| L2 | `projects/status-full-saas.sh` | 36-57 | existing status checks |
| V1 | targeted pytest runs | Registry `2 passed`; PresuPro `10 passed` | runtime verification of scoped findings |
| D1 | read-only SQLite inspection | Registry 1 active project; PresuPro 2 accepted estimates, 1 Registry-linked | confirmation that local datasets exist |

### Search coverage for `not_found`

- Factory projects enumerated: `PresuPro_sandbox`, `client_portal_sandbox`, `hydraulic_diagram_service`, `panelforge`, `panelforge_sandbox`, `photo2pdf_sandbox`, `planspec`, `planspec_sandbox`, `receipts_sandbox`, `registry_sandbox`.
- Deep code inspection scoped to `registry_sandbox`, `PresuPro_sandbox`, `client_portal_sandbox`, and Cabinet runtime/docs.
- Holded search: `backend/adapters/holded.py`, `backend/services/invoicing.py`, `backend/api/routes.py`, `core/models.py`, tests and scoped repo-wide symbol search for `holded`, `idempot*`, `retry`, `reconcil*`, `timeout`.
- Launch/discovery search: workspace files matching `*compose*`, `*launch*`, `*supervisor*`, `*.service`, `*.sh`, plus URL/port environment references.
- Cabinet integration search: `projects/Cabinet_web/tools`, `web`, schemas and integration docs; no Registry/PresuPro/Holded runtime client found.
