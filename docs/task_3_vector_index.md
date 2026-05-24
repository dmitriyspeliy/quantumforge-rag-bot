# Задание 3. Создание векторного индекса базы знаний

## Выбранная embedding-модель

Для индексации используется модель:

```text
OpenAI text-embedding-3-small
```

Параметры:

```text
API: OpenAI Embeddings API
Размер эмбеддинга: 1536 dimensions
Назначение: semantic search / retrieval для RAG
```

Модель выбрана в задании 1, потому что она подходит для быстрого MVP, не требует локального GPU и даёт хорошее качество поиска при низкой стоимости.

## Векторная база

Используется:

```text
FAISS
```

Причины выбора:

- быстро работает локально;
- не требует отдельного сервера;
- подходит для учебного MVP;
- просто сохраняется в папку `vectorstore/`;
- интегрируется с LangChain.

## База знаний

В качестве базы знаний используется папка:

```text
data/knowledge_base/
```

В ней находится 30+ уникальных Markdown-документов и словарь замен:

```text
terms_map.json
```

Документы описывают вымышленную sci-fi вселенную, созданную через замену ключевых терминов. Это нужно, чтобы LLM не могла отвечать по памяти и была вынуждена использовать RAG-индекс.

## Chunking

Для разбиения документов используется:

```text
RecursiveCharacterTextSplitter
```

Параметры по умолчанию:

```text
CHUNK_SIZE=1200
CHUNK_OVERLAP=150
```

У каждого чанка сохраняются метаданные:

```text
source
title
file_name
chunk_id
chunk_index
chunk_size
```

Это нужно, чтобы бот мог показывать источник ответа.

## Как построить индекс

Создать `.env`:

```powershell
copy .env.example .env
```

Заполнить:

```env
OPENAI_API_KEY=your_openai_api_key
```

Построить индекс:

```powershell
python scripts/build_index.py
```

После выполнения в папке `vectorstore/` появятся файлы FAISS-индекса:

```text
index.faiss
index.pkl
```

## Как проверить поиск

Пример запроса:

```powershell
python scripts/search_index.py "Who was Xarn Velgor?"
```

Дополнительные примеры:

```powershell
python scripts/search_index.py "What is the Void Core?"
python scripts/search_index.py "Where did Oryn train Lior Solvyr?"
python scripts/search_index.py "What organization resisted the Orion Dominion?"
```

## Ожидаемый результат

Поисковый скрипт должен вернуть релевантные чанки с метаданными:

```text
source
title
chunk_id
score
text
```

Пример:

```text
Query: Who was Xarn Velgor?
Results: 4
source=01_xarn_velgor.md
title=Xarn Velgor
chunk_id=0
score=...
text=Xarn Velgor was once Aren Solvyr...
```

## Что фиксируется после генерации

После запуска `build_index.py` нужно зафиксировать:

```text
scripts/build_index.py
scripts/search_index.py
app/rag/*
docs/task_3_vector_index.md
vectorstore/index.faiss
vectorstore/index.pkl
```

Также в README задания указывается:

```text
Embedding model: text-embedding-3-small
Embedding size: 1536
Vector DB: FAISS
Knowledge base: data/knowledge_base
Chunks count: вывод команды build_index.py
Generation time: вывод команды build_index.py
```
