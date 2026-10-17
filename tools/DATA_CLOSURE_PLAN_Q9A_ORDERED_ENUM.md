# План Q9-a — упорядоченный enum в Workbench и Factory

## Статус

План согласованного изменения двух репозиториев. Код, стандарт и рабочие
спецификации не менялись, PR в `code-factory` не открывался.

**Основа:**

- spike `tools/DATA_CLOSURE_SPIKE_Q9A_ORDERED_ENUM.md`;
- Workbench `origin/main` @ `9cde0aa`;
- Factory `main` @ `391c41c`;
- Cabinet Kernel `origin/agent/cabinet-kernel` @ `b3bee2e`.

Все ссылки `файл:строка` даны по этим ревизиям.

### Утверждённый контракт

| № | Правило |
|---|---|
| K1 | `ordered` допускается только как `ordered: true` или отсутствует. `ordered: false` и любые другие значения запрещены. |
| K2 | Первый элемент `values` — минимальный, последний — максимальный. |
| K3 | Factory генерирует `rank(self) -> int`. |
| K4 | Семантика сравнения `StrEnum` не меняется. |
| K5 | `values` — единственный источник порядка. |
| K6 | Старая Factory обязана отказать, а не проигнорировать атрибут. |
| K7 | Промпт Factory и review Stage 7 используют согласованное представление моделей. |

---

## 1. Решение по `standard_version` и fail-closed

### 1.1 Что проверено

1. **Старая Factory молча принимает неизвестный ключ верхнего уровня.**
   Эксперимент: `validate_spec.validate` с ключом
   `required_factory_features` не даёт ни одной ошибки. Механизм «список
   требуемых возможностей» отказа не обеспечит.
2. **`standard_version: 3` старая Factory отвергает.** Тот же эксперимент:
   `error … unsupported_standard_version`, `tools/validate_spec.py:158–164`.
3. **Неизвестный ключ модели (`ordered`) старая Factory игнорирует везде**
   (spike, §3). Отказ даёт только неизвестный `kind`, но контракт сохраняет
   `kind: enum`.
4. **Равенство `standard_version == 2` зашито в Factory во многих местах.**
   Их нужно перевести на одну константу допустимых версий:

   | Файл | Строки |
   |---|---|
   | `tools/validate_spec.py` | `:158–164` |
   | `tools/bootstrap_project.py` | `:65`, `:96–98` |
   | `tools/build_local_spec.py` | `:1141–1143` |
   | `tools/data_code_seam.py` | `:129`, `:157`, `:165`, `:226`, `:264` |
   | `tools/draft_static_gates.py` | `:3122` |
   | `run_generate.py` | `:363–370` |
   | `rebuild_module.py` | `:1528`, `:1544` |
   | `experimental/factory_mcp/factory_state.py` | `:235–276` |
   | `factory_control/otk_audit.py` | `:876–884` |
   | `verification/handoff_manifest.py` | `:359–383` |

5. **Workbench сейчас допускает только версию 2.**
   - `tools/spec_language_workbench/__init__.py:7` —
     `SUPPORTED_STANDARD_VERSION = 2`, проверка `:33–46`, через неё `FA009`
     (`tools/factory_admission_workbench/service.py:627`).
   - `tools/migrate_spec_v2.py:25, 44–47, 72–73` — миграция только в v2.
6. **`FA004` требует побайтно одинаковый стандарт в обоих репозиториях**
   (`factory_admission_workbench/service.py:601–626`). Сейчас копии
   действительно одинаковы.

### 1.2 Решение

**`standard_version: 3` = v2 + `ordered: true` у `kind: enum`.**
Других изменений в v3 нет.

| Комбинация | Старая Factory | Новая Factory | Старый Workbench | Новый Workbench |
|---|---|---|---|---|
| v2 без `ordered` | принимает | принимает, побайтно тот же путь | принимает | принимает |
| v2 с `ordered` | **молча игнорирует** (сегодняшний риск) | **отказ** `ordered_requires_standard_version_3` | пропускает | **отказ** (тот же код) |
| v3 с `ordered` | **отказ** `unsupported_standard_version` | принимает | **отказ** `FA009` | принимает, если целевая Factory поддерживает v3 |
| v3 без `ordered` | отказ | принимает | отказ | принимает |

