# Индекс SPEC_STANDARD

Короткая навигация по [SPEC_STANDARD.md](SPEC_STANDARD.md) для точечных правок
`global_spec.json`. Нормативным источником остаётся полный стандарт.

## Основы

| Раздел | Когда открывать |
| --- | --- |
| [Зачем](SPEC_STANDARD.md#зачем) | Нужно понять роль спецификации в normalizer, builder и code generation. |
| [Структура файла](SPEC_STANDARD.md#структура-файла) | Нужно проверить обязательные верхнеуровневые секции. |
| [Архитектура создаваемого кода](SPEC_STANDARD.md#архитектура-создаваемого-кода) | Меняются границы модулей, публичные API или generation units. |

## Секции `global_spec.json`

| Секция | Что она определяет | Когда править |
| --- | --- | --- |
| [`contracts`](SPEC_STANDARD.md#1-contracts) | Точные Python-сигнатуры функций и методов. | Меняются аргументы, возвращаемые типы или публичный контракт. |
| [`notes`](SPEC_STANDARD.md#2-notes) | Классифицированные требования к поведению. | Уточняются проверки, ошибки, side effects, provenance, ordering или запреты. |
| [`adapters`](SPEC_STANDARD.md#3-adapters) | Преобразование данных между caller и callee. | Формы аргументов на границе модулей не совпадают. |
| [`config`](SPEC_STANDARD.md#4-config) | Runtime- и product-настройки. | Меняются лимиты, пути, TTL, timeouts или feature knobs. |
| [`models`](SPEC_STANDARD.md#5-models) | DTO, dataclass/Pydantic-схемы и доменные каталоги. | Меняются сущности, поля, типы, defaults или domain taxonomy. |
| [`rules`](SPEC_STANDARD.md#6-rules) | Read-only domain/policy semantics. | Меняются нормативные таблицы, routing, fallback или threshold policy. |
| [`imports`](SPEC_STANDARD.md#7-imports) | Стандартные, внешние и публичные внутренние импорты. | Добавляется зависимость или меняется экспортируемая поверхность модуля. |
| [`module_functions`](SPEC_STANDARD.md#8-module_functions) | Владение всеми функциями, классами и константами. | Символ создаётся, перемещается или меняет модуль-владелец. |
| [`module_order` и `function_order`](SPEC_STANDARD.md#9-module_order-и-function_order) | Порядок генерации модулей и функций. | Меняются зависимости или порядок сборки. |
| [`module_hints`](SPEC_STANDARD.md#10-module_hints) | Подсказки для привязки неоднозначных notes. | Module-level note попадает не в тот модуль. |
| [`module_paths`](SPEC_STANDARD.md#11-module_paths) | Пути генерируемых Python-модулей. | Меняется файловая или package-структура. |
| [`default_module`](SPEC_STANDARD.md#12-default_module) | Получатель непривязанных функций и notes. | Меняется fallback-модуль или появляются непривязанные символы. |
| [Система типов](SPEC_STANDARD.md#13-система-типов-и-происхождение-имён) | Замыкание имён, происхождение типов, нормативный NOT-list. | Появляется новый тип, import типа или ошибка «unknown/ambiguous name». |

## Детали `models`

- [kind моделей — закрытый реестр](SPEC_STANDARD.md#kind-моделей)
- [kind: discriminated_union](SPEC_STANDARD.md#kind-discriminated_union)
- [kind: interface](SPEC_STANDARD.md#kind-interface)

## Детали `notes`

- [Обязательный префикс](SPEC_STANDARD.md#обязательный-префикс)
- [Module-level notes](SPEC_STANDARD.md#модуль-level-notes)
- [Реестр классов notes](SPEC_STANDARD.md#реестр-классов-notes)
- [Что включать в notes](SPEC_STANDARD.md#что-включать-в-notes)

## Финальная проверка

- [Чек-лист перед запуском сборки](SPEC_STANDARD.md#чек-лист-перед-запуском-сборки)
- [Пример минимальной спеки](SPEC_STANDARD.md#пример-минимальной-спеки-для-нового-проекта)

## Маршрутизация типичных изменений

```text
новая сущность или поле       → models → contracts → notes
тип «ровно одно из»           → models (kind: discriminated_union) → variants
новый порт (repo/UoW/gateway) → models (kind: interface) → contracts (Имя.метод)
новый stdlib/third-party тип  → imports (полная строка) → раздел 13
новый инвариант или policy    → rules → владеющий модуль → notes
новая runtime-настройка       → config → notes
изменение публичной границы   → imports.internal → contracts → module_functions
перемещение реализации        → module_functions → module_order → module_paths
несовпадение форматов вызова  → adapters
неоднозначная привязка note   → module_hints
```
