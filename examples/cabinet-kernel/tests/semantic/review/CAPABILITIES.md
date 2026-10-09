# Возможности фикстуры `semantic_runtime`: снаружи или шов

Источник списка — `tests/semantic/RUNTIME_SURFACE.md`, раздел «Named capabilities»
(строки 94–120). Подметоды и действия разобраны отдельно там, где они разной природы.

Критерии.

- **«снаружи»** — строится без изменения ядра: файлы установки и конфигурации, файлы
  манифеста, HTTP-заглушка на loopback, остановка и запуск процесса (сигналы), чтение
  каталога данных, наблюдение за процессами ОС (`/proc`, пространства имён, монтирования,
  события создания процессов), перехват stderr, argv, размещение файлов в файловой системе
  между запросами или до старта, статическое чтение сгенерированных исходников и релиза.
- **«шов»** — нужна точка входа внутри сгенерированного кода: подмена часов, отказ
  конкретного изменения хранилища, момент внутри записи значения, наблюдение за каждым
  сравнением токена и т. п.
- **Опора в State 5/6** — спецификация *называет точку подмены* (модуль, функцию, параметр),
  к которой фикстура может подключиться. Правило, которое лишь *требует свойство*
  («сравнение за постоянное время», «упавший вызов ничего не пишет»), опорой не считается:
  оно говорит, что проверять, но не где фикстуре войти. `80_notes.md` — это State 7
  (заголовок файла: «State 7 — Cabinet Kernel notes»), `30_modules.md` — State 3, а
  `02_rules_*.md` — State 2. Все три приводятся только как контекст.

Общее замечание о процессе. Ядро — отдельный процесс (A18, правило 1:
`02_rules_installation.md:233`). Фикстура его перезапускает (`restart()`), убивает по SIGKILL
(`KernelStopped`) и запускает второй экземпляр (`start_second_kernel()`). Поэтому любой шов
нужно доставить *внутрь процесса ядра* через обёртку запуска. Отсюда следуют два вывода.
Во-первых, шов, у которого есть опора, строится только поверх названной точки подмены.
Во-вторых, ни State 5, ни State 6 не называют канал доставки в процесс: опции старта,
переменной окружения или поля конфигурации нет. А20 к тому же запрещает окружению влиять
на потолки. Обёртка запуска и канал управления (например, файл, который читает подменённая
функция) остаются делом Factory.

## Классификация

