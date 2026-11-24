# Возможности фикстуры `semantic_runtime`: снаружи или шов

Источник списка — `tests/semantic/RUNTIME_SURFACE.md`, раздел «Capabilities»
(итоговая редакция 2026-11-24). Подвозможности разной природы разобраны отдельно.
Вызовы раздела «Calls» (`service`, `owner`, `owner_upload`, `owner_http`, `sign_in`, …)
идут через настоящие слушатели и здесь не разбираются: они снаружи по построению.

Критерии те же, что у cabinet-kernel (`agent/cabinet-kernel`,
`examples/cabinet-kernel/tests/semantic/review/CAPABILITIES.md`).

- **«снаружи»** — строится без точки входа в сгенерированный код. Сюда относятся
  переменные окружения и файлы до старта, запуск и остановка экземпляра, чтение stderr,
  каталог резервных копий, файл хранилища через отдельное read-only соединение SQLite,
  байты файла импорта и сборка релиза из закрытий.
- **«шов»** — нужна точка входа внутри работающего кода: подмена часов, отказ
  конкретного вызова хранилища, остановка внутри прогона копии, удержание проходов
  `instance_lifecycle`.
- **Опора в State 5/6** — спецификация *называет точку подмены*: модуль, функцию или
  порт, к которому фикстура может подключиться. Правило, которое лишь *требует свойство*
  («every change … committed together, or none is»), опорой не считается. Оно говорит,
  что проверять, но не где войти. `02_rules_*.md` (State 2), `30_modules.md` (State 3) и
  `80_notes.md` (State 7) приводятся только как контекст.

Общее замечание. В отличие от ядра, State 5/6 Registry не говорят, отдельный ли процесс
экземпляр для теста. `instance_lifecycle.start_instance` вызывает `boundary:host_process`
(`50_public_apis_5_surfaces.md:319`), и поверхность связывает фикстуру с ним. Если
экземпляр поднимается в процессе pytest, швы с опорой ставятся прямо в названные точки.
Если отдельным процессом, нужен канал доставки, а его State 5/6 не называют. Это дело
обёртки запуска Factory, не пробел в точке входа.

## Классификация

