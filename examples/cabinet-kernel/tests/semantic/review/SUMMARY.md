# Ревью свидетелей cabinet-kernel — сводка

Предмет: 135 тестов-свидетелей в `tests/semantic/test_a01…a21_*.py`, по одному на тег
`[witness: verification:kernel_aNN_*]` решений A01–A21. Для каждого теста назван хотя бы
один конкретный мутант, и проверено, ловит ли тест этого мутанта при любой разумной фикстуре
(`review/ANN.md`). Классификация возможностей фикстуры: `review/CAPABILITIES.md`.

Кода ядра нет, тесты не запускались. Проверено: `python -m py_compile` для всех изменённых
тестов; у каждого из 135 тегов по-прежнему ровно один тест с тем же именем;
`python tools/design_decision_witness.py examples/cabinet-kernel --coverage --json` — находки
без изменений (135 `witness_unverifiable`).

Обозначения: **ловят** — тест падает на названных мутантах своего инварианта (с учётом
исправлений); **частично** — часть разумных мутантов проходит, причина в ANN.md;
**формальные** — не ловят ни одного мутанта (здесь все — `pytest.skip`).

## По решениям

| решение | тестов | ловят | исправлено | частично | формальных осталось | новых вопросов | известные вопросы |
|---|---|---|---|---|---|---|---|
| A01 | 8 | 8 | 3 | 0 | 0 | 0 | — |
| A02 | 6 | 6 | 3 | 0 | 0 | 0 | — |
| A03 | 10 | 9 | 1 | 1 | 0 | 1 | A03 `os.fork` — решение владельца 06.10, не вопрос |
| A04 | 7 | 7 | 2 | 0 | 0 | 0 | — |
| A05 | 8 | 8 | 2 | 0 | 0 | 0 | — |
| A06 | 4 | 3 | 1 | 1 | 0 | 0 | A06 RT6 |
| A07 | 5 | 5 | 3 | 0 | 0 | 0 | A07 RT3 |
| A08 | 6 | 6 | 2 | 0 | 0 | 0 | — |
| A09 | 8 | 7 | 0 | 1 | 0 | 0 | — |
| A10 | 9 | 9 | 2 | 0 | 0 | 0 (связан с вопросом A11) | — |
| A11 | 6 | 5 | 0 | 1 | 0 | 1 | A11 RT5, A13 RT9 |
| A12 | 3 | 3 | 0 | 0 | 0 | 0 | — |
| A13 | 8 | 6 | 1 | 1 | 1 | 0 | A13 RT9 |
| A14 | 10 | 9 | 1 | 1 | 0 | 0 | — |
| A15 | 6 | 5 | 3 | 1 | 0 | 1 | — |
| A16 | 10 | 9 | 0 | 1 | 0 | 0 | — |
| A17 | 5 | 5 | 2 | 0 | 0 | 0 | — |
| A18 | 6 | 5 | 5 | 1 | 0 | 0 | — |
| A19 | 4 | 4 | 2 | 0 | 0 | 0 | — |
| A20 | 4 | 4 | 2 | 0 | 0 | 0 | — |
| A21 | 2 | 0 | 0 | 0 | 2 | 0 | A21 |
| **итого** | **135** | **123** | **35** | **9** | **3** | **3** | |

«Исправлено» — тесты, в которые внесена правка (усиление, контрольный сценарий или поправка,
без которой тест падал бы на верном ядре). Один из них, `kernel_a18_symlink_in_data_dir_refused`,
после правки остаётся «частично». Смысл ни одного Required test не менялся.

### Тесты, которые падали бы на верном ядре (исправлены)

- A10 `kernel_a10_used_approval_and_grant_do_not_cover_resend`: читал `fresh.attempt_number`,
  которого нет в State 6 `ShownApproval`. Заменено наблюдаемыми полями (новый `approval_id`,
  старое одобрение `used`, тот же `request_digest`); RT9 номер не называет.