| возможность | что делает | класс | как строится / какая точка входа нужна | опора в State 5/6 (цитата file:line) или «нет опоры» |
|---|---|---|---|---|
| `installation.owner_token`, `installation.agent_token(name)` | читают токены из файла конфигурации установки | снаружи | чтение файла конфигурации, который фикстура сама записала | не требуется |
| `installation.set_agent_tokens`, `installation.set_owner_token`, `installation.write_config_text`, `installation.write_secret`, `installation.set_manifest_revision`, `installation.select_instance` | переписывают конфигурацию или файл секрета | снаружи | запись файлов. Токены ядро перечитывает перед каждым запросом (A16, правило 2), остальное действует при `restart()` | не требуется |
| `installation.set_config_mode(mode)` | права на файл конфигурации | снаружи | `chmod` и `restart()` | не требуется |
| `installation.set_credential(service_id, header_name, secret_value)` | файл секрета только для владельца и ссылка на него (`None` — ссылка на отсутствующий файл) | снаружи | запись файла секрета и ссылки в конфигурации | не требуется |
| `clock.set(epoch_us)`, `clock.advance(ms, days)` | задают показание `clock.kernel_now` | **шов** | подмена источника настенного времени модуля `clock` внутри процесса ядра. Нужна до старта ядра и между запросами | **есть, на уровне модуля.** `50_public_apis.md:575`: «The only reader of the wall clock; replaceable as a whole in tests (A19).» Сигнатура без параметра часов: `60_contracts.json:8` `"kernel_now": "() -> KernelInstant"`. Контекст: `30_modules.md:400` «The wall and monotonic clocks, and their replacement by a fixed clock in tests.» (State 3); `80_notes.md:26` «keeps each clock behind one private module-level reader function so that a test can replace the whole module's time source with a fixed clock» (State 7) |
| `clock.fix_monotonic(ns)` | фиксирует монотонный источник модуля `clock` | **шов** | подмена источника монотонного времени того же модуля | **есть, косвенно.** В разделе `public_op:clock.monotonic_deadline` (`50_public_apis.md:585–618`) слов о подмене нет. Её покрывает только «replaceable as a whole» в разделе `kernel_now` (`50_public_apis.md:575`): «as a whole» относится к модулю, у которого два источника, см. `60_contracts.json:9` `"monotonic_deadline": "(duration_ms: int) -> MonotonicDeadline"`. Явно оба источника названы только в State 3 (`30_modules.md:400`, `30_modules.md:412`) и State 7 (`80_notes.md:26`). Правило: `02_rules_installation.md:330` «With the clock module's monotonic source fixed to a sentinel value» |
| `mcp_request(operation, request, *, token, raw)` | один запрос через вход MCP | снаружи | клиент MCP, который передаёт сырые байты | не требуется |
| `restart()` | остановка и повторный старт на том же каталоге | снаружи | сигнал и запуск процесса, перехват stderr и кода выхода | не требуется |
| `kernel_exited()` | статус выхода, если ядро завершилось само | снаружи | `waitpid` дочернего процесса | не требуется |
| `KernelStopped` | исключение вызова, под которым фикстура убила ядро | снаружи | обрыв соединения клиента после SIGKILL | не требуется |
| `start_second_kernel()` | второй процесс на том же каталоге | снаружи | запуск процесса | не требуется |
| `host.remove_bubblewrap()` | на хосте нет bubblewrap при следующем старте | снаружи | `PATH` без `bwrap` или скрытие бинарника в mount namespace запуска | не требуется |
| `host.set_env(name, value)` | переменная окружения при следующем старте | снаружи | окружение процесса | не требуется |
| `sandbox_executions()` | для каждого запуска песочницы: сетевые интерфейсы, монтирования, каталог обмена, процессы, оставшиеся после завершения | снаружи | `/proc/<pid>/ns`, `mountinfo`, argv `bwrap` (`--bind` каталога обмена), дерево процессов. Пробный запуск при старте (`50_public_apis.md:1186`) тоже попадёт в список, но тестам это не мешает: они считают от базовой линии | не требуется |
| `sandbox_runtime_paths()` | пути хоста, которые релиз монтирует как среду песочницы | снаружи | статическое чтение релиза или argv `bwrap` | не требуется |
| `faults.unconfirmed_cleanup(nth=1)` | n-й запуск песочницы, считая с этого момента, не может подтвердить очистку | снаружи (решение, см. ниже) | **За «снаружи».** Очистка — это сбор процессов и удаление каталога обмена (`02_rules_functions.md:221`, A03 правило 7). Каталог обмена виден в argv `bwrap`. Фикстура-наблюдатель ловит n-й `execve` `bwrap` (тот же наблюдатель, что для `process_arguments()`) и, пока каталог существует, мешает его удалить средствами хоста: монтирует tmpfs внутри каталога (`EBUSY`) или ставит `chattr +i`. Ядро при этом не меняется. **За «шов».** Нужны привилегии хоста (root, CAP_LINUX_IMMUTABLE или право монтировать) и стоп по событию exec (ptrace или proc connector). Без них остаётся только подмена внутри `sandbox`. **Решение: снаружи.** Причина: момент — это создание процесса, факт ОС; препятствие — состояние файловой системы; входить в код не нужно | не требуется. Если владелец не принимает привилегированный наблюдатель, это шов без опоры: State 5 описывает только свойство, `50_public_apis.md:1174` «None: an unconfirmed cleanup is the result `crashed` with detail `cleanup_failed`» |
| `faults.fail_store_change(change_name)` | следующее изменение с этим именем терпит отказ | **шов** | отказ внутри транзакции конкретного именованного изменения `store.record_change`. Снаружи мишень не выбрать. Право только на чтение или нехватка места бьют по любому изменению и не действуют на уже открытый дескриптор. Триггер SQLite, записанный в базу между запросами, зависит от сгенерированной схемы таблиц, а её State 6 не фиксирует | **нет опоры.** Искал: `fault`, `inject`, `hook`, `failed transaction` в `50_public_apis.md`, `60_*.json`, `60_contracts.md`. Есть только свойство: `50_public_apis.md:863` «`internal_error` for any other broken invariant of its own, or a failed transaction — nothing written either way.» Сигнатура без точки подмены: `60_contracts.json:15` `"record_change": "(change: StoreChange, actor: Actor) -> RecordSet"` |
| `faults.crash_during_value_write()` | ядро падает посреди записи значения | **шов** (решение) | **За «снаружи».** inotify на создание временного файла в области значений, затем SIGKILL. Это гонка: запись может успеть закончиться, и тест пройдёт без проверки. Детерминированно — только ptrace или seccomp-стоп на системном вызове `rename` или `fsync` временного файла. **Решение: шов.** Нужен момент *внутри* `store.put_value_bytes` (между созданием временного файла и `rename`). Перехват системных вызовов привязывает фикстуру к последовательности ввода-вывода сгенерированного кода, а это уже вход в исполнение, а не наблюдение за процессом | **нет опоры.** Только свойство: `50_public_apis.md:732` «Written to a temporary file, flushed, checked, renamed; a completed file is never overwritten» и `02_rules_installation.md:276` «A crash during a value write leaves either no file or the complete file.» Сигнатура `put_value_bytes` в `60_contracts.json` — `(content: bytes, expected_digest: str, expected_size: int) -> str`, без хука |
| `faults.place_symlink(relative_path, target)` | символическая ссылка в каталоге данных | снаружи | тест (`test_a18_store.py:287`) ставит ссылку *между запросами* по пути `value_file(...)`. Запросы обрабатываются по одному (A18 правило 3), поэтому это размещение в файловой системе, пока ядро простаивает, а не момент внутри записи. Вторая часть проверки — отказ старта после `restart()` | не требуется |
| `faults.alter_value_write(kind, nth=1)` | n-я запись значения изменена после сброса временного файла и до проверки (`content` — один байт, `size` — +1 байт) | **шов** | момент между `flush` и `fsync` и проверкой дайджеста внутри `put_value_bytes`. Снаружи — только стоп на системном вызове с подменой файла (те же доводы, что для `crash_during_value_write`) | **нет опоры.** Только свойство: `50_public_apis.md:732` (выше) и `50_public_apis.md:737` «`refused` when digest or size do not match». Порядок «flush, fsync, re-check» назван только в State 7 (`80_notes.md:56`) и точкой входа не является |
| `manifest.write_record`, `manifest.write_record_text`, `manifest.new_revision` | файлы манифеста платформы | снаружи | запись файлов | не требуется |
| `stub_service()`: `base_url`, `authority`, `on(...)` с ответом, `set_down`, `requests` | HTTP-заглушка на loopback | снаружи | свой HTTP-сервер | не требуется |
| действие `drop_after_request` | закрыть соединение после чтения запроса | снаружи | заглушка | не требуется |
| действие `refuse_connection` | отказ в соединении | снаружи | заглушка (закрытый порт или RST) | не требуется |
| действие `redirect` | ответ 3xx с `Location` | снаружи | заглушка | не требуется |
| действие `kill_kernel` | SIGKILL ядру, когда запрос пришёл, до ответа | снаружи | заглушка знает PID ядра от фикстуры | не требуется |
| действие `hold` | держать ответ | снаружи | заглушка | не требуется (в тестах не используется) |
| `store_dump()` | все байты хранилища | снаружи | чтение каталога данных | не требуется |
| `run_spool(run_id)` | файлы спула прогона | снаружи | чтение каталога данных. Раскладку спула (каталог на прогон) называет A18 правило 2, точное имя каталога — нет; фикстура узнаёт его из сгенерированных исходников | не требуется |
| `kill_on_sandbox_start(nth=1)` | SIGKILL ядру при старте n-го запуска песочницы | снаружи (решение) | **За «снаружи».** Старт запуска — это создание процесса `bwrap` потомком ядра. Его видно по событию fork/exec (proc connector, ptrace или опрос `/proc`), и тот же наблюдатель нужен для `process_arguments()`. Тест проверяет только, что прерванный запуск «concluded nothing» (`test_a14_waiting.py:591`). Любой момент после появления `bwrap` и до записи результата этому удовлетворяет. **За «шов».** Если под «стартом» понимать точку внутри `sandbox.execute_function` до создания процесса, нужен хук. Опрос `/proc` может пропустить короткий запуск, а пробный запуск при старте (`50_public_apis.md:1186`) сбивает счёт, если ядро ещё не запущено. **Решение: снаружи** со стопом по событию exec | не требуется. Как шов — без опоры |
| `surface_answers()` | сырые байты всех ответов входа MCP | снаружи | транспорт клиента фикстуры | не требуется |
| `token_comparisons()` | каждое сравнение предъявленного токена с токеном владельца и токенами агентов и примитив сравнения, либо наблюдатель времени | **шов** (вариант с наблюдателем времени — снаружи, но статистический) | нужно наблюдать каждое сравнение внутри `surface.authenticate_token`. Обёртка над самой функцией видит один вызов на запрос, а не отдельные сравнения. Подмена `hmac.compare_digest` в процессе ядра — это патч стандартной библиотеки, а не шов, названный спецификацией | **нет опоры: спецификация называет свойство, а не точку входа.** `60_contract_plan.json:551` «Compare a presented token in constant time with the current token list and return its actor, or none.» `60_contracts.json:84` `"authenticate_token": "(presented_token: str \| None) -> Actor \| None"` — параметра-компаратора нет. Правила: `02_rules_installation.md:34` «The kernel compares it in constant time», `02_rules_installation.md:128`. Примитив `hmac compare_digest` назван только в State 7 (`80_notes.md:348`) |
| `host_output()` | stderr и журнал ядра | снаружи | перехват stderr, чтение файла журнала | не требуется |
| `process_arguments()` | argv ядра и всех его потомков | снаружи | `/proc/<pid>/cmdline` по событиям fork/exec | не требуется |
| `data_directory` | каталог данных для чтения | снаружи | путь | не требуется |
| `value_file(value_digest)` | относительный путь опубликованных байтов | снаружи | поиск файла по дайджесту в области значений или статическое чтение раскладки из исходников. Точное имя (`sha256/…`, подкаталоги) State 6 не фиксирует | не требуется |
| `kernel_sources()` | исходники сгенерированных модулей | снаружи | статическое чтение | не требуется |
| `release` (`ceilings`, `dependencies`, `sandbox_interpreter`) | что объявляет релиз | снаружи | статическое чтение файлов релиза | не требуется |
| `host_scratch_directory()` | каталог хоста вне каталога данных | снаружи | временный каталог | не требуется |