Почему так:

- v3 — единственная форма, которую старая Factory гарантированно
  отвергает (K6).
- v2 остаётся полностью рабочей, поэтому периода несовместимости для
  существующих проектов нет.
- `ordered` в v2-спеке новая Factory отвергает. Это закрывает сегодняшний
  путь «атрибут есть, но молча проигнорирован».

**Lineage.** Сейчас все переходы lineage обязаны записывать версию 2
(`handoff_manifest.py:373–374`, `otk_audit.py:884`). Новое правило: все
переходы одной спеки записывают **одну и ту же** допустимую версию. Переход
v2 → v3 у проекта — это новая принятая спека, а не смешанный lineage.

---

## 2. Порядок изменений без периода несовместимости

| Шаг | Репозиторий | Что сливается | Эффект для существующих v2-проектов | Можно ли откатить |
|---|---|---|---|---|
| **A** | Factory | Код: допустимые версии `{2, 3}`; валидация enum (§3.1); эмиссия с `rank()` и `values` как единственным источником порядка; строка `ordered` в промпте **только** для упорядоченных enum; тесты. Текст стандарта **не** меняется. | Нет: v2 без `ordered` даёт побайтно те же normalize, срезы, `models.py` и промпты (условие S3, §6) | Да, отдельный revert |
| **B** | Workbench | Код:<br>• `spec_language_workbench` допускает `{2, 3}`;<br>• валидация model closure по правилам A;<br>• новая проверка Stage 9 «целевая Factory поддерживает v3» (только для v3-спек);<br>• выравнивание review-промпта (§7);<br>• правило `data_closure` M-E3. | Нет. Единственный эффект — State 7 contradictions один раз переоткроют единицы, потому что review-промпт стал боевым (§7). | Да |
| **C** | Оба | Пара коммитов `SPEC_STANDARD.md` (§0 версия 3, §5 `ordered`) с **одинаковыми байтами**, сливаются подряд, Factory первым | Между двумя слияниями `FA004` блокирует Stage 9 всем проектам. Это fail-closed, без неверного поведения, на минуты. | Да, парой |
| **D** | Workbench, ветка `agent/cabinet-kernel` | Миграция Cabinet Kernel на v3 (§4) | Затрагивает только Cabinet Kernel | Да, revert ветки проекта |

Почему порядок именно такой:

- **A раньше B.** Workbench не может допустить v3, пока целевая Factory не
  умеет её обрабатывать. Проверка B на Stage 9 читает возможность у
  конкретного checkout Factory.
- **B раньше C.** Иначе стандарт обещает форму, которую инструменты
  Workbench ещё отвергают.
- **D последним.** Только после того как всё остальное на `main` обоих
  репозиториев.

Между A и D v3-спеки нет ни у одного проекта, поэтому новая ветка кода
неактивна. Ни в один момент v3-спека не может попасть в Factory, которая её
не понимает:

- старая Factory отвергает v3 сама;
- Workbench отвергает v3 до шага B и проверяет целевую Factory после него.

---

## 3. Файлы и функции

### 3.1 Factory (шаг A)

