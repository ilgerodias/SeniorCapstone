"""
Local, offline RAG ingestion for hackingBuddyGPT's PrivEscLinux --rag_path corpus.

Replaces utils/rag.py's hardcoded OpenAIEmbeddings (text-embedding-3-large, a
paid API call per chunk/query) with a local sentence-transformers model
(BAAI/bge-small-en-v1.5, 384-dim, runs on CPU) and a *persistent* Chroma store,
so the corpus is embedded once and reloaded on every later run instead of
being re-embedded from scratch each time RagBackground() is constructed.

Source docs: markdown files under --corpus-dir. Front matter (--- ... ---) at
the top of each file is read as per-document metadata (source_url, license,
tags) and attached to every chunk cut from that file.

Usage:
    # one-time ingestion (or re-run after adding/editing corpus files):
    python scripts/rag_ingest.py ingest --corpus-dir docs/rag_corpus/sample \
        --persist-dir .chroma/rag_db

    # sanity-check retrieval against the persisted store (no re-embedding):
    python scripts/rag_ingest.py query --persist-dir .chroma/rag_db \
        --q "how do I escalate privileges on an unpatched Windows SMB server"
"""
import argparse
import hashlib
import re
import sys
from pathlib import Path

try:
    from langchain_community.document_loaders import DirectoryLoader, TextLoader
    from langchain_chroma import Chroma
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_text_splitters import MarkdownTextSplitter
    from langchain_core.documents import Document
except ImportError as e:
    print(f"Missing dependency: {e}. Install with: "
          f"pip install langchain_core langchain-community langchain-chroma "
          f"langchain-huggingface langchain-text-splitters", file=sys.stderr)
    raise

# --- chunking decision (ticket: "Decide chunking") --------------------------
# HackTricks/CVE-note pages are short, dense, technical write-ups (a few
# hundred to ~1500 words per page/section). 800 characters (~150-200 tokens)
# keeps a chunk to roughly one technique/paragraph -- small enough that a
# retrieved chunk is still specific to one vuln/technique, large enough to
# keep a command + its explanation together. 120 chars (~15%) overlap stops a
# command from being severed from the sentence introducing it when it falls
# near a chunk boundary.
CHUNK_SIZE = 800
CHUNK_OVERLAP = 120

# BAAI/bge-small-en-v1.5: 384-dim output, 512 token max sequence length,
# CPU-friendly (~130MB), intended for retrieval/similarity search. Confirmed
# on the model card (word_embedding_dimension: 384) and HF model page.
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIM = 384

FRONT_MATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def parse_front_matter(text: str) -> tuple[dict, str]:
    """Pull a simple `key: value` / `key: [a, b]` YAML-ish front matter block
    off the top of a markdown file. Returns (metadata, remaining_text)."""
    m = FRONT_MATTER_RE.match(text)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key, val = key.strip(), val.strip()
        if val.startswith("[") and val.endswith("]"):
            val = ", ".join(v.strip() for v in val[1:-1].split(",") if v.strip())
        meta[key] = val
    return meta, text[m.end():]


def load_corpus(corpus_dir: str) -> list[Document]:
    loader = DirectoryLoader(
        corpus_dir, glob="**/*.md", show_progress=True, loader_cls=TextLoader
    )
    raw_docs = loader.load()

    docs = []
    for d in raw_docs:
        meta, body = parse_front_matter(d.page_content)
        title_match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
        meta["title"] = title_match.group(1).strip() if title_match else Path(d.metadata["source"]).stem
        meta["source"] = d.metadata["source"]
        docs.append(Document(page_content=body, metadata=meta))
    return docs


def chunk_corpus(docs: list[Document]) -> list[Document]:
    splitter = MarkdownTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    chunks = splitter.split_documents(docs)
    # stable, content-derived id so re-running ingestion on an unchanged file
    # produces the same chunk ids (upsert-safe) instead of duplicating rows.
    for c in chunks:
        h = hashlib.sha1(c.page_content.encode("utf-8")).hexdigest()[:12]
        c.metadata["chunk_id"] = f"{Path(c.metadata['source']).stem}-{h}"
    return chunks


def get_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def cmd_ingest(args):
    docs = load_corpus(args.corpus_dir)
    print(f"loaded {len(docs)} source document(s) from {args.corpus_dir}")

    chunks = chunk_corpus(docs)
    print(f"split into {len(chunks)} chunk(s) "
          f"(chunk_size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")

    embeddings = get_embeddings()
    db = Chroma.from_documents(
        chunks,
        embeddings,
        ids=[c.metadata["chunk_id"] for c in chunks],
        persist_directory=args.persist_dir,
        collection_name="rag_corpus",
    )
    print(f"persisted {db._collection.count()} vectors to {args.persist_dir} "
          f"(collection=rag_corpus, dim={EMBEDDING_DIM})")


def cmd_query(args):
    embeddings = get_embeddings()
    db = Chroma(
        persist_directory=args.persist_dir,
        embedding_function=embeddings,
        collection_name="rag_corpus",
    )
    count = db._collection.count()
    if count == 0:
        print(f"no vectors found in {args.persist_dir} -- run `ingest` first", file=sys.stderr)
        sys.exit(1)
    print(f"loaded persisted store: {count} vectors (no re-embedding of the corpus)")

    results = db.similarity_search_with_relevance_scores(args.q, k=args.k)
    print(f"\ntop {len(results)} result(s) for: {args.q!r}\n")
    for rank, (doc, score) in enumerate(results, start=1):
        print(f"[{rank}] score={score:.3f} source={doc.metadata.get('source')} "
              f"title={doc.metadata.get('title')} tags={doc.metadata.get('tags')}")
        print("    " + doc.page_content.strip().replace("\n", "\n    ")[:300])
        print()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    p_ingest = sub.add_parser("ingest", help="embed a markdown corpus into a persistent Chroma store")
    p_ingest.add_argument("--corpus-dir", required=True)
    p_ingest.add_argument("--persist-dir", required=True)
    p_ingest.set_defaults(func=cmd_ingest)

    p_query = sub.add_parser("query", help="sanity-check retrieval against an already-persisted store")
    p_query.add_argument("--persist-dir", required=True)
    p_query.add_argument("--q", required=True)
    p_query.add_argument("--k", type=int, default=3)
    p_query.set_defaults(func=cmd_query)

    args = p.parse_args()
    args.func(args)
