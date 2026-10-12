# Задание: повторно закрыть Stage 7 Cabinet Kernel (локальный запуск)

Подготовлено 2026-10-12. Запускать на компьютере, где установлен Codex CLI и
выполнен `codex login`. Всё выполняется локально; GitHub Actions и секреты
GitHub не нужны.

## Зачем

После слияния Factory PR #82 (`6936362`) и Workbench PR #115 (`18d7287`)
промпт ревью State 7 стал совпадать с боевым промптом Factory. Поэтому все
14 LLM-модулей Cabinet Kernel переоткрылись, и FA019 стоит в BLOCK. Нужно
снова провести раунды «Почемучки» в режиме contradictions, пока каждый модуль
не закроется.

## Подготовка

```bash
# 1. Оба репозитория — актуальный main
cd <путь>/code-factory   && git switch main && git pull --ff-only
cd <путь>/spec-workbench && git switch main && git pull --ff-only

# 2. Ветка проекта с инструментами из main (merge, без rebase и force-push)
git switch agent/cabinet-kernel
git pull --ff-only
git merge origin/main

# 3. Проверки перед раундами
export SPEC_WORKBENCH_FACTORY_ROOT=<путь>/code-factory
codex login status
python tools/design_spec_projection.py examples/cabinet-kernel --verify   # ready: true, in_sync: true
python tools/design_questions.py status examples/cabinet-kernel --state 7
```

Ожидаемый статус: `closed=false`, открыты все 14 модулей: canonical_values,
sandbox_runner, store, installation, sandbox, service_invoker, run_values,
functions, bindings, flows, effects, run_graph, runs, surface.

## Раунд

```bash
python tools/design_questions.py ask examples/cabinet-kernel --state 7 \
  --since b3bee2e0a8386635c5018bed065c2aa19fda80ab --provider codex
python tools/design_questions.py status examples/cabinet-kernel --state 7
```

После каждого раунда закоммитить только его файлы и запушить:

```bash
git add examples/cabinet-kernel/questions/state7
git commit -m "cabinet-kernel: State 7 round <N> (codex-cli)"
git push origin agent/cabinet-kernel
```

Повторять, пока `status` не покажет `closed=true`. Модуль закрывается, когда
два последних раунда подряд для него чистые на одном и том же тексте промпта.

## Когда остановиться

- **`closed=true`** — готово. Проверить:
  ```bash
  python tools/authoring.py next cabinet-kernel --json
  ```
  State 7 больше не должен быть блокирующим шагом.
- **Судья нашёл `contradiction`** — ничего не исправлять. Остановиться и
  передать номер раунда, модуль и обе цитаты из `summary.json` этого раунда.
- **10 раундов без закрытия** или ошибка `codex exec` — остановиться и
  передать вывод `status`.

## Нельзя

- Менять `SPEC_STANDARD.md`, модели, контракты, notes и любые другие файлы
  проекта, кроме `examples/cabinet-kernel/questions/`.
- Обходить гейты или редактировать результаты раундов вручную.
- Генерировать продуктовый код.
- Копировать `~/.codex/auth.json` куда-либо, в том числе в репозиторий и
  секреты GitHub.

## Что прислать в ответ

- Статус каждого из 14 модулей и число проведённых раундов.
- Найденные противоречия, если есть (модуль, раунд, цитаты).
- Итог `status --state 7` и `authoring.py next`.
- SHA последнего коммита в `agent/cabinet-kernel`.

## Важно

Раунды через Codex ведутся не той моделью, которой Factory генерирует код. Перед
генерацией State 7 по правилам (`skills/spec-authoring/QUESTIONS.md`) нужно
закрыть ещё раз моделью генератора через API-ключ OpenAI. Этот запуск —
подготовка, а не финальное закрытие.
