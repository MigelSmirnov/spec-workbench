# Ревью свидетелей Registry — сводка

Предмет: 145 тестов в `tests/semantic/test_aNN_*.py` по решениям A01–A19 и A22. Из них 109 — свидетели: по одному на тег `[witness: verification:registry_aNN_<slug>]` в `02_rules_*.md`, имя теста совпадает со slug. Остальные 36 — непомеченные Required tests и дополнительные тесты правил. Для каждого свидетеля назван хотя бы один мутант (правдоподобный неверный Registry) и проверено, ловит ли тест этого мутанта (`review/ANN.md`). Классификация возможностей фикстуры — `review/CAPABILITIES.md`.

Ориентир ожиданий — решения States 1–7 и матрица защиты данных владельца (`sources/privacy_requirements_20261123.md`: «требование → мера → где реализовано → каким тестом подтверждается»). Registry v1 эталоном не служит (владелец, 2026-11-24).

Кода Registry нет, тесты не запускались. Проверено:

- `python -m py_compile` для всех 20 файлов;
- у каждого из 109 тегов ровно один тест с тем же именем (скрипт по тегам `02_rules_*.md` и AST тестов), и те же 109 имён — проверки `verification/configs/registry.yaml` code-factory;
- нет `skip` и `xfail`;
- AST-проверка: каждый атрибут объекта фикстуры (`semantic_runtime`/`rt`, включая `clock.*` и `faults.*`) есть в итоговом `RUNTIME_SURFACE.md`. Расхождений нет.

Обозначения:

- **ловит** — тест падает на мутанте при любой разумной фикстуре;
- **вероятностно** — ловит, только если в прогоне случилась гонка (барьер и повтор раундов) или выпал нужный порядок;
- **частично** — ловит при допущении о фикстуре, которого поверхность не задаёт;
- **не ловит** — мутант назван, тест его не видит (причина в ANN.md).

## По решениям

| решение | свидетелей | непомеченных | мутантов названо | ловит | вероятностно | частично | не ловит | исправлено при написании | выровнено 2026-11-24 |
|---|---|---|---|---|---|---|---|---|---|
| A01 | 11 | 3 | 34 | 33 | 1 (гонка) | 0 | 0 | 1 | 1 |
| A02 | 7 | 0 | 28 | 28 | 0 | 0 | 0 | 1 | 0 |
| A03 | 3 | 1 | 17 | 17 | 0 | 0 | 0 | 1 | 3 |
| A04 | 11 | 0 | 39 | 39 | 0 | 0 | 0 | 1 | 7 |
| A05 | 4 | 2 | 21 | 21 | 0 | 0 | 0 | 1 | 0 |
| A06 | 5 | 0 | 20 | 17 | 3 (порядок) | 0 | 0 | 2 | 0 |
| A07 | 3 | 3 | 10 | 7 | 3 (гонка) | 0 | 0 | 1 | 1 |
| A08 | 3 | 1 | 11 | 11 | 0 | 0 | 0 | 0 | 0 |
| A09 | 5 | 1 | 20 | 20 | 0 | 0 | 0 | 1 | 3 |
| A10 | 2 | 3 | 8 | 8 | 0 | 0 | 0 | 1 | 1 |
| A11 | 4 | 0 | 16 | 16 | 0 | 0 | 0 | 2 | 0 |
| A12 | 4 | 1 | 16 | 16 | 0 | 0 | 0 | 3 | 0 |
| A13 | 7 | 3 | 28 | 28 | 0 | 0 | 0 | 1 | 1 |
| A14 | 6 | 2 | 18 | 18 | 0 | 0 | 0 | 2 | 2 |
| A15 | 5 | 4 | 16 | 15 | 1 (гонка) | 0 | 0 | 2 | 1 |
| A16 | 4 | 8 | 20 | 20 | 0 | 0 | 0 | 2 | 2 |
| A17 | 8 | 2 | 34 | 32 | 0 | 1 | 1 | 1 | 0 |
| A18 | 7 | 1 | 33 | 33 | 0 | 0 | 0 | 2 | 3 |
| A19 | 6 | 1 | 24 | 24 | 0 | 0 | 0 | 1 | 1 |
| A22 | 4 | 0 | 16 | 16 | 0 | 0 | 0 | 0 | 0 |
| **итого** | **109** | **36** | **429** | **419** | **8** | **1** | **1** | **26** | **26** |

