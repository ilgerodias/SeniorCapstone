# RAG use-case: findings + replacement plan

Owner: Andres · Source read: `src/hackingBuddyGPT/utils/rag.py`,
`src/hackingBuddyGPT/usecases/priv_esc/linux_privesc.py`

## Where things are today

**`utils/rag.py`** is the entire RAG implementation (42 lines). `PrivEscLinux`
(`usecases/priv_esc/linux_privesc.py`) is the only use-case that touches it:
when `--rag_path` is set, `init()` builds one `RagBackground` instance
(line 143) and `analyze_result()` calls `get_relevant_documents()` on every
step (line 244) to pull context for the LLM's explanation of the last
command's output.

| What | File : line |
|---|---|
| OpenAI hardcoded (import) | `utils/rag.py:4` — `from langchain_openai import OpenAIEmbeddings` |
| OpenAI hardcoded (instantiation) | `utils/rag.py:28` — `OpenAIEmbeddings(model="text-embedding-3-large", api_key=llm.api_key)`. Reuses the *chat* LLM's API key as the embeddings API key — only works if both chat and embeddings are served from the same OpenAI-compatible endpoint. |
| Embeddings **created** | `utils/rag.py:31` — `Chroma.from_documents(documents, embeddings)`, inside `RagBackground.__init__`. No `persist_directory` is passed, so this is an **in-memory, ephemeral** Chroma collection — every `RagBackground()` call (i.e. every run) re-embeds the entire corpus from scratch via the OpenAI API. The `# TODO: implement cache` comment above it (line 18-19) confirms this is a known gap, not an oversight. |
| Embeddings **queried** | `utils/rag.py:38-41` — `get_relevant_documents(query)`, `k=10` similarity search, called from `linux_privesc.py:244`. |
| Corpus loading / chunking | `utils/rag.py:20-27` — `DirectoryLoader` over `rag_path` (glob `**/*.md` by default), `MarkdownTextSplitter(chunk_size=1000, chunk_overlap=0)`. No metadata is attached beyond what `DirectoryLoader`/`TextLoader` set automatically (just `source` = file path). |
| How a run enables it | CLI flag `--rag_path=<dir of markdown files>`, requires the `rag` extra (`uv sync --extra rag` / `pip install '.[rag]'`) — see `pyproject.toml:73-78` and `README.md:107,152`. If `--rag_path` is set but `langchain` isn't installed, it raises `ImportError` (`linux_privesc.py:138-140`). |

## What has to change for "local, no OpenAI"

1. Swap `OpenAIEmbeddings` → a local `sentence-transformers` model
   (`BAAI/bge-small-en-v1.5`, 384-dim, CPU-friendly, retrieval-tuned — see
   its model card). No API key, no network call per chunk/query.
2. Give `Chroma.from_documents` a `persist_directory` so the corpus is
   embedded **once** and reloaded from disk on every later run — this closes
   the exact gap the `# TODO` comment flags.
3. Separate **ingestion** (build/update the persisted store from the corpus)
   from **retrieval** (load the persisted store, embed only the query) —
   today both are smashed into one constructor that always re-embeds
   everything.
4. Chunking stays markdown-aware but should carry real per-chunk metadata
   (source URL, license, tags) instead of just a file path — the corpus is
   HackTricks pages + CVE notes, and License/attribution tracking is one of
   the other RAG tickets, so the metadata needs to survive chunking.

## What I built

`scripts/rag_ingest.py` — a standalone ingestion/query CLI that implements
all four points above, built on the same `langchain` + `Chroma` stack the
existing code already depends on (so it's a near drop-in for `utils/rag.py`,
not a rewrite in a different framework). See `docs/rag_chunking.md` for the
chunking/metadata decisions and `docs/rag_ingest_README.md` for how to run
and verify it.

**Not yet done (next ticket, for Ian): wire this into `RagBackground`/
`PrivEscLinux`.** Right now `scripts/rag_ingest.py` is a standalone tool
proving the local-embedding + persistence approach works; swapping it into
`utils/rag.py` itself (so `--rag_path` uses it directly) is the integration
step and should happen together with the integration-contract interface Ian
is writing, not before it.