| возможность | что делает | класс | как строится | опора в State 5/6 (file:line) или «нет опоры» |
|---|---|---|---|---|
| `configure(**settings)`, `configure(item=None)` | значения `RuntimeSettings` для следующего старта | снаружи | переменные `REGISTRY_*` окружения старта. `None` — переменной нет | не требуется. Отображение переменных на поля: `60_contracts.md:355`, `60_data_closure.json` (`config.runtime_environment_variables`) |
| `start()` → `None` или диагностика, `stop()`, `restart()` | запуск по порядку A17, остановка, перезапуск | снаружи | запуск и остановка хоста. Диагностика — последняя строка stderr | не требуется. Порядок шагов: `50_public_apis_5_surfaces.md:310–343` (`start_instance`). **Неточность поверхности:** в колонке «reaches» стоит `configuration.load_runtime_settings`. Такой операции нет: есть `runtime_settings.load_runtime_settings` (`50_public_apis_1_foundation.md:461`), её вызывает `configuration.load_configuration` (`50_public_apis_1_foundation.md:501`, `50_public_apis_0_conventions.md:168`) |
| `configure_environment(variables)` | следующий старт видит ровно эти переменные | снаружи | окружение процесса | не требуется (`60_data_closure.json`, `config.runtime_environment_variables`) |
| `configure_release(**constants)` | следующий старт на тестовом релизе с другими значениями названных констант | снаружи (сборка) | Factory собирает релиз, где модуль `data_provider` сгенерирован из закрытия с заменёнными значениями. Работающий код других модулей не трогается | **косвенная.** Модуль и способ потребления названы: «`module:data_provider` has no operation: it exports constants» (`50_public_apis_0_conventions.md:138`), «a consumer imports by name» (`70_data_provider_closure.json:24`). Сборку релиза с другими значениями для теста State 5/6 не называют. Основание — решение владельца 2026-11-24 (`RUNTIME_SURFACE.md`, вступление) |
| `diagnostics()` | строки stderr экземпляра | снаружи | перехват stderr | не требуется. Форма: «one line on the process's standard error» (`50_public_apis_0_conventions.md:116–118`) |
| `clock.set`, `clock.advance` | двигают оба часа вместе | **шов** | подмена модуля `clock` целиком: `recorded_now` и `monotonic_reading` из источников фикстуры | **есть.** «Tests replace the clock as a whole» (`50_public_apis_1_foundation.md:49`). Сказано в разделе `recorded_now`, а владелец обеих операций — `module:clock` (`:59`) |
| `clock.suspend(seconds)` | приостановка хоста: двигает оба часа | **шов** | та же подмена; по действию равна `advance` | **есть** (`50_public_apis_1_foundation.md:49`). Что монотонные часы считают приостановку: `:63–64` |
| `clock.shift_wall(...)` | двигает только записанные часы | **шов** | та же подмена, два источника независимы | **есть** (`:49`). «which a change of the wall clock does not move» (`:63`) |
| `run_session_pass()` → int | один вызов `end_expired_sessions` | **шов** | прямой вызов операции. Кроме того, собственный проход `instance_lifecycle` должен быть удержан | **частичная.** Операция и её выход названы: `50_public_apis_2_sessions.md:433`, «How many sessions it ended» (`:450`). Точки, где удержать собственный проход, нет: `start_instance` всегда запускает оба прохода (`50_public_apis_5_surfaces.md:335–339`), и они идут по `monotonic_reading` (`50_public_apis_0_conventions.md:119–132`). При подменённых часах проход может сработать сам после `advance`, если его ожидание не завязано на часы фикстуры |
| `run_backup_look()` | один вызов `run_daily_backup_if_due`, ожидание запущенного прогона | **шов** | как выше. Нужен ещё сигнал конца прогона | **частичная.** Операция названа (`50_public_apis_4_import_backups.md:242`), но «answer at once, the run going on apart» (`:246–247`): сигнала конца прогона State 5/6 не дают. Удержание собственного прохода — как у `run_session_pass` |
| `backup_files()`, `backup_bytes(name)` | имена и байты в месте резервных копий | снаружи | чтение каталога | не требуется (префиксы: `70_data_provider_closure.json`, `BACKUP_KEPT_PREFIX`, `BACKUP_TEMPORARY_PREFIX`) |
| `read_backup(name, key=None)` → `{table: rows}` | расшифровка снимка и чтение его таблиц | снаружи | HKDF-SHA256 и AES-256-GCM по формату файла, затем SQLite read-only | не требуется. Формат: «A backup file» (`60_contracts.md:256–262`) |
| `restore(name)` | остановка, расшифрованный снимок на место хранилища, старт | снаружи | файловые операции между `stop()` и `start()` (восстановление владельца вне Registry, R0-89) | не требуется. Старт открывает его как любое хранилище (`store.open_store`, `50_public_apis_1_foundation.md:717`) |
| `store_rows(table)` | строки таблицы | снаружи | отдельное read-only соединение SQLite к файлу хранилища. WAL позволяет читать при работающем экземпляре (`60_contracts.md:330–336`) | не требуется. Таблицы: `70_persistence_closure.json` |
| `export_file(...)` | байты файла импорта | снаружи | сериализация JSON по формату | не требуется. Формат: «The import file» (`60_contracts.md:244`) |
| `new_request_id()` | свежий печатный id | снаружи | генератор в фикстуре | не требуется |
| `faults.fail_store_call(method)` | следующий вызов метода `StoreRepository` поднимает ошибку драйвера | **шов** | обёртка над `SqliteStoreRepository`, которую `store` создаёт на каждое соединение (`60_contracts.md:306–312`). Обёртка один раз поднимает ошибку на названном методе | **есть.** `StoreRepository` — порт с обязательством реализации `local` [`SqliteStoreRepository`] (`60_contracts.md:52–53`). Методы: «exactly the 37 methods of `70_persistence_closure.json`» (`60_contracts.md:301–304`). Например, `insert_pointer_row` (`70_persistence_closure.json:729`), `update_pointer_row` (`:791`), `insert_audit_entry_row` (`:972`), `insert_migration_closure_row` (`:1047`). Поведение при сбое: «an error of the driver — is raised unchanged to `store` … which rolls the transaction back and answers `internal_error` (`transaction_failed`)» (`60_contracts.md:314–320`) |
| `faults.fail_next_commit()` | транзакция падает после возврата шага и до коммита | **шов** | подмена коммита внутри `store.run_in_transaction` | **нет опоры.** Есть только свойство: «The step's answer once committed, or `internal_error`» и «committed together, or none is» (`50_public_apis_1_foundation.md:868`, `:873`). Коммит — не метод порта (37 методов: insert, load, find, update, list, delete; `60_contracts.md:303–304`), а точки между шагом и коммитом State 5/6 не называют |
| `faults.fail_next_backup_check("integrity")` | копия не проходит `check_store_file`, хотя расшифровывается | **шов** | подмена ответа `store.check_store_file` или порча расшифрованной копии до проверки | **нет опоры.** Операция названа (`50_public_apis_1_foundation.md:971`), но не как точка подмены. Проверка — `PRAGMA integrity_check` на read-only соединении (`:996`), а не метод порта |
| `faults.fail_next_backup_check("sequence_mismatch")` | счётчик M12 копии отличается от записанного | **шов** | обёртка порта на read-only соединении проверки: `load_audit_sequence_row` отдаёт другое число | **есть.** «`check_store_file` reads the copy's `load_audit_sequence_row` on its read-only connection» (`60_contracts.md:345–347`). Метод: `70_persistence_closure.json:1016`. Порт: `60_contracts.md:52–53` |
| `faults.hold_backup_snapshot()` | прогон копии ждёт после первого чтения, которое фиксирует снимок | **шов** | обёртка порта на собственном соединении снимка: после возврата первого `load_audit_sequence_row` ждать `release()` | **есть, косвенно.** «fixes the snapshot by its first read, `load_audit_sequence_row`» (`60_contracts.md:339–341`), «its first read, of the audit counter, fixes the snapshot» (`50_public_apis_1_foundation.md:956–957`). Отличить репозиторий соединения снимка от репозитория действий фикстура может только по порядку создания (`60_contracts.md:306–310`): отдельного имени у него нет |