Мутанты посчитаны по строкам свидетелей в таблицах ANN.md. Строки непомеченных тестов (A05, A07, A08, A13, A18, A19) называют ещё 33 мутанта, все ловятся. «Исправлено при написании» — свидетели, у которых в ANN.md стоит «исправлен»: без правки тест падал бы на верном Registry или пропускал мутанта. «Выровнено 2026-11-24» — тесты, изменённые при переходе на итоговый `RUNTIME_SURFACE.md` (подробно — в разделах «Исправления» ANN.md). Вердикт ни одной строки от выравнивания не ухудшился. В A01 и A04 проверка формы анонимизированной и стёртой записи стала строже (`view_kind` на проводе нет).

Вероятностные и неполные случаи:

- **Гонки** (5 мутантов): A01 `concurrent_creates_make_one_record` M1, A07 `concurrent_publishes_consecutive_versions` M1–M3, A15 `sequential_and_concurrent_changes_number_in_order` M3. Поверхность даёт только одновременные вызовы из потоков («Concurrency»). Остановить транзакцию в середине нечем, а это было бы и ниже уровня поверхности.
- **Порядок** (3 мутанта, A06): мутант, сортирующий не по ключу, проходит с вероятностью 1/120, 1/6 и 1/24 — порядок вставки случайно совпадает с ожидаемым.
- **Частично** (A17 `missing_token_stops_start_none_owner_only` M4): owner-only Registry, открывший API сервисов на собственном порте, ловится, только если `service()` стучится туда же.
- **Не ловит** (A17 `listener_failure_serves_nothing_keeps_store`, ветка M1 «новое хранилище не удалось удалить»): сделать удаление невозможным, не мешая созданию, поверхность не позволяет.

## Выравнивание по итоговой поверхности (2026-11-24)

- Возможности отказа сведены в `faults.*`:
  - `fail_store_call(method)` — A07, A14, A16; в A16 таблица заменена методом, который её пишет: `insert_migration_closure_row`, `insert_audit_entry_row`;
  - `fail_next_commit()` — A14, A15;
  - `hold_backup_snapshot()` — A18.
- Сессия владельца: `owner()` входит сам только до первой сессии после старта. Перед запросами владельца после сдвига часов за 30 минут простоя добавлен `sign_in()`: A03 — 5 мест, A04 — 10, A18 — 4. В A16 `clock.set` перенесён до загрузки: загрузка принадлежит сессии (M11), поэтому `sign_in()` её бы потерял. В A18 третья часть `backup_during_write` разложена так, чтобы часы не прыгали посреди записей. В A13 тесты просроченной сессии не тронуты.
- `clock.suspend` двигает оба часа (A13 rule 2): A13 test 9 выражает приостановку им.
- Голые виды `validate`/`context` (A09 `_view`, A10), вложенные виды без `view_kind` (A01, A04), `owner_session().csrf` (A19).
- Перечни «surface used» в docstring 12 файлов приведены к итоговым именам.

## Находки на решения (в следующий раунд State 2/5)

Пока они не решены в своих состояниях, `71_semantic_test_export.json` остаётся `open` (STAGE_7_1_SEMANTIC_HANDOFF.md, «Handoff result», п. 5).

