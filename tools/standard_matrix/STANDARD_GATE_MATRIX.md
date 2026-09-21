# Матрица «правило стандарта → гейт воркбенча» · рабочая версия 2026-09-21

Данные: `standard_gate_matrix.json` (412 правил) и `skill_triage.json` (105 фрагментов `SKILL.md`). Собрано девятью
агентами только на чтение, по диапазону строк каждому; гейт засчитан только с `файл:строка`, где правило реально
проверяется. Выборочная проверка 9 утверждений «гейт есть»: 7 точных, 2 — гейт держит часть правила. **Покрытие ниже —
верхняя граница.** Вызов фабричного валидатора на Stage 9 (FA005) гейтом воркбенча не считается: он срабатывает после
того, как спека написана.

## Покрытие по разделам

| § | раздел | правил | гейт воркбенча | гейт называет § | проверяет фабрика | правил валидности без гейта |
|---|---|---|---|---|---|---|
| — | введение, чек-лист, пример | 42 | 24 | 2 | 25 | 10 |
| 1 | contracts | 6 | 3 | 0 | 3 | 2 |
| 2 | notes | 22 | 13 | 0 | 13 | 3 |
| 4 | config | 5 | 1 | 0 | 3 | 2 |
| 5 | models | 31 | 8 | 0 | 21 | 15 |
| 6 | rules и backend IR | 113 | 49 | 7 | 81 | 33 |
| 7 | imports | 14 | 0 | 0 | 10 | 8 |
| 8 | module_functions | 7 | 3 | 0 | 3 | 1 |
| 9 | module_order | 3 | 0 | 0 | 2 | 1 |
| 10 | module_paths | 4 | 2 | 0 | 2 | 0 |
| 11 | default_module | 3 | 1 | 0 | 2 | 2 |
| 12 | типы и происхождение имён | 11 | 1 | 0 | 11 | 9 |
| 13 | properties | 7 | 0 | 0 | 5 | 5 |
| 14 | determinism | 4 | 0 | 0 | 2 | 2 |
| 15 | данные | 140 | 39 | 4 | 33 | 56 |
| | **всего** | **412** | **144** | **13** | **216** | **149** |

## §15 по подразделам

| подраздел | правил | с гейтом |
|---|---|---|
| 15 | 10 | 3 |
| 15.1 | 22 | 11 |
| 15.2 | 11 | 3 |
| 15.3 | 8 | 2 |
| 15.4 | 9 | 0 |
| 15.5 | 25 | 7 |
| 15.6 | 3 | 0 |
| 15.7 | 10 | 0 |
| 15.8 | 3 | 0 |
| 15.9 | 8 | 3 |
| 15.10 | 10 | 2 |
| 15.11 | 21 | 8 |

## Правила валидности спеки без гейта воркбенча

Это список работ. `Ф` — правило проверяет фабрика: воркбенч пропускает то, что фабрика отвергнет.


### §— введение, чек-лист, пример

- L57 §0 `Ф` — Не складывай данные в notes: поведение остаётся в notes, а значения, таблицы, словари, лимиты и политики выносятся в `config`, `models` или `rules`.

### §1 contracts

- L76 §1 `Ф` — `self` указывается в сигнатуре методов.
- L78 §1 — В сигнатурах используются реальные имена типов из проекта, не абстракции.

### §2 notes

