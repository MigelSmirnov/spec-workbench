# Registry State 2 — расследование решения со свидетелями и песочницей

Эксперимент на кластере аудита Registry: A14, A15 и правила A01/A03/A04/A05/A13,
на которые они опираются, вместе с R0-37, R0-58, R0-66, R0-89 и M09.
Канонические решения проекта и общая методика не менялись: всё лежит в этом
каталоге.

Итоги — в [`REPORT.md`](REPORT.md).

## Исходные версии

- Каноническая ветка по `PROJECT_INDEX.json`: `agent/registry`, каталог
  `examples/registry`; на момент эксперимента
  `cf675e5c9d284b7578740d5b074843da066d0d4b`, State 2 закрыт раундом 34.
- Общие инструменты: `main` = `22d05dbf0394d8c0974ba65c42db8168a75b9fb6`;
  `tools/` и `skills/` на `agent/registry` совпадают с ним.
  `tools/questions_workbench` последний раз менялся в `736d1aca`.
- Девять исторических версий текста и одна сконструированная (H1)
  перечислены в `model/sources.py` (`VERSIONS`). Соответствие версий
  раундам — в `results/rounds.md`.

## Как воспроизвести

Из корня репозитория, на этой ветке (нужен Python 3.11+ и git-история
`agent/registry`):

```bash
python experiments/registry-state2-investigation/check_quotes.py   # 71 цитата на своих коммитах
python experiments/registry-state2-investigation/provenance.py     # раунды -> версии текста
python experiments/registry-state2-investigation/run.py            # свидетели и перебор, глубина 6, ~95 с
python experiments/registry-state2-investigation/make_bundle.py    # пакет + цитаты для чтения без репозитория
```

`run.py` детерминирован: на том же коммите получаются те же файлы в
`results/`.

## Состав

| путь | что это |
|---|---|
| `packet/PACKET_empty_erasure.md` | часть 1: пакет расследования одного решения |
| `packet/BUNDLE.md` | тот же пакет с дословными цитатами (собирается) |
| `witnesses/witnesses.json` | часть 2: 17 свидетелей с основаниями и статусом |
| `model/sandbox.py` | часть 3: модель — движок проверок и предикаты норм |
| `model/sources.py` | версии текста и закреплённые цитаты |
| `model/TRACEABILITY.md` | соответствие нормы и элемента модели, с объяснением перевода |
| `run.py`, `results/witnesses.*`, `results/exploration.*` | прогоны свидетелей и ограниченный перебор |
| `provenance.py`, `results/rounds.md`, `results/provenance.json` | какой текст читал каждый раунд и темы кластера в нём |
| `route/ROUTE_CHECK.md` | часть 4: маршрут на настоящих замечаниях |
| `route/model_run/` | точная инструкция и ответ модельного прогона по пакету |
