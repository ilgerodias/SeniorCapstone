# RAG corpus: chunking + metadata decisions

## Chunking

| Parameter | Value | Why |
|---|---|---|
| Splitter | `MarkdownTextSplitter` (langchain) | Corpus source (HackTricks pages) is markdown; splits on markdown structure (headers, code fences) before falling back to char-count, so a chunk doesn't get cut mid-command. |
| Chunk size | **800 characters** (~150-200 tokens) | HackTricks/CVE-note pages are short, dense write-ups — a technique + its one-liner command is usually a paragraph. 800 chars keeps one technique per chunk (specific enough that a retrieved chunk is actually about the query's vulnerability, not a grab-bag of three unrelated techniques), while staying well under the embedding model's 512-token input limit. |
| Overlap | **120 characters** (15%) | Stops a command from being severed from the sentence introducing it when it falls near a boundary. 15% is the common default for technical/procedural text; higher wastes storage on duplicate content for little retrieval gain at this corpus size. |

Original code (`utils/rag.py:26`) used `chunk_size=1000, chunk_overlap=0`.
Zero overlap means any technique whose explanation straddles a chunk boundary
loses half its context on retrieval. We cut size slightly and added overlap.

## Per-chunk metadata

Pulled from a YAML-ish front-matter block at the top of each corpus `.md`
file (see `docs/rag_corpus/sample/*.md` for the format), then attached to
every chunk cut from that file by `chunk_corpus()` in `scripts/rag_ingest.py`:

| Field | Example | Purpose |
|---|---|---|
| `source` | file path | Traceability back to the corpus file. |
| `source_url` | `https://book.hacktricks.xyz/...` | Original page, for citation and for re-crawling if the corpus needs refreshing. |
| `title` | `SMB / MS17-010 (EternalBlue)` | First `#` heading in the file — shown next to a retrieved chunk so a human (or Jeorge's viewer) can see what it's from without opening the file. |
| `license` | HackTricks license text | Required per the "record each source's license, keep attribution" ticket. |
| `tags` | `smb, ms17-010, eternalblue, windows, remote-exploit` | Manually curated per source page; lets retrieval be filtered/boosted by target OS or vuln class later if needed. |
| `chunk_id` | `smb-eternalblue-a6844adf7a21` | `{file-stem}-{sha1(chunk text)[:12]}`. Deterministic: re-running ingestion on an unchanged file produces the *same* id, so Chroma's `ids=` upsert overwrites in place instead of duplicating. Verified in the smoke test (re-ingesting an unchanged corpus leaves the vector count unchanged). |

## Corpus sourcing (ticket: HackTricks + CVE/service notes, license per source)

Not yet done — this is the next step before a real ingestion run:
1. Pick the final target shortlist (see `docs/targets.md`) first, since the
   corpus should cover exactly the services/vulns those targets expose
   (don't scrape all of HackTricks).
2. For each target's exposed service/vuln, pull the matching HackTricks
   page(s) + any CVE/vendor advisory notes, save as markdown under
   `docs/rag_corpus/`, with the front-matter block (`source_url`, `license`,
   `tags`) filled in exactly as in the sample files.
3. Re-run `scripts/rag_ingest.py ingest` to rebuild the persisted store.