- L196 §2 `Ф` — Inline-данные в notes запрещены (таблицы соответствий, allow-lists, пороги, TTL, пути, рейтинги, размеры, словари alias'ов): они размещаются в `config`, `models` или `rules`, а note остаётся address-only: `MUST use = rules.some_policy`.
- L200 §2 — Если caller располагает данными в форме, отличной от контракта callee, это поведение записывается классифицированной нотой caller-а; владелец ноты — caller/callsite, не callee.
- L208 §2 — Нота остаётся требованием к поведению: выражения, вызовы методов, точечная навигация и строковый микро-синтаксис в ней запрещены.

### §4 config

- L237 §4 `Ф` — `config.role` имеет служебное значение `"data"`; `config.schema_version` на верхнем уровне — целое число версии секции.
- L238 §4 `Ф` — Имена `role` и `schema_version` зарезервированы и не используются внутри вложенных namespace config.

### §5 models

- L269 §5 — В `models` ключ `role` имеет служебное значение "data", `schema_version` — целое число версии секции; оба имени зарезервированы и не являются объявлениями моделей.
- L274 §5 `Ф` — Модели должны совпадать с реальными dataclass'ами в `models.py`.
- L276 §5 — Модели с `kind` поле `identity` не содержат.
- L286 §5 — У обычной модели-произведения (без `kind`) `fields` обязательны.
- L292 §5 `Ф` — Реестр `kind` закрыт (enum, mapping, vocabulary, catalog, discriminated_union, interface); неизвестный `kind` делает спеку невалидной.
- L310 §5 `Ф` — Для `discriminated_union` обязательны `discriminator` и непустой `variants`; `fields` отсутствует или пуст.
- L311 §5 `Ф` — Каждый variant — объявленная в этой же спеке модель с `fields`.
- L312 §5 `Ф` — Каждый variant содержит поле с именем дискриминатора типа `Literal['…']` с уникальным в пределах union значением.
- L314 §5 `Ф` — Union внутри union (variant с `kind: discriminated_union`) запрещён.
- L321 §5 `Ф` — Произвольный `type_alias` в спеке запрещён; alias вправе эмитить только backend для именованной конструкции языка.
- L341 §5 `Ф` — Интерфейс, экспортируемый модулем (`imports.internal`), обязан иметь хотя бы один контракт `Имя.*`.
- L343 §5 `Ф` — Каждый контракт интерфейса — полная машинно-проверяемая сигнатура: все параметры с типами и возвращаемый тип; усечённые записи не допускаются.
- L345 §5 `Ф` — У интерфейса нет `fields` и нет данных.
- L374 §5.1 `Ф` — Список `implementations` у `local`/`policy` уникален (без повторов).
- L381 §5.1 `Ф` — `policy`-реализация не имеет исполняемой границы: каждый аргумент её `__init__` — объявленный interface, объявленная модель или скаляр (`str|int|bool|Decimal`); она не владеет соединениями, файлами или сетью.

### §6 rules и backend IR

- L414 §6 `Ф` — `rules.role` имеет служебное значение "data", `rules.schema_version` — целое число версии секции; оба имени зарезервированы и не являются политиками.
- L417 §6 `Ф` — Обычный ключ `rules` содержит декларативную domain/policy semantics и не является исполняемым кодом или псевдокодом.
- L531 §6.1 `Ф` — `projections` обязаны точно покрывать поля модели возвращаемого типа из контракта projection-функции; форма модели и сигнатура в IR не дублируются.
- L545 §6.1 `Ф` — Пара `(method, path)` и `handler` уникальны; status/method/response/return modes принадлежат закрытым реестрам версии backend; неизвестные поля на всех узлах запрещены.
- L723 §6.3 — Для `transaction: "external"` форму guard-а выбирает контракт конструктора — `(self, connection, context)` или `(self, connection)`, других форм нет.
- L744 §6.3 `Ф` — Для `transaction: "owned"` `schema_function` имеет контракт `(database_url: str) -> None`; для `"external"` — `(connection: object) -> None`.
- L774 §6.3 `Ф` — Bind-ы фильтра v3: `argument_set` — ровно bind, column, argument, тип аргумента `tuple[<scalar>, ...]`; `optional_argument` — ровно bind, column, argument, тип `<scalar> | None`.
- L808 §6.3 — Кодек json_value у postgres_sync_v1 несёт только скаляры, str-enum и dict и не несёт коллекцию record-моделей: колонка json_value с типом tuple[<Model>, ...] под postgres_sync_v1 недопустима.
- L814 §6.3 `Ф` — Модуль репозитория обязан импортировать вложенные модели кодека (element_model, модели внутри типа json_value) через imports.module_internal.<module>; иначе emitter останавливается с перечнем недостающих имён.
- L825 §6.3 `Ф` — Терм фильтра с bind argument/optional_argument/argument_set может нести path — непустой список имён полей; column при этом обязана иметь storage json_model, и путь обязан резолвиться в скалярное поле вложенной модели.
- L830 §6.3 `Ф` — Для элемента unique вида {column, path} действуют те же правила, что для path в фильтре: колонка обязана иметь storage json_model, путь обязан резолвиться в скалярное поле вложенной модели.
- L863 §6.4 `Ф` — rules.holded_transport_backend/v1 — закрытый IR: только emitter python_httpx_holded_purchase_v1 (один POST create, один GET списка, один GET документа, без пагинации/повторов); IR обязан фиксировать wiring, HTTP method/path, имя credential header, TLS/redirect/retry policy, отображения payload/item и трёх response shapes.
- L865 §6.4 — Runtime credential берётся из config; секретное значение не входит в IR.
- L887 §6.5 `Ф` — rules.source_byte_store_backend/v1 — закрытая форма (kind, schema_version 1, backend.emitter = python_filesystem_source_byte_store_v1, wiring{module, concrete_class, interface SourceByteStore, models_module}, layout с фиксированными значениями).
- L910 §6.5 `Ф` — Модуль wiring.module владеет ровно одним классом wiring.concrete_class, реализующим Protocol SourceByteStore из models с фиксированными контрактами __init__, final_reference_for, stage, verify, publish, remove_staging.
- L940 §6.6 `Ф` — rules.credential_security_backend/v2 — закрытая форма (kind, schema_version 2, backend.emitter = python_credential_security_v2, wiring{module, models_module}, secret{entropy_codec, envelope_separator, selector_codec}, secret_hash{argon2id, RFC_9106_LOW_MEMORY, hmac_sha256}); версия 1 донормативная и стандартом не описывается.
- L961 §6.6 `Ф` — Модуль wiring.module владеет ровно тремя функциями с фиксированными контрактами (issue_service_credential, parse_service_token, verify_service_secret); IssuedCredentialSecret и PresentedCredentialSecret — value-модели в models.
- L989 §6.7 `Ф` — rules.canonical_digest_backend/v1 — закрытая форма (kind, schema_version 1, единственный emitter python_canonical_json_digest_v1, wiring{module}, recipes{<name>: input model|json_text|string_tuple|bytes}).
- L1010 §6.7 — Модуль wiring.module владеет ровно одной функцией на рецепт, в порядке объявления, с контрактом, фиксированным полем input.
- L1035 §6.7 `Ф` — Ключи рецепта закрыты: model требует все три поля (input, exclude_fields, datetime_normalization), остальные входы — только input.
- L1047 §6.8 `Ф` — Форма time_source_policy/v1 закрыта: wall_clock{authority_modules, allowed_primitives, single_host_source, samples_per_read}, elapsed_time{authority_modules, allowed_primitives, samples_per_read, persisted}, representation{type, field, unit, conversion}; словарь примитивов и конверсий закрыт версией.
- L1074 §6.8 `Ф` — wall_clock обязателен; elapsed_time, representation и оба samples_per_read — по необходимости; отсутствующий elapsed_time означает, что измерять длительность не вправе никто.
- L1086 §6.8 `Ф` — Если полномочие на длительность принадлежит тому же модулю, что и настенные часы, он единственный читатель обоих часов хоста и обязан принадлежать backend-у §6.9 версии 3, а потребители получают длительность через wiring.elapsed_clock_function.
- L1092 §6.8 `Ф` — authority_modules — модули из module_functions; пустой список вместе с пустым allowed_primitives означает «настенные часы не читает никто».
- L1094 §6.8 `Ф` — single_host_source: true требует ровно одного модуля и ровно одного примитива.
- L1097 §6.8 `Ф` — conversion — из закрытого набора identity_ns, floor_ns_to_us, floor_ns_to_ms, floor_ns_to_s; unit обязан совпадать с результатом конверсии, единица примитива — с её входом, а models.<type>.fields.<field> обязан быть int.
- L1130 §6.9 `Ф` — system_clock_backend/v1 — закрытая форма: emitter python_system_utc_clock_v1, wiring{module, concrete_class, interface Clock, models_module}, time{source system_utc, representation timezone_aware_utc_datetime, read per_call}; один класс порта Clock, now возвращает timezone-aware UTC datetime.
- L1146 §6.9 `Ф` — system_clock_backend/v2 — закрытая форма: emitter python_host_epoch_clock_v1, wiring{module, function, models_module}, time{policy rules.time_source_policy, read per_call}; примитив, число показаний и представление в backend-е не повторяются, а читаются из rules.time_source_policy.
- L1162 §6.9 `Ф` — Версия 2 требует: single_host_source: true с wiring.module как единственным полномочным модулем, примитив time.time_ns, samples_per_read: 1, объявленный representation; module_functions[<module>] == [<function>] и контракт <function>: "() -> <representation.type>".
- L1173 §6.9 `Ф` — system_clock_backend/v3 — закрытая форма: emitter python_host_clock_v1, wiring{module, wall_clock_function, elapsed_clock_function, models_module}, time{policy, read per_call}; тот же модуль — единственный читатель обоих часов хоста.
- L1189 §6.9 `Ф` — Версия 3 сверх требований версии 2 требует от elapsed_time: authority_modules == [<module>] (раздать полномочие конечным модулям нельзя — дефект валидации), ровно один примитив time.monotonic_ns, samples_per_read: 1, persisted: false.
- L1193 §6.9 `Ф` — module_functions[<module>] версии 3 — ровно две операции с контрактами <wall_clock_function>: "() -> <representation.type>" и <elapsed_clock_function>: "() -> int"; иных функций и классов модуль не содержит.
- L1203 §6.9 `Ф` — Версия 2 не расширяется: она владеет только операцией настенных часов и служит спекам, где длительность измеряют другие модули.

### §7 imports

- L1239 §7 `Ф` — Голое имя модуля в `imports.stdlib` — runtime-импорт и не связывает типовых имён; тип, используемый в полях или сигнатурах, обязан быть связан полной import-строкой.
- L1243 §7 `Ф` — `imports.third_party` записывается полными строками импорта как в коде.
- L1244 §7 `Ф` — `imports.internal` — модуль → список экспортируемых символов; это полный публичный export surface provider-модуля (см. также 1283).
- L1246 §7 `Ф` — Имена consumer/provider в `module_internal` — логические ключи из `module_functions`; каждый символ обязан принадлежать provider.
- L1249 §7 — `module_internal[consumer][provider]` содержит минимальный прямой runtime import surface consumer-модуля, а не копию публичного API provider-а; символ добавляется только если consumer обязан импортировать его для своих contracts, classified notes или иного явно объявленного module-local поведения.
- L1255 §7 — Для provider-а `models` перечисляются только модели, enum и interface, которые consumer непосредственно называет/конструирует/проверяет в своём runtime коде.
- L1261 §7 — Запрещено заполнять `module_internal` широким переносом всего `imports.internal[provider]`, всего реестра `models` или wildcard-семантикой «может понадобиться»; лишний символ — ошибка спеки, а не безвредная избыточность.
- L1266 §7 — Если consumer не импортирует ни одного символа provider-а, ребро provider-а отсутствует целиком; facade/router также перечисляет только реально используемые символы.

### §8 module_functions

- L1317 §8 — Константы (UPPER_CASE) тоже включаются в `module_functions`.

### §9 module_order

- L1339 §9 `Ф` — `module_order` — порядок сборки модулей: зависимости идут первыми.

### §11 default_module

- L1386 §11 `Ф` — `default_module` — строка с именем модуля; при отсутствии секции дефолтится к "app".
- L1388 §11 — Модуль с именем `default_module` должен существовать в `module_functions`.

### §12 типы и происхождение имён

- L1400 §12 `Ф` — Builtins — закрытый список, фиксируемый стандартом (str, int, float, bool, bytes, None, object, dict, list, set, tuple, Exception, BaseException + Literal[...], type[X], X | None); список не расширяется под проект.
- L1409 §12 `Ф` — Класс, которым владеет модуль, является типом только если символ экспортирован через `imports.internal` и имеет хотя бы один классовый контракт `Имя.метод`; экспортированные функции и константы типами не являются.
- L1415 §12 `Ф` — Каждое имя в type position (поле модели, сигнатура contracts, `variants`) обязано резолвиться ровно в один источник; неизвестное имя — ошибка валидации, не warning.
- L1418 §12 `Ф` — Коллизия происхождения — всегда BLOCK: builtin, модель, import, interface и union не могут неоднозначно владеть одним локальным именем.
- L1430 §12 `Ф` — Нормативный NOT-list: generics/TypeVar, callable-типы и иные runtime-only типы в полях моделей в язык не входят; обход через notes или нестандартные ключи делает спеку невалидной.
- L1431 §12 `Ф` — Untagged unions запрещены: union без дискриминатора не входит в язык (nullable `X | None` остаётся полевой записью).
- L1434 §12 `Ф` — Модельное наследование как механизм union запрещено: принадлежность варианта объявляется в `variants`, а не через subclass.
- L1436 §12 `Ф` — Проектное расширение builtins запрещено: новый тип — это модель, объявленный import или изменение стандарта.
- L1440 §12 `Ф` — Произвольный именованный `type_alias` запрещён: alias может появляться лишь как форма эмиссии именованных конструкций языка (раздел 5).

### §13 properties

- L1447 §13 `Ф` — Ключ `properties` — точное имя из `contracts` (функция обязана существовать в contracts, повтор в 1482), значение — список строковых булевых выражений.
- L1464 §13 `Ф` — Нормативное подмножество выражений properties замкнуто: корни result/аргументы/self, литералы, атрибуты/элементы, сравнения, in/not in, булевы и арифметические операции, comprehensions, чистые builtins abs,sum,len,all,any,range,min,max,str, строковые startswith/endswith/lower/upper, одна верхнеуровневая `A implies B`.
- L1475 §13 `Ф` — Выражение обязано возвращать `bool` и не должно выполнять import, assignment, I/O, mutation, вызов проектной функции, доступ к clock/random/global state или вычисление через undeclared helper.
- L1483 §13 `Ф` — Пустой список properties запрещён: удали ключ, если properties нет.
- L1484 §13 `Ф` — Имена аргументов в properties должны точно совпадать с контрактом.

### §14 determinism

- L1507 §14 `Ф` — Ключ `determinism` обязан существовать в `contracts`, значение обязано быть JSON boolean.
- L1508 §14 `Ф` — `true` запрещает зависимость результата от clock, random, uuid, secrets, порядка hash-контейнеров и иного скрытого недетерминированного состояния.

### §15 данные

- L1523 §15 — Замыкание значений обязательно наравне с замыканием типов (§12): спека без замкнутых значений допускает несколько корректных сборок и не может быть собрана детерминированно.
- L1532 §15 — Результат авторского semantic-gate (вопрос владельцу продукта) обязан быть материализован в спеке так, чтобы валидатор отличал принятое решение от пропущенного вопроса.
- L1536 §15 — Четыре механизма перехода к детерминированной эмиссии (derivation, placement, lowering, legacy recovery) различаются; смешивать их запрещено.
- L1541 §15 — placement: продуктовое значение обязано получить ровно один дом по процедуре 15.2.
- L1558 §15.1 — Спека содержит только значения времени сборки: значение принадлежит спеке тогда и только тогда, когда оно известно до запуска приложения и не зависит от действий пользователя.
- L1564 §15.1 — Экземпляры доменных сущностей в спеке не хранятся; у runtime-данных в спеке есть только поле в models.
- L1567 §15.1 — Иллюстративное значение запрещено: пример в note («например, 12.5») при генерации превращается в дефолт или literal в коде.
- L1571 §15.1 `Ф` — Значение, порождаемое внешней системой (remote id, номер документа, токен), в спеку не попадает никогда, включая примеры формата.
- L1629 §15.1.1 — Запрещено выводить identity: entity из наличия таблицы, ORM, id, UUID, persistence или CRUD.
- L1632 §15.1.1 — Запрещено добавлять id «на будущее»; стабильная идентичность допустима только когда её требует продуктовая семантика либо внешний владелец данных.
- L1635 §15.1.1 — Запрещено считать составное значение entity только потому, что оно представлено отдельной моделью.
- L1642 §15.1.1 — Для identity: entity писатель обязан определить, чем сохраняется идентичность экземпляра через изменения состояния.
- L1689 §15.2 — Каждое значение спеки имеет ровно один дом, определяемый процедурой размещения.
- L1697 §15.2 — Проверка 1: значение, которым владеет внешняя система, в спеке не хранится (класс mirrored, 15.5).
- L1698 §15.2 — Проверка 2: значение, вводимое пользователем во время работы приложения, в спеке не хранится.
- L1699 §15.2 — Проверка 3: значение, меняющееся при смене окружения или деплоя, размещается в config.
- L1700 §15.2 — Проверка 4: значение, меняющееся по продуктовому, нормативному или коммерческому решению, размещается в rules.
- L1717 §15.3 `Ф` — Воспроизведение содержимого блока данных внутри note запрещено.
- L1723 §15.3 — Ссылка указывает на наименьший узел, который потребитель использует целиком; ссылка на родителя при использовании одного листа запрещена.
- L1726 §15.3 `Ф` — Каждый лист блока данных обязан быть достижим хотя бы одной ссылкой из notes, properties или другого блока данных.
- L1727 §15.3 `Ф` — Недостижимый лист — мёртвые данные и ошибка спеки, а не безвредный остаток.
- L1746 §15.4 `Ф` — Значение фиксированной точности записывается строкой ("21.00"), а не числом с плавающей точкой; тип восстанавливается при эмиссии по объявленному типу поля.
- L1749 §15.4 — Каждая строка табличных данных имеет стабильный идентификатор, объявленный в самих данных.
- L1750 §15.4 — Позиция в массиве идентификатором строки не является.
- L1753 §15.4 — Вычисляемые значения в блоках запрещены: никаких выражений, шаблонов, подстановок и ссылок одного листа на другой.
- L1756 §15.4 — Дублирование листа в двух домах запрещено.
- L1757 §15.4 — Совпадение значений в разных домах допустимо только как случайное; если значения обязаны совпадать, у них один дом и одна ссылка.
- L1785 §15.5 — Модель `mirrored` локально read-only, обязана иметь `remote_id` и `synced_at`; расхождение разрешается в пользу remote.
- L1794 §15.5 — `issued` обязан хранить значения, а не ссылки на `master` и `rules`; нормализация выпущенного документа запрещена.
- L1798 §15.5 — Модель класса `mirrored` не участвует в расчётах: факт внешней системы читается из подтверждённого ответа, а не выводится локально.
- L1801 §15.5 — Взаимодействие с внешней системой отделяется переводящим слоем: DTO внешнего API не проникает в доменные модели.
- L1803 §15.5 — Состояние обмена — явная модель состояний, а не булев флаг; повторяемый вызов снабжается idempotency key, выводимым из содержимого.
- L1811 §15.5.1 `Ф` — Выводимые ограничения не повторяются в persistence-данных; nullable/non-nullable не назначается повторно — обязательность берётся из объявления поля в `models`.
- L1846 §15.5.1 `Ф` — Если backend допускает несколько storage representations для domain type, спека обязана явно выбрать одну из закрытого словаря; единственный выбор является derivation и в проекте не дублируется.
- L1853 §15.5.1 — Имена внутренних codec/helper-функций принадлежат backend-эмиттеру и не добавляются в `contracts`, `module_functions` или notes.
- L1856 §15.5.1 — Ручной проектный кодек внутри детерминированно эмитируемого persistence-модуля запрещён; неподдерживаемая пара типов — DEFECT, а не повод сгенерировать `_parse_*`/`_row_to_*`.
- L1859 §15.5.1 — Codec выполняет только представительное преобразование; нормализация, default, fallback, фильтрация обязаны иметь владельца в models/rules/config/properties/поведении функции.
- L1891 §15.6 — Для `master`-модели, значения которой цитируются в `issued`, объявляется период действия (`valid_from`, `valid_to`), а изменение выполняется вставкой новой строки, не UPDATE.
- L1894 §15.6 — Расчёт, порождающий `issued`, обязан фиксировать момент, на который выбраны значения; момент хранится в документе.
- L1896 §15.6 — Политика в `rules` с датой вступления в силу объявляет её явно; note ссылается на политику адресно и не воспроизводит дату.
- L1908 §15.7 `Ф` — `schema_version` — целое, обязательно на верхнем уровне `config`, `models` и `rules`.
- L1912 §15.7 — Несовместимое изменение (удаление/переименование обязательного поля, смена типа, удаление значения закрытой таксономии, смена стабильного идентификатора строки) требует повышения `schema_version`; совместимое — не повышает.
- L1915 §15.7 — Несовместимое изменение объявляет переход как последовательность обратимых фаз expand/contract; одношаговая миграция запрещена.
- L1939 §15.7.1 — Подтверждённое продуктовое значение размещается обычной процедурой 15.2; специальный legacy-дом не создаётся.
- L1950 §15.8 — Денежные и расчётные величины представляются фиксированной точкой; `float` для них запрещён; тип связывается полной import-строкой.
- L1953 §15.8 — Политика округления объявляется в `rules` и адресуется note; округление без политики — недоспецифицированное поведение.
- L1956 §15.8 — Распределение суммы по позициям объявляет судьбу остатка; сумма частей обязана равняться целому, правило закрепляется в `properties`.
- L1975 §15.9 — Блок данных является обычным provider-модулем; доступ к нему объявляется ребром `module_internal` наравне с любой зависимостью.
- L2040 §15.11 — Запрещены runtime-экземпляры и иллюстративные значения в любом блоке.
- L2044 §15.11 `Ф` — Запрещены inline-данные в notes: таблицы, пороги, allow-list, alias-словари, пути, ставки, коэффициенты.
- L2046 §15.11 `Ф` — Запрещены вычисляемые значения, шаблоны и внутриблочные ссылки.
- L2047 §15.11 — Запрещена позиционная идентификация строк табличных данных.
- L2048 §15.11 — Запрещён `float` для величин фиксированной точности.
- L2049 §15.11 — Запрещена нормализация `issued`-документов ссылками на изменяемые источники.
- L2050 §15.11 — Запрещена одношаговая несовместимая миграция.
- L2053 §15.11 — Запрещены compiler-generated codec/helper symbols, материализованные как проектные contracts, module_functions или notes.

### §— введение, чек-лист, пример

- L2090 §Чек-лист `Ф` — Runtime knobs лежат в config, domain schemas/catalogs в models, policy tables в rules; inline-данные не остаются в notes.
- L2094 §Чек-лист `Ф` — module_order корректен: зависимости раньше зависимых, `models` первый, `rules`/`config` доступны до ссылающихся модулей.
- L2102 §Чек-лист `Ф` — Типы замкнуты: каждое имя в type position — builtin, объявленная модель или символ с полной import-строкой; коллизий происхождения нет.
- L2104 §Чек-лист `Ф` — Каждый экспортируемый interface имеет полные method contracts; у discriminated_union — discriminator, закрытые variants и Literal-теги.
- L2111 §Чек-лист `Ф` — Каждый State 2 invariant имеет одного владельца и первичное представление в rules, classified note или properties; чистые функции отмечены в determinism.
- L2120 §Чек-лист — Каждое значение размещено процедурой 15.2: нет значений в notes прозой и значений без дома.
- L2126 §Чек-лист — Блоки канонизированы: сортированные ключи, строковая фиксированная точка, стабильные идентификаторы строк, нет вычисляемых значений.
- L2140 §Чек-лист — Значения, цитируемые в issued, имеют период действия; документ фиксирует момент расчёта.
- L2149 §Чек-лист `Ф` — `schema_version` присутствует в трёх блоках; несовместимое изменение сопровождается фазами expand/contract.

## Скилл: куда уходит каждый из 105 фрагментов

| корзина | фрагментов |
|---|---|
| проверяемое требование → гейт и подсказка в находке | 39 |
| вопрос на суждение → поле `questions` своей фазы | 26 |
| навигация → вывод `authoring.py next` | 19 |
| пересказ стандарта → ссылка на § | 12 |
| обоснование методики → вне обязательного чтения | 9 |

### Вопросы на суждение по фазам (всё, что остаётся от скилла как текст)

**state3_module_responsibilities** — 7 ⚠ больше пяти
- (362-367) Is each module justified by the knowledge and rules it owns rather than by a screen, endpoint or verb?
- (409-431) Do most public capabilities of this module rest on one hidden mechanism with one reason to change, or only share an entity name?
- (457-467) Does the candidate hold several state machines, transaction topologies, disjoint dependency sets or consumer subsets that mean it is several modules?
- (471-477) Do this module's public operations share one mechanism, invariants, dependencies and reason to change, or does it split along the mechanism?
- (490-497) Does any module own policy outside its role, merely forward arguments, or mirror an endpoint or entity instead of a mechanism?
- (503-504) Is the public API smaller than the hidden behaviour, and would any split trigger fire if this module were one file?
- (811-824) Does each module name state one ownership boundary, or does it only collect behaviour nobody else owns?

**state1_models** — 4
- (235-253) For each model: why does it exist, who creates, reads and modifies it, and where does every required field come from?
- (276-283) Is every field needed by a stated requirement, and are concepts that change for different reasons kept as separate models?
- (786-798) Is any dict, Any, metadata bag or shared status field standing in for a model structure not yet decided?
- (857-869) Is every interface, optional field and format branch required by a present product need rather than a future one?

**state2_rules_decisions** — 3
- (292-307) Which statements must always hold, and which values merely configure behaviour; is each recorded as an accepted decision?
- (355-359) Does each invariant name one future owning responsibility, and is every lifecycle-relevant state transition written explicitly?
- (799-810) Is every policy a declared rule, config value, ordering or recorded open question rather than prose like 'best' or 'reasonable'?

**state4_reviewed_flows** — 3
- (529-538) At each flow transition, are the crossing model, next decision owner, adapter, error translator and cleanup duty named?
- (541-548) Does every major flow end in an observable result or explicit failure produced by a named module, with no logic hidden in endpoints?
- (851-856) For every promised state, artifact or result in this flow, which single component produces it?

**state7_notes** — 3
- (689-694) Could this function be implemented as return None, an empty value, a constant or plain forwarding without contradicting its notes?
- (695-701) Are this function's observable outcome, output field sources, failure behaviour, side effects and forbidden shortcuts all stated in its notes?
- (838-850) Does each MUST note name a specific condition, outcome, assignment or boundary that a stub implementation would violate?

**state0_product_frame** — 2
- (223-229) Does every primary action have an observable outcome and known failure outcome, with unknowns written as open questions rather than abstractions?
- (774-785) Does every product promise name a concrete user action, its observable output and its failure?

**state6_exact_contracts** — 2
- (645-650) Does every argument have a clear source, every return value a consumer, and every function exactly one owning module?
- (825-837) Does any signature keep uncertainty through dict, Any, object, or optional parameters added only for hypothetical reuse?

**state2_to_state3_trace** — 1
- (78-79) Is every ownership or relation claim backed by a normative source you read, not by a shared name or --mentions hit?

**state5_public_module_operations** — 1
- (564-572) Does each public operation serve a real cross-module need, hide internal sequencing, and return an output concrete enough to forbid empty results?