| Файл | Функция или место | Изменение |
|---|---|---|
| Новый `tools/spec_version.py` (или константа в `validate_spec.py`) | `SUPPORTED_STANDARD_VERSIONS = frozenset({2, 3})`, `ORDERED_ENUM_MIN_VERSION = 3` | Один источник допустимых версий |
| `tools/validate_spec.py` | `_check_standard_version` (`:158–170`) | Принимать `{2, 3}`. Запрет `adapters` остаётся для обеих версий. |
| `tools/type_resolver.py` | Новая `check_enum_declarations(spec)` рядом с `check_model_kinds` (`:374–387`), вызов из `validate_spec_types` (`:537`) | Отказы (коды в §5.1):<br>• `ordered` не `True` (в том числе `false`, `"yes"`, `1`, `null`);<br>• `ordered` у модели без `kind: enum`;<br>• `ordered` при `standard_version` 2;<br>• пустые `values`, не-строки, дубликаты в `values` любого enum;<br>• при `ordered`: `members` или `member_names` в форме словаря. Список `member_names` допустим: он сопоставляется с `values` позиционно (`generate_models_draft.py:237–240`). |
| `tools/validate_spec.py` | `_check_models` (`:843–888`) | Вызвать ту же `check_enum_declarations`. Канонический валидатор и `type_resolver` не должны расходиться. |
| `tools/generate_models_draft.py` | `emit_enum` (`:276–303`) | Для `ordered` порядок — только `values`. Добавить метод `rank(self) -> int` (§3.3). |
| `tools/generate_models_draft.py` | `runtime_members_for_spec` (`:250–264`) | Переиспользовать имена членов из старого `models.py` только при **совпадении последовательности** значений, а не множества. Это нужно для K5 на всех enum: сейчас перестановка теряется (spike, 9e). |
| `tools/generate_models_draft.py` | `enum_member_names` (`:144–154`), `uppercase_enum_member_name` (`:127–141`) | Дубликат значения — `ValueError`, а не алиас `_2`. Валидатор ловит раньше, эмиттер страхует. |
| `tools/generate_models_draft.py` | `structured_enum_members` (`:232–247`) | При `ordered` формы `members` и `member_names`-словарь недостижимы (отвергнуты валидатором). Для страховки — `ValueError`. |
| `tools/generate_agent.py` | `build_runtime_model_surface_block` (`:422–466`) | Для `ordered` enum в **обоих** путях (`:440–443` и `:464–466`) выводить одну и ту же строку: члены в порядке `values` и пометку «ordered, lowest → highest; compare with `.rank()`, never with `<`, `max`, `min` or `sorted` on members». Для неупорядоченных enum не менять ничего: v2-промпты остаются побайтно прежними. |
| `tools/generate_agent.py` | `_parse_runtime_model_surface` (`:343–383`) | Без изменений. Если строку ordered строить из спеки, порядок членов из кода не нужен. |
| `tools/draft_static_gates.py` | Новый gate рядом с проверкой версии (`:3122`) | Рекомендуется: в коде LLM-модуля сравнение членов упорядоченного enum через `<`, `>`, `max`, `min`, `sorted` без `key=…rank` — BLOCK. |
| Гейты версии (§1.1, п. 4) | Все места | Заменить `== 2` / `!= 2` на принадлежность константе. Для lineage — «все переходы одной версии». |
| `tools/bootstrap_project.py` | `:65` | Новый проект по-прежнему создаётся в v2. v3 — осознанный переход. |
| `patch_ops.py` | `_op_set_standard_version` (`:169`) | Принимать 3. Это путь миграции проекта, если он идёт через Factory. |
| `SPEC_STANDARD.md` | — | Только на шаге C, в паре с Workbench |

### 3.2 Workbench (шаг B)