## Швы с опорой в спеке

- **`clock.set`, `clock.advance`.** State 5 называет точку подмены: модуль `clock` «replaceable
  as a whole in tests» (`50_public_apis.md:575`), а `kernel_now` не принимает время от
  вызывающего (`60_contracts.json:8`). Фикстура подменяет источник модуля и не трогает ни одну
  операцию. Чего не хватает: канала доставки подмены в отдельный процесс ядра (см. «Общее
  замечание»). Это забота обёртки запуска Factory, а не пробел в точке входа.
- **`clock.fix_monotonic`.** Опора есть, но косвенная. «As a whole» в State 5 стоит только в
  разделе `kernel_now`. В разделе `monotonic_deadline` (`50_public_apis.md:585–618`) о подмене
  ничего не сказано. Явно два источника названы лишь в State 3 (`30_modules.md:400`) и State 7
  (`80_notes.md:26`).

Тесты, использующие швы с опорой:

| witness | тест | шов |
|---|---|---|
| `kernel_a01_activation_identity_is_store_position` | `test_a01_identity.py::test_activation_identity_is_store_position` | `clock.set`, `clock.advance` |
| `kernel_a01_equal_contract_not_made_current` | `test_a01_identity.py::test_equal_contract_not_made_current` | `clock.set`, `clock.advance` |
| `kernel_a01_equal_submission_returns_existing` | `test_a01_identity.py::test_equal_submission_returns_existing` | `clock.set`, `clock.advance` |
| `kernel_a10_no_decision_changes_nothing` | `test_a10_approvals.py::test_no_decision_changes_nothing` | `clock.advance` |
| `kernel_a11_unknown_blocks_dependants` | `test_a11_unknown_outcome.py::test_unknown_blocks_dependants` | `clock.advance` |
| `kernel_a12_pins_survive_later_records` | `test_a12_run_start.py::test_pins_survive_later_records` | `clock.advance` |
| `kernel_a13_advance_only_inside_request` | `test_a13_advance.py::test_advance_only_inside_request` | `clock.advance` |
| `kernel_a13_resolved_unknown_conclusion` | `test_a13_advance.py::test_resolved_unknown_conclusion` | `clock.advance` |
| `kernel_a14_elapsed_wait_changes_nothing` | `test_a14_waiting.py::test_elapsed_wait_changes_nothing` | `clock.advance` |
| `kernel_a19_monotonic_reading_never_stored` | `test_a19_time.py::test_monotonic_reading_never_stored` | `clock.fix_monotonic`, `clock.set` |
| `kernel_a19_service_timestamp_not_kernel_time` | `test_a19_time.py::test_service_timestamp_not_kernel_time` | `clock.set` |
| `kernel_a19_timestamps_from_injected_clock` | `test_a19_time.py::test_timestamps_from_injected_clock` | `clock.set` (через помощник `_authored_sequence`) |

