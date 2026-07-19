# STANDARD_DELTA 002 — properties, determinism и трассировка инвариантов

Статус: **внедрено 2026-07-18 по результатам ревью методологии**.

## Проблема

State 2 добывал data invariants, transitions и ownership, а State 7 вручную
задавал placeholder-вопрос. Между ними и уже существующим Factory property
слоем не было машинно-проверяемого перехода. Инвариант мог раствориться в
notes, не попасть в `properties`, либо вообще потеряться.

## Решение

1. `SPEC_STANDARD.md` нормирует существующие секции `properties` и
   `determinism`, включая замкнутое подмножество выражений над `result`,
   аргументами и `self`.
2. State 2 заводит Workbench-sidecar `invariant_ledger.json` со стабильным id,
   формулировкой, будущим function owner и landing.
3. State 7 обязан выбрать одно первичное приземление: `rules`, classified
   `note` или `properties.<function>`, и отдельно принять решение о
   `determinism`.
4. `semantic_lint.py --invariants ...` выдаёт S10, если owner или landing не
   разрешается в собранной спецификации.

Ledger не является частью `global_spec.json` и не передаётся фабрике. Он
проверяет авторский процесс; финальная спека остаётся единственным входом
Factory.

## Формат ledger v1

```json
{
  "schema_version": 1,
  "invariants": [
    {
      "id": "INV-001",
      "statement": "a completed job has a result id",
      "owner_function": "complete_job",
      "landing": {
        "kind": "property",
        "expression": "result.status != 'completed' or result.result_id is not None"
      }
    }
  ]
}
```

Формы landing:

- `{"kind": "rules", "path": "job_status_transitions"}` — path разрешается
  относительно корня `rules`;
- `{"kind": "note", "text": "..."}` — точная classified note с префиксом
  `owner_function`;
- `{"kind": "property", "expression": "..."}` — точное выражение в
  `properties.<owner_function>`.

Точное значение, а не индекс массива, сохраняет трассировку при перестановке
notes/properties. До State 7 `owner_function` и `landing` могут быть `null`, но
strict semantic lint перед export обязан закрыть оба поля.

## Граница изменений

Нормализатор и export pipeline не меняются: `properties` и `determinism` уже
проходят через Factory. Изменение ограничено стандартом, authoring workflow и
advisory semantic lint.