## Швы с опорой в спеке

- **`clock.*`** (`50_public_apis_1_foundation.md:49`). Модуль `clock` заменяется целиком.
  Оба источника — его, поэтому `shift_wall` (только записанные) и `suspend` (оба) строятся
  на одной подмене.
- **`faults.fail_store_call`** — порт `StoreRepository` и его 37 названных методов
  (`60_contracts.md:52–53`, `:301–304`). Путь сбоя назван там же (`:314–320`).
- **`faults.fail_next_backup_check("sequence_mismatch")`** и
  **`faults.hold_backup_snapshot`** — тот же порт, методы `load_audit_sequence_row` на
  названных соединениях проверки и снимка (`60_contracts.md:339–347`). У удержания опора
  косвенная: соединение снимка не имеет собственного имени, его различает только порядок
  создания репозиториев.

## Швы с частичной опорой

- **`run_session_pass`, `run_backup_look`.** Вызываемые операции названы. Но
  `start_instance` всегда запускает собственные проходы (`50_public_apis_5_surfaces.md:335–339`),
  и точки их удержания нет. У `run_backup_look` нет и сигнала конца прогона
  (`50_public_apis_4_import_backups.md:246–247`). Фикстура держит проходы своими средствами:
  например, ожидание прохода завязано на подменённые часы и не срабатывает без вызова.
  Так она обещает «never lets the passes … run on their own», но спецификация этого
  не называет.

## Швы без опоры в спеке

- **`faults.fail_next_commit`.** Есть только свойство атомарности
  (`50_public_apis_1_foundation.md:868`, `:873`). Точки между шагом и коммитом нет.
- **`faults.fail_next_backup_check("integrity")`.** Операция `check_store_file` названа,
  но не как заменяемая. Целостность проверяет `PRAGMA` на соединении, а не метод порта.

Искал в `50_public_apis_0..5_*.md`, `60_contracts.md`, `60_contracts.json`,
`60_contract_plan.json`, `60_model_closure_*.json`, `60_data_closure.json`,
`70_persistence_closure.json`, `70_data_provider_closure.json`. Шаблоны: `replace`,
`Tests replace`, `substitut`, `inject`, `fault`, `seam`, `hook`, `StoreRepository`,
`run_in_transaction`, `commit`, `copy_store_snapshot`, `check_store_file`,
`load_audit_sequence_row`, `Passes`, `data_provider`. Кроме модуля `clock` и порта
`StoreRepository`, точек подмены State 5/6 не называют.

