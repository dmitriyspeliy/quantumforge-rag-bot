# Задание 6. Автоматическое ежедневное обновление базы знаний

## Выбранный источник данных

Для учебного проекта выбран симулированный локальный источник:

```text
data/incoming_docs/
```

Логика такая:

1. новые или изменённые документы появляются в `data/incoming_docs/`;
2. скрипт `scripts/update_index.py` сканирует эту папку;
3. новые/изменённые файлы копируются в `data/knowledge_base/`;
4. затем пересобирается FAISS-индекс.

Такой источник выбран потому, что он прост для демонстрации, не требует доступа к S3, Google Drive или GitHub API, но показывает тот же production-паттерн: внешний источник → ingestion → chunking → embeddings → vector index.

## Скрипт обновления индекса

Основной скрипт:

```text
scripts/update_index.py
```

Он выполняет:

1. сканирование `data/incoming_docs/`;
2. расчёт SHA-256 для каждого `.md`/`.txt` файла;
3. сравнение с manifest-файлом;
4. копирование новых/изменённых файлов в `data/knowledge_base/`;
5. загрузку документов;
6. разбиение на чанки;
7. генерацию embeddings;
8. пересборку FAISS-индекса;
9. запись JSON-лога.

## Manifest

Для отслеживания изменений используется файл:

```text
docs/task6_logs/index_manifest.json
```

В нём хранится соответствие:

```text
relative_file_path -> sha256
```

Если hash файла изменился, документ считается изменённым и повторно попадает в индекс.

## Логирование

Лог обновления пишется в:

```text
docs/task6_logs/update_index.log.json
```

В лог попадает:

```text
started_at
finished_at
duration_sec
source_dir
knowledge_base_dir
vectorstore_dir
embedding_model
files_scanned
files_added_or_changed
documents_loaded
chunks_indexed
index_files
errors
changed_files
```

Пример:

```json
{
  "started_at": "2026-05-24T18:00:00",
  "finished_at": "2026-05-24T18:00:07",
  "duration_sec": 7.12,
  "source_dir": "data\\incoming_docs",
  "knowledge_base_dir": "data\\knowledge_base",
  "vectorstore_dir": "vectorstore",
  "embedding_model": "text-embedding-3-small",
  "files_scanned": 1,
  "files_added_or_changed": 1,
  "documents_loaded": 35,
  "chunks_indexed": 35,
  "index_files": [
    "index.faiss",
    "index.pkl"
  ],
  "errors": []
}
```

## Запуск вручную

```powershell
python scripts\update_index.py
```

## Настройка ежедневного запуска на Windows

Для Windows используется Task Scheduler.

Скрипт регистрации задачи:

```text
scripts/register_daily_update_task.ps1
```

Запуск:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\register_daily_update_task.ps1
```

По умолчанию задача создаётся с параметрами:

```text
Task name: QuantumForgeRagDailyIndexUpdate
Schedule: каждый день в 06:00
```

Можно указать другое время:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\register_daily_update_task.ps1 -RunAt "07:30"
```

## Поведение при ошибке

Если во время обновления возникает ошибка:

1. ошибка записывается в `errors`;
2. скрипт завершает работу с exit code `1`;
3. Task Scheduler фиксирует неуспешное выполнение;
4. лог остаётся в `docs/task6_logs/update_index.log.json`.

Для production можно добавить retry, alert в Slack/Telegram и отдельный dead-letter каталог для проблемных документов.

## Проверка обновления

1. Добавить новый `.md` файл в:

```text
data/incoming_docs/
```

2. Запустить:

```powershell
python scripts\update_index.py
```

3. Проверить лог:

```powershell
Get-Content docs\task6_logs\update_index.log.json
```

4. Проверить поиск по новому документу:

```powershell
python scripts\search_index.py "What is HyperRelay?"
```

## Архитектурная диаграмма

PlantUML-диаграмма находится в файле:

```text
docs/diagrams/task6_auto_update.puml
```

Поток:

```text
data/incoming_docs
  -> scripts/update_index.py
  -> data/knowledge_base
  -> chunking
  -> embeddings
  -> FAISS index
  -> logs
```

## Итог

В проекте реализовано автоматическое обновление базы знаний через локальный источник документов. Решение можно запускать вручную или ежедневно через Windows Task Scheduler. Скрипт логирует изменения, количество новых документов, размер итогового индекса и ошибки.
