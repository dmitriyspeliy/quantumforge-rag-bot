# Задание 7. Аналитика покрытия и качества базы знаний

## Цель

Оценить полноту и качество базы знаний RAG-бота, выявить темы, по которым бот не сможет ответить, и подготовить рекомендации по улучшению покрытия.

## Искусственные пробелы

Для задания добавлены искусственные пробелы. Физически документы из базы не удаляются, чтобы не ломать предыдущие задания. Вместо этого используется конфигурация:

```text
data/evaluation/coverage_gaps.json
```

Исключённые темы:

```text
Xarn Velgor
Void Core
Synth Flux
```

Исключённые источники:

```text
01_xarn_velgor.md
11_void_core.md
08_synth_flux.md
```

Во время оценки вопросы по этим темам считаются отсутствующими в базе знаний, и корректное поведение бота — ответить:

```text
Я не знаю. В базе знаний нет достаточно информации для ответа.
```

## Логирование запросов

Скрипт оценки сохраняет JSONL-лог:

```text
docs/task7_logs/rag_evaluation_logs.jsonl
```

Каждая строка содержит:

```text
timestamp
id
question
topic
expected_status
actual_status
success
chunks_found
answer_length
answer
sources
blocked_sources
matched_keywords
missing_keywords
notes
```

## Golden set

Golden set находится в файле:

```text
data/evaluation/golden_questions.jsonl
```

В нём 12 вопросов:

- 7 вопросов на известные темы;
- 3 вопроса на искусственно исключённые темы;
- 2 вопроса вне домена.

## Автоматическое тестирование

Скрипт:

```text
scripts/evaluate.py
```

Запуск:

```powershell
python scripts\evaluate.py
```

Результаты:

```text
docs/task7_logs/rag_evaluation_logs.jsonl
docs/task7_logs/rag_evaluation_report.json
```

## Метод оценки

Для каждого вопроса проверяется:

1. ожидаемый статус: `answer` или `unknown`;
2. были ли найдены чанки;
3. длина ответа;
4. найденные источники;
5. наличие ожидаемых ключевых слов;
6. флаг успешности.

## Диаграмма

PlantUML sequence diagram:

```text
docs/diagrams/task7_evaluation_sequence.puml
```

Диаграмма показывает:

```text
evaluate.py -> golden set -> RAG bot -> FAISS -> LLM -> logs/report
```

А также потенциальные точки сбоя:

- пустой индекс;
- нерелевантные чанки;
- устаревший документ;
- искусственный пробел;
- prompt-injection chunk;
- ответ без ожидаемых ключевых слов.

## Ожидаемые выводы

Плохо покрытые темы:

```text
Xarn Velgor
Void Core
Synth Flux
```

Количество искусственных пробелов:

```text
3
```

Темы вне базы:

```text
capital of Finland
QuantumForge + Snowflake integration
```

Рекомендации:

1. Вернуть или переписать документы по Xarn Velgor, Void Core и Synth Flux.
2. Добавить владельцев и дату актуальности для документов.
3. Поддерживать golden set и запускать `evaluate.py` после каждого обновления индекса.
4. Анализировать вопросы, где бот ответил `unknown`, и на их основе расширять базу.
5. Для production добавить dashboard по темам, источникам, unknown-rate и качеству retrieval.