| Файл | Функция или место | Изменение |
|---|---|---|
| `tools/spec_language_workbench/__init__.py` | `SUPPORTED_STANDARD_VERSION` (`:7`), проверка `:33–46` | Допускать `{2, 3}`; в отчёте — `supported_standard_versions` |
| Новый `tools/model_closure_validation.py` (или функция в `spec_projection_workbench/service.py`) | Вызов из `_project` (`spec_projection_workbench/service.py:396–405`) | Те же правила, что `check_enum_declarations` в Factory, с теми же кодами. Плюс: `ordered` в closure при `standard_version` 2 в `global_spec.json` — BLOCK `ordered_requires_standard_version_3`. Сейчас проекция копирует N1–N3 дословно (spike, §4.5). |
| `tools/factory_admission_workbench/service.py` | Новая проверка `FA020` рядом с `_factory_toolchain_check` (`:1027`) | Для v3-спеки: целевая Factory объявляет поддержку v3. Источник — константа `SUPPORTED_STANDARD_VERSIONS` из нового модуля Factory, читается тем же способом, каким `_standard_check` читает файлы. Нет константы — BLOCK. Для v2 — `NOT_APPLICABLE`. |
| `tools/factory_admission_workbench/service.py` | `_language_check` (`:627–650`), lineage (`:944–970`) | Принимать v3; lineage — одна версия на всех переходах |
| `tools/factory_slice_workbench/service.py` | `_PROMPTS_SCRIPT` (`:213–232`), `module_prompts` (`:239–280`) | Строить промпт так же, как боевой `generate_agent`: срез `models` → `generate_models_code` Factory во временном каталоге → `build_prompt(local_spec, models_code)` (§7) |
| `tools/questions_workbench` | — | Без изменений кода. После шага B дайджесты всех единиц State 7 изменятся один раз (§7.3). |
| `tools/migrate_spec_v2.py` | — | Без изменений: миграция в v2 остаётся миграцией в v2 |
| `tools/model_surface_workbench/index.py` | `:86–87` | Без изменений: `ordered` на поверхность имён не влияет |
| `data_closure` (будущая реализация) | Правило M-E3 (`DATA_CLOSURE_RESEARCH_Q9_Q10_Q11.md`, §5.1) | Note, опирающаяся на порядок enum, законна только при `ordered: true`. Пересказ порядка рядом с адресом — `duplicated_data`. |
| `skills/spec-authoring/SPEC_STANDARD.md` | — | Только на шаге C, байты те же, что в Factory |

### 3.3 Форма `rank()` в эмиссии

Пример для `DisclosureClass`, текущая эмиссия плюс метод:

```python
class DisclosureClass(StrEnum):
    open = 'open'
    OPEN = 'open'
    business_confidential = 'business_confidential'
    BUSINESS_CONFIDENTIAL = 'business_confidential'
    personal_data = 'personal_data'
    PERSONAL_DATA = 'personal_data'

    def rank(self) -> int:
        return tuple(type(self)).index(self)
```

- Итерация `StrEnum` не включает алиасы, поэтому `rank()` равен позиции в
  `values` (spike, §4.6).
- `__lt__` не переопределяется: строковая семантика сохраняется (K4).
- `rank` — имя, генерируемое эмиттером, а не проектный символ. Оно не
  добавляется в `contracts`, `module_functions` или notes (по аналогии с
  §15.5.1 о helper-ах backend-а). Промпт сообщает о нём строкой ordered.
- **Ограничение:** член enum с именем `rank` конфликтовал бы с методом.
  Валидатор отвергает значение `rank` у упорядоченного enum (код
  `ordered_enum_reserved_member`). В Cabinet Kernel такого значения нет.

---

## 4. Миграция Cabinet Kernel (шаг D, ветка `agent/cabinet-kernel`)

### 4.1 Какие enum упорядочены

State 1 Cabinet Kernel прямо называет упорядоченные множества —
`01_models.md:22–24`: «A set named here as ordered — disclosure classes
(M01), effect classes (M10) — is ordered by the declared order of its
enumeration, and its members are compared only by that position, never as
text». Это и есть K2 + K3 + K4.

| Enum | Источник в State 1 | `values` в `global_spec.json` | Совпадает с «lowest → highest»? |
|---|---|---|---|
| `DisclosureClass` | `01_models.md:52–53` (M01) | `open, business_confidential, personal_data` | да |
| `EffectClass` | `01_models.md:473` (M10, K-08) | `read, draft-write, state-transition, external-effect, destructive` | да |

`values` переставлять не нужно. Остальные 31 enum упорядоченными не
объявлены.

### 4.2 Изменения данных проекта

| Файл | Изменение |
|---|---|
| `60_model_closure_domain.json` | `DisclosureClass`, `EffectClass`: добавить `"ordered": true` |
| `global_spec.json` | `standard_version: 3`. Модели придут проекцией, а `standard_version` проекция не переносит — это отдельная авторская правка. |
| `01_models.md:22–24` | Сослаться на `ordered: true` как на материализацию правила. Текст правила не меняется. |

