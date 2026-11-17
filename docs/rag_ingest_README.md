# Running `scripts/rag_ingest.py`

## Setup

```bash
pip install langchain_core langchain-community langchain-chroma \
    langchain-huggingface langchain-text-splitters markdown
# (same as the repo's existing `rag` extra, plus langchain-huggingface in
#  place of langchain-openai)
```

First run downloads `BAAI/bge-small-en-v1.5` (~130MB) from Hugging Face —
needs normal internet access once, then it's cached locally
(`~/.cache/huggingface`) and every later run is fully offline.

## Ingest (build/update the persisted store)

```bash
python scripts/rag_ingest.py ingest \
    --corpus-dir docs/rag_corpus/sample \
    --persist-dir .chroma/rag_db
```

Safe to re-run after editing/adding corpus files — chunk ids are derived
from file + content hash, so unchanged chunks are upserted in place rather
than duplicated.

## Query (sanity-check retrieval, no re-embedding)

```bash
python scripts/rag_ingest.py query \
    --persist-dir .chroma/rag_db \
    --q "how do I escalate privileges on an unpatched Windows SMB server" \
    --k 3
```

This opens a *new* `Chroma` handle against `--persist-dir` without calling
`ingest` again — it should report the same vector count as the last ingest
and answer instantly (only the query string gets embedded, not the corpus).

## What's verified vs. what still needs your pass

I ran the full pipeline (load → chunk → embed → persist → reload → query)
against the 2-file sample corpus in `docs/rag_corpus/sample/`, but **this
sandbox has no network route to huggingface.co**, so I substituted a fake
deterministic embedding function to prove out the plumbing:

- ✅ Markdown loading + front-matter metadata parsing
- ✅ Chunking (800/120) produces one chunk per sample doc at this size
- ✅ Chunk ids are stable across re-ingestion of an unchanged corpus (no
  duplicate growth — confirmed by ingesting twice and comparing counts)
- ✅ A fresh `Chroma(persist_directory=...)` handle (simulating a new
  process / new run) reloads the same vector count without re-embedding
- ⚠️ **Not verified by me: real semantic retrieval quality.** The fake
  embedding I used for the plumbing test returns near-random similarity
  rankings by design — that's expected and not a bug in the script. You
  need to run `ingest` + `query` yourself once with real network access so
  `bge-small-en-v1.5` actually downloads, then confirm the sample query
  above correctly ranks the SMB/EternalBlue chunk above the unrelated SUID
  chunk. That's the "sanity-check retrieval: sample queries return relevant
  chunks, sensibly ranked" item on your list — flagging it as still open.

## Next steps (still on your list)

- Build the real corpus (HackTricks + CVE notes for your chosen targets) —
  see `docs/rag_chunking.md`.
- Hand the retrieval interface (`Chroma(...).similarity_search(...)`, or
  wrap it to match whatever call signature Ian's integration contract
  specifies) to Ian so it plugs into the agent loop.