- A18 `failed_store_call_writes_nothing`, `published_file_digest_never_overwritten`,
  `symlink_in_data_dir_refused`: продолжали вызывать ядро после `internal_error`, хотя процесс
  после него завершается (80_notes `serve_kernel`, `answer_request`). Добавлен `restart()`;
  в тесте symlink — только то, что видно без старта.
- A18 `store_module_sole_transaction_owner`: статическая проверка давала ложные срабатывания
  (`repo.commit(rev)`, docstring «Begin …»).
- A19 `service_timestamp_not_kernel_time`, `monotonic_reading_never_stored`: у сервиса не было
  credential, и по A17 rule 2 запрос не отправлялся (`credential_unresolved`). Добавлен
  `installation.set_credential`.

### Частично ловящие (причина)

| witness | что проходит | что нужно |
|---|---|---|
| `kernel_a03_unloadable_module_is_crashed` | ядро само делает `compile`/`ast.parse` и пишет `crashed` без песочницы | `sandbox_executions()` для свидетеля (правка подготовлена, откачена) |
| `kernel_a06_new_version_inherits_nothing` | повторное использование одобрения прежней версии (оно уже `used`) | `stub.set_down` для свидетеля; часть известного вопроса A06 RT6 |
| `kernel_a09_read_unsent_or_unanswered_unreachable` | повтор при отказе в соединении | `stub.requests` не видит отказанных соединений; счётчика попыток соединения на поверхности нет |
| `kernel_a11_restart_turns_in_flight_unknown` | `started_at`/`ended_at` восстановления из не того источника, если часы фикстуры стоят | `clock` для свидетеля (правка подготовлена, откачена) |
| `kernel_a13_one_node_executes_at_a_time` | параллельное исполнение с метками времени записи | `clock` для свидетеля; строгое `<` решалось бы фикстурой (правка откачена) |
| `kernel_a14_recovery_completes_before_surface` | восстановление лениво внутри первого запроса | `clock` для свидетеля (правка подготовлена, откачена) |
| `kernel_a15_spool_file_ceiling` | ядро без проверки `spool_file_bytes_max` | недостижимо при release v1 — новый вопрос A15 |
| `kernel_a16_token_match_unique_constant_time` | сравнение токенов не за постоянное время | `token_comparisons()` — шов без опоры, «not yet specified» |
| `kernel_a18_symlink_in_data_dir_refused` | запись случая испытания при неудавшейся публикации | возможность убрать ссылку (например, `faults.remove_symlink`) |

### Формальные (оставлены)

- `kernel_a13_resolved_unknown_conclusion` — `pytest.skip` до решения известного вопроса A13 RT9.
- `kernel_a21_security_review_gate_complete`, `kernel_a21_security_references_resolve` —
  `pytest.skip`: это дизайн-гейт, а не поведение ядра; известный вопрос A21. Для справки:
  `design_lint --state 2` сейчас без находок.

## Вопросы владельцу (новые)

Подробно, с цитатами — в ANN.md соответствующего решения. Выбор не сделан.

1. **A03 RT10 — считается ли loopback `lo` сетевым интерфейсом.** A03 rule 1: «… network
   namespaces, no network interface»; новый сетевой namespace bubblewrap всегда содержит `lo`.
   (а) `lo` считается — ядро обязано его убрать, тест как есть; (б) «кроме loopback» — тест
   допускает `lo`, формулировку уточнить.
2. **A11 RT7 (и RT3) — у `ShownApproval` нет `attempt_number`.** M24 и RT7 («each approval the
   number of the attempt it was requested for») его требуют, State 6 `ShownApproval` не несёт,
   а других путей чтения одобрений нет. Тесты RT3/RT7 читают поле и на верном ядре упадут.
   (а) добавить поле в `ShownApproval`; (б) снять проверку номера одобрения (меняет смысл RT7).
   Тот же пробел делает непроверяемым пункт A10 rule 1 «approvals requested before it never count».
3. **A15 RT3 недостижим при release v1.** `output_bytes` = 64 MiB < `spool_file_bytes_max` =
   128 MiB, а `service_response_bytes_max` = `spool_file_bytes_max`, поэтому `resource_exhausted`
   всегда даёт другой потолок. (а) принять тест и переформулировать RT3; (б) изменить потолки;
   (в) свидетельствовать статически или новой возможностью.