## Швы без опоры в спеке

- **`faults.fail_store_change`.** State 5 называет только свойство («a failed transaction —
  nothing written either way», `50_public_apis.md:863`). Точки, где фикстура могла бы сорвать
  именованное изменение, нет.
- **`faults.crash_during_value_write`.** Только свойство (`50_public_apis.md:732`,
  `02_rules_installation.md:276`). Момент «во время записи» лежит внутри `put_value_bytes`.
- **`faults.alter_value_write`.** Только свойство (`50_public_apis.md:732`, `:737`). Момент
  «после flush, до проверки» лежит внутри `put_value_bytes`.
- **`token_comparisons()`.** Только свойство (`60_contract_plan.json:551`,
  `02_rules_installation.md:34`). Примитив назван лишь в State 7 (`80_notes.md:348`). Сам
  `RUNTIME_SURFACE.md:112` пишет «not yet specified».

Искал в `50_public_apis.md`, `60_contracts.json`, `60_contracts.md`, `60_contract_plan.json`,
`60_model_closure_*.json`, `60_data_closure.json`, `60_exception_taxonomy.json`, а для
контекста — в `02_rules_*.md` и `80_notes.md`. Шаблоны: `clock`, `kernel_now`, `monoton`,
`inject`, `fault`, `hook`, `seam`, `replace`, `substitut`, `compare_digest`, `constant[- ]time`,
`crash`, `flush`, `temporary`, `symlink`, `failed transaction`. Точек отказа и хуков, кроме
подмены модуля `clock`, State 5/6 не называет.