1. **A16 rule 6 — перепроверка при подтверждении недостижима через поверхность.** Все производственные id чеканит Registry, поэтому конфликт не может возникнуть между показом шага и подтверждением. `registry_a16_held_pointer_id_refuses_whole_import` показывает только отказ до шага (A16.md).
2. **A16 Required test 11 говорит «is refused», а State 7 (`OwnerActionStep.run`) отвечает нечистым `ImportMappingAnswer`, не отказом.** Тест следует State 7: шаг не показан, значение не создано. Формулировку Required test нужно выровнять (A16.md).
3. **A19 Required test 4 против правила State 5 об обрезанном теле.** Required test 4: «также когда объявленная длина меньше» — `file_too_large`. State 5 `serve_owner_request`: файл, чьи байты идут за объявленный конец, теряет закрывающий разделитель и отклоняется как `file_unreadable`. Тест проверяет длину, меньшую на один байт. Какой код верен при обрезке самого файла, должно решить State 2/5 (A19.md).
4. **State 5 не фиксирует путь отказа `agent_call_refused`.** A08 rule 7 и A10 rule 3 требуют «того же ответа», что для несуществующего. При этом State 5 Conventions «Stages» велит пути называть запись её id. Тесты сравнивают код, стадию и виды, но не путь (A08.md, A10.md, A04.md).
5. **Нет Required test у правил:**
   - A13 rule 1 (атрибуты cookie) и rule 7 (32 байта, сравнение за постоянное время, нет в URL и журнале);
   - A09 rule 1 (конфигурация держит токены, не права) и rule 5 (ни один токен не несёт прав владельца);
   - A10 rule 6 (вызов и изменение сессии применяются по одному).
   По матрице защиты данных (P6, D2) это меры безопасности без подтверждающего теста.
6. **Гонки засвидетельствованы только вероятностно:** A01 rule 7, A07 rule 2, A15 rule 5 («первым закоммиченный держит меньший номер»). Детерминированный свидетель потребовал бы точки остановки внутри транзакции; State 5 её не называет.
7. **`faults.fail_next_commit` без опоры в State 5/6** (CAPABILITIES.md). На нём держатся A14 `failed_store_leaves_no_change_no_entry` и `accepted_change_writes_one_entry_in_transaction` (первые половины), A15 `failed_change_leaves_sequence_unchanged`. Варианты: назвать в State 5 точку «перед коммитом» у `store.run_in_transaction` или перевести тесты на `fail_store_call` последнего метода действия.
8. **`faults.fail_next_backup_check("integrity")` без опоры.** `check_store_file` назван, но не как точка подмены (A18 `failed_backup_still_deletes_old_backups`, `integrity_failure_deleted_and_reported`). Удержание собственных проходов `instance_lifecycle` для `run_session_pass`/`run_backup_look` и сигнал конца прогона копии тоже не названы (6 свидетелей A18 и A13 test 9).
9. **A18: часы фикстуры не идут сами.** Мутант, который берёт мгновение записи копии не при первом чтении снимка, а позже, неотличим (A18.md). Нужны часы, сдвигающиеся между чтениями, или решение, что это не свидетельствуется.
10. **A17 test 6 «прерванный до переименования старт не оставляет хранилища»** показан только следствием; само прерывание требует возможности, которой нет (A17.md).
11. **A04-1 показан только парами стадий, которые называют Required tests:** (1)<(5), (2)<(4), (5)<(6). Перестановка, например, (3) и (4) не ловится (A04.md).
12. **A09 rule 4 в первом релизе не достигается:** ни один ответ Kernel не несёт поля `PERSONAL_DATA_FIELDS`, а у остальных сервисов высший класс `personal_data`. Тесты 5–6 показывают проверку класса на тестовом релизе (`configure_release`), потому что мера P3/D3 матрицы должна быть подтверждена тестом. Решение State 2 должно назвать этот способ.

## Сторонняя проверка (Codex judge-checks, 2026-11-24)

Судья `design_questions.py judge-checks` (Codex) оценил каждого из 109 свидетелей против формальных инвариантов, которые называет его Required test (`design_decision_witness.py binding_material`, `witness_judgement.py`). Итог: **54 `asserts`, 55 `partial`, 0 `does_not`**. Строка `workbench:state2_rules_decisions` (A21) — не свидетель этих тестов, здесь не учитывается.

