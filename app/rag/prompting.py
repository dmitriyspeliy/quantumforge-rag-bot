"""
Prompt templates for the RAG bot.
"""

from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate


SYSTEM_PROMPT = """
You are a corporate knowledge-base assistant for the fictional Astral Rift Chronicles domain.

Rules:
1. Answer only using the provided context.
2. If the context does not contain enough information, answer exactly:
   "Я не знаю. В базе знаний нет достаточно информации для ответа."
3. Do not use outside knowledge.
4. Provide a short public explanation of how the answer was found.
5. Do not reveal hidden reasoning. Use only concise, source-based steps.
6. At the end, list sources in the format: Источники: file_name#chunk_id.

Answer format:
Шаги:
1. ...
2. ...

Ответ:
...

Источники:
- ...
""".strip()


FEW_SHOT_EXAMPLES = """
Few-shot examples:

Q: Who was Xarn Velgor?
A:
Шаги:
1. В найденном фрагменте указано, что Xarn Velgor раньше был Aren Solvyr.
2. Там же сказано, что он стал Noctari servant of the Orion Dominion.

Ответ:
Xarn Velgor раньше был Aren Solvyr, одарённым Asterian Knight. После падения он стал Noctari servant of the Orion Dominion и символом страха.

Источники:
- 01_xarn_velgor.md#0

Q: What is the Void Core?
A:
Шаги:
1. В найденном фрагменте Void Core описан как massive battle station.
2. Также указано, что он использовался для fear-based control.

Ответ:
Void Core — это огромная боевая станция Dominion, созданная для уничтожения планет и контроля через страх.

Источники:
- 11_void_core.md#10
""".strip()


RAG_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        ("human", "{few_shot_examples}\n\nContext:\n{context}\n\nUser question:\n{question}"),
    ]
)


def format_context(chunks: list[dict]) -> str:
    """
    Convert retrieved chunks to prompt context with metadata.
    """

    if not chunks:
        return ""

    formatted: list[str] = []
    for chunk in chunks:
        formatted.append(
            "\n".join(
                [
                    f"Source: {chunk['source']}#{chunk['chunk_id']}",
                    f"Title: {chunk['title']}",
                    f"Score: {chunk['score']:.4f}",
                    "Text:",
                    chunk["content"],
                ]
            )
        )

    return "\n\n---\n\n".join(formatted)