Условно (если владелец не примет решение «снаружи», принятое выше):
`faults.unconfirmed_cleanup` (`kernel_a03_unconfirmed_cleanup_stops_kernel`) и
`kill_on_sandbox_start` (`kernel_a14_restart_in_flight_becomes_unknown`) тоже станут швами
без опоры.

## Свидетели, зависящие хотя бы от одного шва без опоры в спеке

| witness | тест | шов(ы) без опоры |
|---|---|---|
| `kernel_a16_token_match_unique_constant_time` | `test_a16_surface_access.py::test_token_match_unique_constant_time` | `token_comparisons()`. Тест не вызывает его, а делает `pytest.skip` после наблюдаемой части (`test_a16_surface_access.py:603`): часть свидетеля про постоянное время не проверяется |
| `kernel_a18_failed_store_call_writes_nothing` | `test_a18_store.py::test_failed_store_call_writes_nothing` | `faults.fail_store_change` |
| `kernel_a18_published_file_digest_never_overwritten` | `test_a18_store.py::test_published_file_digest_never_overwritten` | `faults.alter_value_write` |
| `kernel_a18_value_write_atomic_publish` | `test_a18_store.py::test_value_write_atomic_publish` | `faults.crash_during_value_write` |

Итого: 4 свидетеля (3 полностью держатся на шве без опоры, 1 пропускает свою часть,
требующую шва). При иной оценке двух пограничных возможностей — 6.