Известные, уже поднятые, только упомянуты где встретились: A06 RT6, A07 RT3, A11 RT5, A13 RT9, A21.

### Required tests без witness (не вопрос ревью, к сведению)

Без тега и, значит, без теста: A02 RT4; A03 RT6; A05 RT6, RT7; A06 RT3, RT4; A08 RT5; A09 RT6;
A10 RT3, RT8; A11 RT4; A12 RT3; A13 RT5; A16 RT6.

## Швы фикстуры (итог по CAPABILITIES.md)

- **Снаружи** — всё, кроме перечисленного ниже: файлы установки и манифеста, HTTP-заглушка и все
  её действия (включая `kill_kernel`), `restart`, `kernel_exited`, `start_second_kernel`,
  `host.*`, `sandbox_executions`, `sandbox_runtime_paths`, чтение каталога данных и хранилища,
  `faults.place_symlink` (ставится между запросами), `surface_answers`, `host_output`,
  `process_arguments`, `kernel_sources`, `release`, `host_scratch_directory`.
  Пограничные, решены как «снаружи» при привилегированном наблюдателе процессов:
  `faults.unconfirmed_cleanup`, `kill_on_sandbox_start`.
- **Швы с опорой в State 5:** `clock.set`, `clock.advance` (`50_public_apis.md` `clock.kernel_now`:
  «replaceable as a whole in tests (A19)»); `clock.fix_monotonic` — опора косвенная (та же фраза,
  явно монотонный источник назван только в State 3 и State 7). Используют 12 свидетелей
  (A01 ×3, A10, A11, A12, A13 ×2, A14, A19 ×3 — список в CAPABILITIES.md). Канал доставки
  подмены в отдельный процесс ядра не назван — забота обёртки Factory.
- **Швы без опоры в State 5/6:** `faults.fail_store_change`, `faults.crash_during_value_write`,
  `faults.alter_value_write`, `token_comparisons()` — спецификация называет только свойство.
- **Свидетели, зависящие от шва без опоры (вход для решения владельца: узаконить швы в
  State 5/6 или перевести в `note:`):**
  - `kernel_a16_token_match_unique_constant_time` (`token_comparisons`; часть уже skip);
  - `kernel_a18_failed_store_call_writes_nothing` (`faults.fail_store_change`);
  - `kernel_a18_published_file_digest_never_overwritten` (`faults.alter_value_write`);
  - `kernel_a18_value_write_atomic_publish` (`faults.crash_during_value_write`).

  Если владелец не примет «снаружи» для пограничных — добавятся
  `kernel_a03_unconfirmed_cleanup_stops_kernel` и `kernel_a14_restart_in_flight_becomes_unknown`.

## Изменения RUNTIME_SURFACE.md (исправление явной ошибки)

Таблица «Places the surface cannot reach yet» не называла возможность, без которой тест не может
пройти на верном ядре. Дописано в строки, больше ничего не менялось:

- `kernel_a18_failed_store_call_writes_nothing`, `kernel_a18_published_file_digest_never_overwritten`:
  `restart()` — процесс завершается после ответа `internal_error` (80_notes `serve_kernel`).
- `kernel_a19_service_timestamp_not_kernel_time`: `installation.set_credential` — без него запрос
  не отправляется (A17 rule 2).
- `kernel_a19_monotonic_reading_never_stored`: `installation.set_credential` (то же) и `clock.set`
  (тест вызывал его и до ревью).

Не исправлено, на решение владельца (подробно — CAPABILITIES.md, «Ошибки и несоответствия»):
чтение `installation.owner_token`/`agent_token` у семи свидетелей без `installation` в строке
таблицы; `stub.requests` при строке с одним `stub_service()` (атрибут той же возможности);
вводная фраза «the next section lists» указывает на раздел, озаглавленный как список
недостижимого. Правки ревью, которым понадобилась бы возможность вне строки свидетеля (`clock`
для A11/A14, `sandbox_executions()` для A03), откачены, а свидетели помечены «частично».