### 4.3 Notes, опирающиеся на порядок (`80_notes.md` @ `b3bee2e`)

| Строка | Сейчас | После миграции |
|---|---|---|
| `:125` `highest_disclosure_class` | «by the declared order of = models.DisclosureClass (open, then business_confidential, then personal_data)» | Убрать пересказ в скобках (дубль `values`, M-E2), ранжировать по `rank()` |
| `:312` `prove_version` | «the highest effect class … in the declared order of = models.EffectClass» | Адрес оставить, порядок теперь нормативен (`ordered`), ранжирование — `rank()` |
| `:311`, `:268`, `:517`, `:607` | Сравнения классов через `highest_disclosure_class` и «above open» | Без изменений: опираются на функцию, которая теперь использует `rank()` |
| `:539` `handle_activate_flow_version` | «highest effect class is above read» | Без изменений текста: «above» теперь определено через `ordered` |
| `:226` `judge_execution` | «in this order of = models.SandboxOutcome: timeout …; resource_exhausted …» | `SandboxOutcome` **не** упорядочен: порядок здесь — приоритет проверок, то есть алгоритм. Убрать «of = models.SandboxOutcome» из выражения порядка; последовательность уже перечислена в самой note. |
| `:119` `fit_port_value` | «checks in exactly this order …: presence, carriage, schema, size» | Без изменений: порядок проверок — алгоритм, задан в самой note и на порядок `FitCheck` не опирается |

Правило A05-5 (`02_rules_flows.md:71–72`, `:102`
`highest_effect_class = max(…)`) по смыслу уже требует `rank()`. В коде это
`max(…, key=EffectClass.rank)`, а не `max(…)` по строке.

### 4.4 Последствия миграции

- Изменятся промпты модулей, импортирующих два enum: строка ordered.
  Изменится `models.py`: метод `rank`. Черновики пересоздадутся
  (`draft_acceptance.inputs`).
- Delta Factory: адреса `models.DisclosureClass.ordered`,
  `models.EffectClass.ordered`. В эксперименте affected-set резолвера
  включал `canonical_values`, `models`, `surface`; для `EffectClass` его
  нужно измерить на шаге D.
- Единицы State 7 затронутых модулей переоткроются и пройдут
  contradictions и `data_closure` по диффу.

---

## 5. План тестов

### 5.1 Factory — валидатор (`test_type_resolver.py`, `test_spec_standard_v2.py` → новый `test_spec_standard_versions.py`)

| Сценарий | Ожидание |
|---|---|
| v2, enum без `ordered` (все проекты) | 0 ошибок, как сейчас |
| v3, `ordered: true` | 0 ошибок |
| v3, `ordered: false` | `ordered_must_be_true` |
| v3, `ordered: "yes"` / `1` / `null` / `[]` | `ordered_must_be_true` |
| v3, `ordered` у обычной модели / `mapping` / `discriminated_union` | `ordered_outside_enum` |
| v2, `ordered: true` | `ordered_requires_standard_version_3` |
| v3, `values: []` | `enum_values_empty` |
| v2 или v3, дубликат в `values` | `enum_values_duplicate` (новый отказ и для v2 — см. §6, S4) |
| v2 или v3, не-строка в `values` | `enum_values_not_string` |
| v3, `ordered` + `members` | `ordered_enum_members_forbidden` |
| v3, `ordered` + `member_names` словарём | `ordered_enum_member_names_dict_forbidden` |
| v3, `ordered` + `member_names` списком той же длины | 0 ошибок |
| v3, `ordered`, значение `rank` | `ordered_enum_reserved_member` |
| `standard_version: 4`, `0`, `"3"`, отсутствует | `unsupported_standard_version` |

### 5.2 Factory — эмиссия (`test_models_selected_draft_generator.py`, `test_models_import_smoke.py`)

- `rank()` возвращает `0..n-1` в порядке `values`; алиасы UPPER дают тот же
  `rank`.
