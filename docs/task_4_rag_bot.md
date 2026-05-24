# Задание 4. Реализация RAG-бота с техниками промптинга

## Что реализовано

Создан RAG-бот, который:

1. принимает пользовательский вопрос;
2. строит embedding запроса той же моделью, что использовалась для индексации;
3. ищет ближайшие чанки в FAISS;
4. проверяет релевантность найденных фрагментов по score threshold;
5. формирует prompt с найденным контекстом;
6. применяет few-shot prompting;
7. просит модель дать короткие публичные шаги ответа на основе источников;
8. отправляет prompt в LLM;
9. возвращает ответ и список использованных источников.

## Используемые компоненты

```text
Embedding model: text-embedding-3-small
LLM: задаётся через CHAT_MODEL
Vector DB: FAISS
Knowledge base: data/knowledge_base
Index directory: vectorstore
Interface: CLI / REPL
```

## Few-shot prompting

В prompt добавлены два примера из той же предметной области:

1. вопрос про Xarn Velgor;
2. вопрос про Void Core.

Они нужны, чтобы модель отвечала в ожидаемом формате:

```text
Шаги:
1. ...
2. ...

Ответ:
...

Источники:
- ...
```

## Chain-of-Thought

В реализации используется безопасный вариант: модель не раскрывает скрытое рассуждение, а показывает только краткие публичные шаги, основанные на найденных источниках.

Это соответствует цели задания: пользователь видит, как ответ связан с документами, но бот не выдаёт внутренние рассуждения модели.

## Запуск одного вопроса

```powershell
python scripts/ask_bot.py "Who was Xarn Velgor?"
```

## Запуск REPL

```powershell
python -m app.main
```

Выход:

```text
exit
```

## Примеры успешных вопросов

```powershell
python scripts/ask_bot.py "Who was Xarn Velgor?"
python scripts/ask_bot.py "What is the Void Core?"
python scripts/ask_bot.py "Where did Oryn train Lior Solvyr?"
python scripts/ask_bot.py "What organization resisted the Orion Dominion?"
python scripts/ask_bot.py "What is the Silver Kestrel?"
```

## Примеры вопросов, где бот должен ответить «Я не знаю»

```powershell
python scripts/ask_bot.py "What is the capital of Finland?"
python scripts/ask_bot.py "How does QuantumForge integrate with Snowflake?"
```

## Критерий отказа

В FAISS setup используется distance-like score: чем меньше score, тем ближе найденный чанк.

Если лучший найденный score выше `RAG_SCORE_THRESHOLD`, бот не отправляет вопрос в LLM и отвечает:

```text
Я не знаю. В базе знаний нет достаточно информации для ответа.
```

Текущее значение:

```env
RAG_SCORE_THRESHOLD=0.85
```

## Файлы реализации

```text
app/rag/chain.py
app/rag/prompting.py
app/main.py
scripts/ask_bot.py
docs/task_4_rag_bot.md
```
