import os
try:
    from langchain_community.document_loaders import DirectoryLoader, TextLoader
    from langchain_chroma import Chroma
    from langchain_ollama import OllamaEmbeddings
    from langchain_text_splitters import MarkdownTextSplitter
except ImportError:
    _has_langchain = False
else:
    _has_langchain = True

def has_langchain():
    return _has_langchain

class RagBackground:

    retriever = None

    # TODO: implement cache (loading from Chroma database)
    # db = Chroma(persist_directory=persistent_directory, embedding_function=embeddings)
    def __init__(self, rag_path, llm, glob_pattern='**/*.md'):
        print("now loading documents")
        loader = DirectoryLoader(rag_path, glob=glob_pattern, show_progress=True, loader_cls=TextLoader)
        documents = loader.load()
        print("done loading documents")

        markdown_splitter = MarkdownTextSplitter(chunk_size=1000, chunk_overlap=0)
        documents = markdown_splitter.split_documents(documents)
        embeddings = OllamaEmbeddings(
            model="nomic-embed-text",
            base_url=os.environ.get("OLLAMA_API_BASE", "http://192.168.122.1:11434"),
        )

        print("loading into vector store")
        db = Chroma.from_documents(documents, embeddings)

        self.retriever = db.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 10},
        )

    def get_relevant_documents(self, query):
        if not self.retriever:
            raise ValueError("RAG system not initialized")
        result = self.retriever.get_relevant_documents(query)
        return "".join([d.page_content + "\n" for d in result])