Классы для каждого `partial`:

- **1 — пробел теста.** Названное пунктом проверяемо через поверхность, тест часть не утверждал. Тест усилен: значения из States 1–7, контроль рядом с отказом, без skip/xfail, имя прежнее.
- **2 — пункт заявляет больше, чем показывает.** Сценарий пункта касается не всего, что ему вменено. Тест не раздувается, это находка на State 2. Две разновидности:
  - **2a** — судья вменил инварианты, которых пункт не называет;
  - **2b** — названный инвариант — конъюнкция или бикондиционал, а пункт показывает одну его часть; остальные части показывают соседние пункты.
- **3 — универсальное.** Инвариант квантифицирован по всем значениям, спискам, страницам или копиям, конечный тест его целиком не утверждает. Переносится в `factory_checks_issue` из `90_factory_target.json` (TASK.md).

Если у свидетеля два класса, первым указан основной.

**Общая причина 2a — инструмент, не пункты.** Формальные инварианты каждого решения записаны одним блоком ```` ```text ```` с метками `-- ANN-n`. `required_test_items()` возвращает этот блок как один элемент, поэтому фильтр `statements` в `binding_material` (`set(invariant_ids(s)) & set(named)`) всегда пропускает блок целиком. Судья видит «binds A17-1», но под ним все инварианты решения как `invariant:` и вменяет их (A09, A11, A12, A15, A17 и другие). Пункты State 2 в этих случаях уже сужены до своих id. Сужать нечего, предлагается одно из двух:

- (а) `binding_material` делит блок по меткам `-- <id>` и передаёт только строки названных id. Это правка `tools/`: только на main через ветку `tools/*`;
- (б) State 2 записывает каждый инвариант отдельным пунктом.

| свидетель | класс | что сделано / предложено |
|---|---|---|
| A01 `equal_repeat_answers_existing_project` | 2b | A01-1 по моделям: пункт показывает Project; Customer/Room/Pointer — пункт 12. Оставить `Shows A01-1, A01-3` или расщепить A01-1 по моделям |
| A01 `publish_retry_returns_same_pointer` | 2b | то же для ArtifactPointer |
| A01 `concurrent_creates_make_one_record` | 1 | `race()`: снимок всех таблиц до и после каждой одновременной пары (+1 строка, +1/0 записей аудита, прочее не тронуто); добавлена пара «один издатель, разные факты» указателя |
| A02 `blank_display_name_refused` | 3 (+2b) | A02-2 «каждое хранимое обязательное значение»; ветку «отсутствует» A02-1 показывает `empty_optional_email_clears_it`. Перенос |
| A02 `out_of_form_values_all_named` | 2b | пункт показывает часть A02-4 о площади; комнаты и этаж — пункт 6 (`asserts`). Оставить `Shows A02-4` или расщепить A02-4 (rooms / area / floor) |
| A02 `required_texts_blank_refused_padded_kept` | 3 | «для каждого хранимого значения». Перенос |
| A03 `correction_without_alias_clears_it` | 1 | проверяется `customer_ref`: исправление ссылается на клиента, карточка и ответ его несут |
| A05 `restrict_restricted_customer_unchanged` | 1 | `_mints_no_confirmation`: в ответе нет `confirmation_id` ни на какой глубине, id журнала прежние |
| A05 `end_ended_relationship_keeps_date` | 1 | то же, для обоих повторов |
| A05 `regrant_keeps_access_version` | 1 | то же |
| A06 `same_instant_projects_list_by_id` | 3 | «every list answer», «equal keys never occur». Перенос |
| A06 `erased_customers_list_last` | 3 | то же |
| A06 `artifact_versions_list_highest_first` | 3 | то же |
| A06 `project_card_rooms_follow_list_rooms` | 3 | то же |
| A07 `concurrent_publishes_consecutive_versions` | 2b | «в той же транзакции» (A07-4) гонкой ненаблюдаемо; его показывает `failed_publish_leaves_nothing` (`asserts`). Предложено `Shows A07-1, A07-2, A07-3` |
| A08 `kernel_publish_names_owner_and_publisher` | 2a | судья вменил A08-1; пункт называет A08-2. Оставить `Shows A08-2` |
| A08 `withdraw_outside_set_not_found` | 2b (+2a) | показывает часть A08-1 об отзыве; публикацию — `presupro_publish_refused`. Оставить `Shows A08-1` |
| A09 `context_portal_answered_kernel_refused` | 2a | судья подтвердил A09-1, вменил A09-2/3. Оставить `Shows A09-1` |
| A09 `answer_above_class_refused_whole` | 2a | подтвердил A09-2, вменил A09-1/3. Оставить `Shows A09-2` |
| A09 `kernel_highest_class_business_confidential` | 2a | подтвердил A09-3, A09-2, вменил A09-1. Оставить `Shows A09-3, A09-2` |
| A10 `revoked_project_next_call_refused` | 2b | часть A10-1 `p in granted(x)`; токен и регистрацию показывают другие тесты A10/A11. Оставить `Shows A10-1` или расщепить A10-1 |
| A11 `ended_session_access_read_refused` | 1 | `agent_session_rows`: одна строка до конца, ни одной после |
| A11 `reregistered_ended_identity_empty` | 2a | подтвердил A11-2, вменил A11-1. Оставить `Shows A11-2` |
| A11 `owner_ended_session_call_refused` | 1 | строки сессии после конца нет, у другой сессии есть |
| A11 `ended_session_leaves_no_record` | 1 | «не зарегистрирована»: отказ A10 rule 3 как для незнакомой, `unknown_session` владельцу, нет в списке; контроль — живая сессия |
| A12 `grant_and_activate_moves_once` | 2a | вменён A12-1, пункт называет A12-2. Оставить `Shows A12-2` |
| A13 `eight_hours_and_sign_out_refused` | 2b (+2a) | конъюнкты A13-1 «8 ч» и «sign-out»; 30 мин и рестарт — пункты 8 и `restart_ends_owner_sessions`. Оставить `Shows A13-1` или расщепить A13-1 по конъюнктам |
| A13 `idle_limit_boundary_exclusive` | 2b (+2a) | конъюнкт «30 мин». То же |
| A13 `monotonic_clock_decides_validity` | 2b | «сессия кончается с подтверждением и загрузкой» — не A13-1 (это M11/A13 rule 2). Через поверхность не видно: сессии владельца не хранятся в `store_rows`. Оставить `Shows A13-1`, хвост о подтверждении и загрузке снять из пункта или дать возможность фикстуры |
| A14 `noop_archive_writes_no_entry_no_confirmation` | 3 (+2a) | обратное направление A14-1 («нет записи без принятого изменения») — по всем действиям. Перенос; A14-2 вменён |
| A14 `agent_projection_read_writes_no_entry` | 3 (+2a) | то же |
| A14 `accepted_change_writes_one_entry_in_transaction` | 1 (+3) | проверена запись `customer_recorded` клиента теста; обратное направление — перенос |
| A15 `erase_before_today_leaves_only_own_entry` | 2a | подтвердил A15-2 (и A15-3), вменил A15-1. Оставить `Shows A15-2` |
| A15 `sequential_and_concurrent_changes_number_in_order` | 2a | подтвердил A15-1, вменил A15-2/3. Оставить `Shows A15-1` |
| A17 `missing_token_stops_start_none_owner_only` | 2a | вменён A17-2. Оставить `Shows A17-1` |
| A17 `equal_secrets_stop_start` | 1 + 2b | все 15 пар шести секретов (было 5); длина — пункт 3. Оставить `Shows A17-2` или расщепить A17-2 (различие / длина) |
| A17 `secret_length_counted_in_utf8_bytes` | 1 + 2b | граница ±1 байт для каждого из 6 секретов (было 3); различие — пункт 2 |
| A17 `listener_failure_serves_nothing_keeps_store` | 2a | вменён A17-2. Ветка «удаление не удалось» не о A17-1 и через поверхность недостижима (см. «Не ловит» выше). Оставить `Shows A17-1` |
| A17 `unknown_variables_ignored_misspelt_item_missing` | 2a | вменён A17-2. Оставить `Shows A17-1` |
| A17 `service_address_with_tokens_and_wellformed` | 2a | то же |
| A17 `address_text_form_and_exclusive_bind` | 2a | то же |
| A17 `failed_check_stops_before_any_listener` | 2a | то же |
| A18 `backup_during_write_is_one_snapshot` | 1 + 3 | копия во время записи восстанавливается: только `first`, M12 = 1, `second` — `unknown_project`. «Каждая хранимая копия …» — перенос |
| A18 `retention_cutoff_exact_to_microsecond` | 2b | часть A18-1 о 30 × 24 ч; «не прошедшая проверку» — пункт 4 и `failed_backup_still_deletes_old_backups`. Оставить `Shows A18-1` или расщепить A18-1 |
| A18 `record_matches_snapshot_mismatch_deleted` | 3 | «каждая хранимая копия зашифрована, проверена, без сессий». Перенос |
| A18 `backup_unreadable_without_its_key` | 3 | то же |
| A18 `integrity_failure_deleted_and_reported` | 3 | то же |
| A18 `restored_store_holds_no_agent_session` | 3 | то же |
| A19 `access_request_markup_shown_as_text` | 3 | `render(v) = escape(v)` для каждого v. Перенос |
| A19 `quote_semicolon_name_round_trips` | 2a + 3 | вменён A19-1; A19-2 универсален. Оставить `Shows A19-2`, перенос |
| A19 `every_shown_value_escaped_csp_forbids_script` | 1 + 3 | форма ссылок враждебной сессии сверяется с формой простой (scheme, netloc, path, fragment, параметры). «Каждая страница/значение» — перенос |
| A19 `query_language_in_name_not_executed` | 2a + 3 | вменён A19-1. Оставить `Shows A19-2`, перенос |
| A19 `import_values_read_as_text_not_evaluated` | 2a + 3 | то же |
| A22 `undeclared_type_publish_refused` | 1 + 2b | проверен `owner_service == "presupro"` у контроля. Сам пункт показывает A22-3: предложено `Shows A22-3` (A22-1 — пункт 4) |
| A22 `first_release_declares_only_estimate` | 3 (+2a) | равенство множества объявленных типов — по всем именам, тест берёт выборку. Перенос; A22-2 вменён |

Итого по основному классу: **1 — 14** (тесты изменены: A01, A03, A05, A11, A14, A17, A18, A19, A22), **2 — 24** (2a — 14, 2b — 10), **3 — 17**.

После правок: `python -m py_compile` всех файлов проходит; у каждого из 109 тегов по-прежнему ровно один тест с тем же именем. Новый прогон судьи не делался: дайджест изменённых проверок другой, прежний вердикт к ним не относится.

### Находки State 2 (класс 2)

1. **Формат формальных инвариантов (общая причина 2a, 14 свидетелей):** A08 `kernel_publish_…`, A09 ×3, A11 `reregistered_…`, A12 `grant_and_activate_…`, A15 ×2, A17 ×6 (`missing_token`, `listener_failure`, `unknown_variables`, `service_address`, `address_text_form`, `failed_check`). Их пункты уже называют только свои id, менять id не нужно. Блок инвариантов надо давать судье по id: правка `binding_material` (ветка `tools/*` на main) или отдельные пункты в State 2.
2. **A07 test 1:** `Shows A07-1, A07-2, A07-3` вместо `A07-1, A07-2, A07-3, A07-4`.
3. **A22 test 1:** `Shows A22-3` вместо `A22-1, A22-3`.
4. **A13 test 9:** хвост «the session is ended, with its confirmation and upload, at the next pass» не относится к A13-1 и через поверхность не наблюдаем. Снять из пункта, либо назвать возможность фикстуры (State 5 `owner_sessions`) и отдельный инвариант.
5. **Конъюнкции под одним id (2b).** Либо принять `partial` как перенос, либо расщепить id в State 2:
   - A01-1 — по моделям: `equal_repeat`, `publish_retry`;
   - A02-4 — rooms / area / floor: `out_of_form`;
   - A08-1 — publish / withdraw: `withdraw_outside_set`;
   - A10-1 — token / registered / granted: `revoked_project`;
   - A13-1 — 8 ч / 30 мин / sign-out / restart: `eight_hours`, `idle_limit_boundary`, `monotonic_clock`;
   - A17-2 — различие / длина: `equal_secrets`, `secret_length`;
   - A18-1 — возраст / проверка: `retention_cutoff`.

   Ни одному из этих пунктов не нужен чужой сценарий: каждую часть показывает соседний пункт с `asserts`.

### Переносится в `factory_checks_issue` (класс 3)

A02 `blank_display_name_refused`, `required_texts_blank_refused_padded_kept`; A06 ×4 (`same_instant_projects_list_by_id`, `erased_customers_list_last`, `artifact_versions_list_highest_first`, `project_card_rooms_follow_list_rooms`); A14 `noop_archive_writes_no_entry_no_confirmation`, `agent_projection_read_writes_no_entry` (и обратное направление в `accepted_change_writes_one_entry_in_transaction`); A18 `record_matches_snapshot_mismatch_deleted`, `backup_unreadable_without_its_key`, `integrity_failure_deleted_and_reported`, `restored_store_holds_no_agent_session` (и «каждая копия» в `backup_during_write_is_one_snapshot`); A19 `access_request_markup_shown_as_text`, `quote_semicolon_name_round_trips`, `query_language_in_name_not_executed`, `import_values_read_as_text_not_evaluated` (и «каждая страница» в `every_shown_value_escaped_csp_forbids_script`); A22 `first_release_declares_only_estimate`. Всего 17 основных и 3 сопутствующих. Задача (`factory_checks_issue` в `90_factory_target.json`) ещё не открыта.

### Повторный прогон судьи после исправлений (2026-11-24)

Судья пересудил изменённые файлы (вердикты хранятся по дайджесту, `questions/checks/`). Итог по 110 привязкам: **60 `asserts`, 50 `partial`** (было 54 / 56). Из 50: 1 — проверка Workbench A21 (не тест Registry); остальные — классы 2 и 3 выше. После второго прогона дополнительно исправлены `registry_a05_every_repeated_transition_answers_unchanged` (теперь `asserts`) и `registry_a22_removed_type_pointers_still_listed` (остался `partial` только по классу 2a). `registry_a19_script_room_name_shown_as_text` получил `partial` без изменения своего теста — класс 3 (утверждение «для каждого значения»), колебание судьи.

Судья запускался на корне фабрики, собранном во временной папке как экспорт: `verification/configs/registry.yaml` из code-factory `main` и тесты кейса байт-в-байт в `projects/registry/tests/semantic/`. До экспорта `binding_material` иначе не находит файлов («names no readable file») — это пробел инструмента: TASK.md требует судить настоящие тесты до закрытия манифеста.

Ошибка инструмента (класс 2a, подтверждена): `required_test_items()` возвращает огороженный блок «Formal invariants» одним пунктом, поэтому фильтр `statements` в `design_decision_witness.binding_material` не сужает инварианты до названных в Required test, и судья требует от теста все инварианты решения. Исправление — в `tools/` на `main` Workbench через ветку `tools/*`; после него 14 вердиктов класса 2a нужно пересудить.