- `D.OPEN < D.BUSINESS_CONFIDENTIAL is False` — строковая семантика
  сохранена (K4).
- Перестановка `values` при существующем `models.py` отражается в эмиссии
  (сейчас не отражается — spike, §4.2).
- `member_names` списком + `ordered`: имена из списка, порядок `values`.
- Смоук-импорт `models.py` с упорядоченным enum и методом `rank`.

### 5.3 Factory — промпт (`test_generate_agent*` / новый)

- Для упорядоченного enum строка в путях `models_code` и `None` побайтно
  одинакова, порядок — `values`, есть пометка и имя `rank`.
- Для неупорядоченного enum оба пути дают ту же строку, что на `391c41c`
  (golden).

### 5.4 Factory — lineage и версии (`test_standard_version_lineage.py`, `factory_state`, `otk_audit`, `handoff_manifest`)

- Lineage v3 → v3 проходит.
- Смешанный lineage (base v2, normalized v3) — mismatch.
- `factory_state` и OTK для v3 не выдают `*_standard_version_mismatch`.

### 5.5 Factory — регрессия без изменения поведения для v2

Прогнать `normalize_spec` → `build_local_spec` → `generate_models_code` →
`build_prompt` на всех `global_spec.json` проектов в `code-factory/projects`
и на канонических кейсах Workbench на старом (`391c41c`) и новом коде.
Побайтное равенство для всех v2-спек — условие S3.

### 5.6 Workbench

| Тест | Сценарий |
|---|---|
| `tests/test_spec_language_workbench.py` | v2 и v3 проходят; `4` → `unsupported_standard_version` |
| `tests/test_spec_projection_workbench.py` (новые случаи) | Отказы N1–N3 из spike и все строки §5.1 на уровне model closure; `ordered` в closure при v2 → BLOCK |
| `tests/test_factory_admission.py` | `FA020`: v3 + Factory без константы → BLOCK; v3 + Factory с `{2, 3}` → PASS; v2 → NOT_APPLICABLE. `FA004` при расхождении стандарта → BLOCK (существующий). |
| `tests/test_factory_slices.py` | `module_prompts` строит промпт с `models_code`: строка enum = боевой формат (фейковую Factory в `tests/test_factory_slices.py` дополнить `generate_models_code`) |
| `tests/test_design_questions_gates.py` | Изменение представления промпта переоткрывает единицу State 7 ровно на дифф её промпта |
| `tests/test_migrate_spec_v2.py` | Без изменений: миграция в v2 не создаёт v3 |

### 5.7 Сквозные отрицательные сценарии (обе стороны)

| Сценарий | Ожидание |
|---|---|
| v3-спека → старая Factory (`391c41c`) | отказ `unsupported_standard_version` (уже проверено) |
| v3-спека → Workbench до шага B | отказ `FA009` |
| v3-спека → Workbench после B, целевая Factory до A | отказ `FA020` |
| v2-спека с `ordered` → новая Factory | отказ `ordered_requires_standard_version_3` |
| Стандарт изменён только в одном репозитории | `FA004` BLOCK |

---

## 6. Условия безопасного включения

| № | Условие | Как проверяется |
|---|---|---|
| S1 | Шаг A слит в Factory `main`, тесты §5.1–§5.4 зелёные | CI Factory |
| S2 | Шаг B слит в Workbench `main`, тесты §5.6 зелёные | CI Workbench (кроме известного красного шага `cabinet-web-backend`, не связанного с изменением) |
| S3 | Для всех v2-спек normalize, срезы, `models.py` и промпты побайтно равны до и после A | Прогон §5.5, результат приложен к PR A |
| S4 | Ни одна существующая спека не содержит дубликатов `values`, не-строковых значений и пустых enum. Иначе новый отказ сломает её сборку. | Тот же прогон §5.5. В Cabinet Kernel 33 enum проверены — нарушений нет (spike, §4). |
| S5 | Шаг C: стандарт побайтно одинаков, `FA004` PASS | `FA004` на любом кейсе |
| S6 | Целевая Factory checkout, указанный проектом (`90_factory_target.json`), содержит A | `FA020` PASS для v3-спеки |
| S7 | После шага B State 7 contradictions переоткрыты и закрыты на новых промптах у проектов, которые идут в Factory | `design_questions.py status --state 7` |
| S8 | Шаг D: Cabinet Kernel проходит Stage 8 и Stage 9 на v3; `rank()` есть в `models.py`; промпты `canonical_values` и `flows` содержат строку ordered | Stage 9 + ручная сверка |