## Свидетели, зависящие от шва без опоры или с частичной опорой

| witness | тест | шов |
|---|---|---|
| `registry_a14_failed_store_leaves_no_change_no_entry` | `test_a14_audit_entries.py::test_failed_store_leaves_no_change_no_entry` | `faults.fail_next_commit` (первая половина; вторая — `fail_store_call`, с опорой) |
| `registry_a14_accepted_change_writes_one_entry_in_transaction` | `test_a14_audit_entries.py::test_accepted_change_writes_one_entry_in_transaction` | `faults.fail_next_commit` (первая половина; вторая — `fail_store_call`) |
| `registry_a15_failed_change_leaves_sequence_unchanged` | `test_a15_audit_log.py::test_failed_change_leaves_sequence_unchanged` | `faults.fail_next_commit` |
| `registry_a18_failed_backup_still_deletes_old_backups` | `test_a18_backups.py::test_failed_backup_still_deletes_old_backups` | `faults.fail_next_backup_check("integrity")`; `run_backup_look` (частичная) |
| `registry_a18_integrity_failure_deleted_and_reported` | `test_a18_backups.py::test_integrity_failure_deleted_and_reported` | `faults.fail_next_backup_check("integrity")`; `run_backup_look` (частичная) |
| `registry_a18_backup_during_write_is_one_snapshot` | `test_a18_backups.py::test_backup_during_write_is_one_snapshot` | `run_backup_look` (частичная) |
| `registry_a18_retention_cutoff_exact_to_microsecond` | `test_a18_backups.py::test_retention_cutoff_exact_to_microsecond` | `run_backup_look` (частичная) |
| `registry_a18_record_matches_snapshot_mismatch_deleted` | `test_a18_backups.py::test_record_matches_snapshot_mismatch_deleted` | `run_backup_look` (частичная) |
| `registry_a18_backup_unreadable_without_its_key` | `test_a18_backups.py::test_backup_unreadable_without_its_key` | `run_backup_look` (частичная) |
| `registry_a18_restored_store_holds_no_agent_session` | `test_a18_backups.py::test_restored_store_holds_no_agent_session` | `run_backup_look` (частичная) |
| `registry_a13_monotonic_clock_decides_validity` | `test_a13_owner_session.py::test_monotonic_clock_decides_validity` | `run_session_pass` (частичная) |

Итого без опоры: 5 свидетелей. Три держатся на `fail_next_commit`, у двух из них вторая
половина опирается на `fail_store_call`; ещё два — на `fail_next_backup_check("integrity")`.
С частичной опорой (только удержание проходов): ещё 6 свидетелей. Непомеченный
`test_a18_backups.py::test_missed_backup_while_stopped_not_made_up` тоже зависит от
`run_backup_look`.

Варианты для `fail_next_commit` (решение за владельцем):

- оставить шов без опоры;
- заменить его на `fail_store_call` последнего метода, который действие пишет в своей
  транзакции (запись аудита или `upsert_audit_sequence_row`), — опора на порт;
- в State 5 назвать точку «перед коммитом» у `store.run_in_transaction`.

`configure_release` (6 свидетелей A01, A09, A22) — не шов, а сборка. Её опора косвенная:
модуль `data_provider` назван, тестовый релиз — нет.

Сопоставление тестов и возможностей сверено скриптом по AST итоговых тестов, с
транзитивным обходом помощников внутри файла.


## После раунда State 2 от 2026-11-24

`faults.fail_next_commit()` удалён из `RUNTIME_SURFACE.md`: три свидетеля, которые на нём держались (A14 `failed_store_leaves_no_change_no_entry`, `accepted_change_writes_one_entry_in_transaction`, A15 `failed_change_leaves_sequence_unchanged`), теперь используют `faults.fail_store_call` с методами `StoreRepository`, названными в State 6 (`insert_audit_entry_row`, `update_project_row`, `update_customer_row`). Строки и выводы выше о `fail_next_commit` — история; шов без опоры остаётся один: `fail_next_backup_check("integrity")` (2 свидетеля A18), плюс частичная опора у удержания проходов.
