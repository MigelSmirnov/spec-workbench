# Проектирование `http_router_backend/v1`

Это операционное руководство дополняет нормативный
[`SPEC_STANDARD.md`, раздел 6.1](SPEC_STANDARD.md#61-http_router_backendv1).
При расхождении действует `SPEC_STANDARD.md`; этот документ объясняет порядок
проектирования и проверки IR, но не расширяет его язык.

## 1. Когда проектировать router IR

Router IR проектируется **после** того, как подтверждены ключевые системные
потоки (State 4), публичные операции модулей (State 5) и их точные контракты
(State 6). Маршрут не является источником Python API:

```text
reviewed flow
  -> owning module and public operation
  -> contracts[handler/function]
  -> rules.http_router_backend route/wiring
  -> deterministic emitter
```

Не начинай с перечня URL и не восстанавливай сигнатуры из legacy-router.
Legacy-код допустим как evidence для инвентаризации, но решения должны быть
закреплены в моделях, ownership, contracts, imports и IR.

## 2. Разделение ответственности

| Объект | Владелец в спецификации | Что он определяет |
|---|---|---|
| Символ и Python-сигнатура | `module_functions`, `contracts` | Имя, модуль и canonical contract |
| HTTP-экспонирование | `rules.http_router_backend.routes` | method, path, auth, status, lowering |
| Тело table-handler-а | backend/emitter | Детерминированное thin orchestration |

Router-модуль является обычным физическим модулем спецификации: его символы
объявлены в `module_functions`, а placement и ordering следуют обычным правилам
`module_paths` и `module_order`. При этом тела его
table-handler-ов, app factory, extractors и generated projections принадлежат
backend-у. Ownership символа и ownership его детерминированной реализации —
разные вещи.

`imports.module_internal[router]` остаётся обычным минимальным графом прямых
runtime-imports. Он не является списком endpoint-ов и не даёт разрешения
«экспортировать всё». Единственный каталог HTTP-экспонирования — `routes`.

## 3. Порядок проектирования

### Шаг 1. Зафиксировать операции и контракты

Для каждого будущего endpoint сначала определи owning operation и точный
контракт. Затем объяви контракт handler-а в его owning router- или
companion-модуле. Route row не содержит `signature` и не повторяет типы.

Версия 1 принимает только позиционные и positional-or-keyword параметры:
variadic (`*args`, `**kwargs`) и keyword-only параметры не допускаются.

### Шаг 2. Объявить backend и wiring

Заполни `backend`, затем:

- `wiring.module` — логический ключ router-модуля;
- `app_factory` — функция этого модуля с контрактом;
- `request_parameter` — имя параметра request во всех table-handler-ах;
- `state_bindings` — непустое отображение slot → параметр app factory →
  атрибут app state;
- `credential_extractors` — именованные transport extractors.

В v1 extractor имеет только `kind: "header_scheme"`; его функция принадлежит
router-модулю, принимает ровно один позиционный параметр и ссылается на
exception из `error_policy`.

### Шаг 3. Описать principals и auth policies

Principal содержит resolver и typed arguments. Auth policy только выбирает
объявленный principal или `null`. Не помещай в auth policy продуктовые guards:
проверки capability/ownership выражаются вызовами `authorize`, а сама политика
остаётся в security/domain owner.

### Шаг 4. Описать projections

Projection объявляет функцию и список записей
`{"field": <target>, "value": <typed ref>}`. Return type её canonical
контракта должен быть record model, а `fields` должны покрывать модель ровно:
без пропусков, повторов и лишних полей.

### Шаг 5. Заполнить route catalog

| `emission` | Когда использовать | Где живёт handler |
|---|---|---|
| `table` | Поток выражается typed refs, authorize/delegate/projection | router-модуль |
| `irregular` | В v1 нет достаточного lowering, но контракт и причина ясны | ровно `irregular_ownership.module` |

`irregular` — не лазейка для скрытой бизнес-логики и не свободный Python-код в
IR. Он содержит только общие route-поля и `irregular_reason`; реализация
принадлежит companion-модулю.

Для `table` укажи `authorize`, `delegate`, `projection` и `returns`.
Каждый authorization step содержит boolean `binds`; значение `true` может один
раз связать slot `context` для следующих вызовов.
Допустимые сочетания:

- `returns: "delegate"` — обычный результат delegate;
- `returns: "projection"` — route вызывает projection;
- `returns: "none"` — только вместе с `response_mode: "none"`;
- `response_mode: "binary"` — требует projection call.

### Шаг 6. Выбрать typed refs

Аргумент каждого вызова — закрытый объект DSL:

| Источник значения | Форма |
|---|---|
| Доступный slot: app state или backend-bound `actor`/`context`/`result` | `{"ref":"slot","name":"store"}` |
| Credential extractor | `{"ref":"credential","name":"bearer"}` |
| Handler parameter/поле модели | `{"ref":"parameter","path":["payload","email"]}` |
| Enum member | `{"ref":"enum","type":"Capability","member":"INVOICE_READ"}` |
| JSON scalar или `null` | `{"ref":"literal","value":true}` |

Строки `"payload.email"`, `"store"` и `"Capability.INVOICE_READ"` запрещены:
это скрытый Python-код без типизированного происхождения.

### Шаг 7. Закрыть error policy

`error_policy` задаёт `body: "empty"`, default status, непустой список записей
`{"exception": ..., "status": ...}` и `unavailable_to_module`. Доступные
исключения должны быть прямыми imports router-модуля; недоступные входят и в mapping, и в
`unavailable_to_module`. В v1 status находится в диапазоне 400–599.

### Шаг 8. Проверить ссылки и уникальность

Перед генерацией проверь:

- каждый handler/function имеет ровно один owner и canonical contract;
- path-параметры существуют в контракте handler-а;
- parameter paths проходят через объявленные model fields;
- call arity совпадает с контрактом целевой функции;
- slots, credentials, principals, policies, projections и enums объявлены;
- handler и пара `(method, path)` уникальны;
- `module_internal[router]` содержит только реально необходимые прямые imports;
- table и irregular handlers принадлежат требуемым модулям.

## 4. Минимальный связный пример

Контракты и module ownership объявляются в обычных разделах спецификации и
намеренно не дублируются в route row.

```json
{
  "kind": "http_router_backend",
  "schema_version": 1,
  "backend": {"framework": "fastapi", "emitter": "fastapi_sync_v1"},
  "wiring": {
    "module": "api",
    "app_factory": "create_app",
    "request_parameter": "request",
    "state_bindings": {
      "store": {"factory_parameter": "store", "state_attribute": "store"}
    },
    "credential_extractors": {}
  },
  "principals": {},
  "auth_policies": {"public": {"principal": null}},
  "projections": [],
  "routes": [
    {
      "handler": "get_invoice",
      "method": "GET",
      "path": "/invoices/{invoice_id}",
      "auth": "public",
      "success_status": 200,
      "response_mode": "json",
      "emission": "table",
      "authorize": [],
      "delegate": {
        "function": "load_invoice",
        "args": [
          {"ref": "slot", "name": "store"},
          {"ref": "parameter", "path": ["invoice_id"]}
        ]
      },
      "projection": null,
      "returns": "delegate"
    }
  ],
  "error_policy": {
    "body": "empty",
    "default_status": 500,
    "mapping": [{"exception": "InvoiceNotFound", "status": 404}],
    "unavailable_to_module": []
  },
  "irregular_ownership": {"module": "api_irregular"}
}
```

## 5. Миграция существующего router

Для legacy-приложения:

1. инвентаризируй все `(method, path, handler)` и раздели table/irregular;
2. восстанови owning operations, models и contracts вне route rows;
3. замени Python-like args на typed refs;
4. вынеси все project-specific имена в IR;
5. проверь, что весь существующий каталог выражается одной схемой без
   специальных констант backend-а;
6. только после эквивалентной deterministic emission считай миграцию закрытой.

Если IR отсутствует, проект может идти обычным LLM-маршрутом. Если IR
присутствует, но невалиден, это `DEFECT`: удалять его или молча переключаться на
LLM нельзя.

## 6. Нормативный NOT-list

В `http_router_backend/v1` запрещено:

- повторять `signature`, типы моделей или поля projection в route row;
- помещать Python expressions, imports, lambdas или call syntax в args;
- прошивать project-specific capabilities, slots, state attributes или имя
  companion-модуля в backend;
- делать router владельцем guards, persistence или продуктовой политики;
- считать `imports.internal` или `module_internal` автоматическим каталогом
  endpoint-ов;
- использовать `irregular` вместо проектирования отсутствующего DSL без
  явной причины и ownership;
- генерировать по частично валидному IR.

После изменения спецификации запускай её штатную валидацию и inspector, затем
используй только официальный deterministic Route B Factory. Прямой вызов
внутреннего emitter-а не является пользовательским workflow.