Пока не выполнены S1–S6, ни одна спека не должна объявлять v3. Пока не
выполнено S7, review State 7 закрывает не тот промпт, который получит
генератор.

---

## 7. Расхождение боевого промпта Factory и review-промпта Stage 7

### 7.1 Откуда расхождение

- **Боевой путь.** `generate_agent.main` читает `models.py` проекта
  (`tools/generate_agent.py:2016–2028`) и вызывает
  `build_prompt(local_spec, models_code)` (`:2033`). Поверхность моделей
  строится из кода (`_parse_runtime_model_surface`, `:343–383`).
- **Review-путь.** `factory_slice_workbench._PROMPTS_SCRIPT` вызывает
  `build_prompt(local_spec, None)` (`tools/factory_slice_workbench/service.py:213–232`).
  Поверхность строится из объявления спеки (`:452–466`).

### 7.2 Измерение

Cabinet Kernel @ `b3bee2e`, Factory @ `391c41c`. `models.py` получен
детерминированным `generate_models_code` из среза `models`. Сравнивались
промпты 14 LLM-модулей в двух путях; всего различается 2669 строк.

| Вид различия | Строк | Характер |
|---|---|---|
| Поля моделей | 1992 | **Только порядок**: в двух проверенных модулях множества полей совпадают у всех моделей (`canonical_values` 36/36, `store` 136/136). Боевой путь сортирует поля по алфавиту (`generate_agent.py:379`), review — в порядке объявления. |
| Enum | 504 | **Содержание**: боевой путь даёт имена членов (`OPEN='open'`, только UPPER — `:366`) по алфавиту (`:442`), review — значения в порядке `values` с пометкой «member names were not available» |
| Interface (операции порта) | 102 (только `store`) | **Содержание**: операции `StoreRepository` есть только в боевом пути (`:381–386`, `_protocol_method_signatures` `:390`) |
| Блок `MODELS CONTEXT` | 56 (по 4 на модуль) | Только в боевом пути (`:766–773`) |
| Прочее | 15 | Сопутствующие строки |

Размеры промптов: review 112–598 строк, боевой 117–704 строки на модуль.

### 7.3 Оценка

- **Порядок полей** на поведение не влияет: поля именованные.
- **Enum и interface** — разное содержание. Review проверяет текст, в
  котором у модели нет точных имён членов enum и операций порта. Значит:
  - класс противоречий «note называет член или операцию, которых нет»
    contradictions на review-промпте может не увидеть;
  - его же может ложно увидеть там, где боевой промпт даёт точные имена.
- **Для Q9-a.** Строка ordered, добавленная только в один путь, сделала бы
  review слепым к упорядоченности (или наоборот). Поэтому K7 обязателен.

### 7.4 Решение

**Review строит промпт боевым путём.** Workbench генерирует `models.py`
эмиттером Factory во временном каталоге и передаёт его в `build_prompt`
(§3.2). Строка ordered (§3.1) одинакова в обоих путях.

Альтернатива — менять боевой путь Factory, чтобы он строил поверхность из
спеки. Она отвергнута: это меняет боевые промпты **всех** v2-проектов,
инвалидирует все черновики (`draft_acceptance.inputs`, `prompt_sha256`) и
нарушает условие S3.

**Цена решения.** Один раз после шага B меняются дайджесты всех единиц State 7
во всех кейсах. Contradictions переоткрывают каждый модуль и рецензируют его
по диффу промпта (`questions_workbench/service.py:242–255`). Это работа на
один раунд на модуль, а не новая проверка с нуля. Учтено в условии S7.