Ни один помощник (`_case`, `_function`, `_published`, `_service`, …) не использует швов без
опоры. Шов с опорой через помощник один: `_authored_sequence` в `test_a19_time.py`.
Сопоставление сверено скриптом (вызовы и помощники, AST) по итоговым тестам ветки.

## Для решения владельца

Решение за владельцем; варианты нейтрально:

- **(a) Узаконить швы в State 5/6.** Назвать точки входа, по аналогии с `clock`
  («replaceable as a whole in tests»): точку отказа именованного изменения в
  `store.record_change`, точку внутри `store.put_value_bytes` (после сброса временного файла
  и до проверки, и до `rename`), наблюдаемый примитив сравнения в
  `surface.authenticate_token`. При желании — и канал доставки подмены в процесс ядра,
  который сейчас не назван даже для `clock`.
- **(b) Перевести четырёх свидетелей из таблицы выше в `note:`.** Тогда свойства A18 (правила
  3–4) и A16 (постоянное время) остаются требованиями без исполняемого свидетеля.

Варианты можно сочетать по свидетелям. Отдельно владельцу стоит подтвердить или отвергнуть
решение «снаружи» для `faults.unconfirmed_cleanup` и `kill_on_sandbox_start`: оно опирается на
привилегированного наблюдателя процессов на хосте.

Ошибки и несоответствия в `RUNTIME_SURFACE.md` (не исправлены):

1. Строки 91–92: «Each is used only by the witnesses **the next section** lists for it».
   Следующий раздел назван «Places the surface cannot reach yet» (стр. 122), и его вступление
   (стр. 124–127) говорит о тестах, которые *нельзя* выразить и которые «not written around».
   На деле это карта «возможность → свидетели» для уже написанных тестов, которые эти
   возможности используют. Заголовок и вступление противоречат роли раздела.
2. Нарушено обещание «used only by the witnesses … lists»: часть тестов использует
   возможности, которых нет в их строке. Итог после ревью (подробно — SUMMARY.md):
   - исправлено в RUNTIME_SURFACE.md как явная ошибка (тест без возможности не может пройти
     на верном ядре): `restart()` в строках `kernel_a18_failed_store_call_writes_nothing` и
     `kernel_a18_published_file_digest_never_overwritten`; `installation.set_credential` в
     строках `kernel_a19_service_timestamp_not_kernel_time` и
     `kernel_a19_monotonic_reading_never_stored`; `clock.set` в строке
     `kernel_a19_monotonic_reading_never_stored`;
   - не исправлено (на решение владельца): чтение `installation.owner_token` / `agent_token`
     без `installation` в строке — `kernel_a01_caller_supplied_identity_refused`,
     `kernel_a04_verdict_set_only_by_kernel`, `kernel_a16_unknown_token_uniform_refusal`,
     `kernel_a16_schema_checked_before_record_read`, `kernel_a17_instance_fixed_by_installation`,
     `kernel_a19_request_cannot_supply_time`, `kernel_a20_over_ceiling_refused_not_truncated`;
     `stub.requests` при строке с одним `stub_service()` (A07, A08, A10, A11, A14) — `requests`
     это атрибут `stub_service()`, новой возможности нет;
   - правки ревью, которым нужна возможность вне строки свидетеля (`clock` для
     `kernel_a11_restart_turns_in_flight_unknown` и `kernel_a14_recovery_completes_before_surface`,
     `sandbox_executions()` для `kernel_a03_unloadable_module_is_crashed`), откачены; свидетели
     помечены «частично» в своих ANN.md.
3. Объявлены, но ни одним тестом не используются: `installation.set_owner_token`,
   `installation.write_config_text`, `manifest.write_record_text`, действие заглушки `hold`.
4. Строка `kernel_a16_agent_code_not_run_in_kernel` (стр. 224) стоит после свидетелей A21 и
   нарушает порядок таблицы. Это косметика.
5. `token_comparisons()` (стр. 112) описан как «dependence on the matching prefix», а текст
   пропуска в тесте — как «dependence on the length of the matching prefix». Расхождение
   небольшое.
