
## Core research papers (long-context or retrieval-augmented)

* **Retrieval-Augmented Generation (RAG)** — Lewis et al. (Meta/Facebook) 2020. Introduces RAG paradigm: combine parametric LM with non-parametric retrieval.
* **RETRO: Improving language models by retrieving from trillions of tokens** — Borgeaud et al., 2021/2022. Retrieval-enhanced transformer trained with chunked cross-attention.
* **Longformer: The Long-Document Transformer** — Beltagy, Peters, Cohan (2020). Local + global attention to scale to thousands of tokens; also LED variant.
* **BigBird: Transformers for Longer Sequences** — Zaheer et al. (NeurIPS 2020). Sparse attention reducing quadratic cost, theoretical results on expressivity.
* **Reformer: The Efficient Transformer** — Kitaev et al. (2020). Uses locality-sensitive hashing and reversible layers to reduce memory/time.
* **Memory-augmented and retrieval-based works**: papers that explore external memory, retrieval-augmented training, and chunked cross-attention (look up RETRO, RAG, and related follow-ups).

## Summarization & hierarchical approaches

* **Hierarchical summarization / SUMMA** — earlier work on multi-document hierarchical summarization (e.g., SUMMA 2014).
* **Survey & recent papers on long-document summarization** — many 2023–2024 papers + surveys on hierarchical summarization for long documents and multi-stage summarization pipelines.

## Practical system / implementation resources (tutorials, guides)

* **LangChain RAG tutorials** — practical guides for building retrieval + LLM pipelines, how to chunk, index, and query.
* **Pinecone / Chunking guides** — practical blog posts about chunking strategies and best practices for building embeddings+vector DBs.
* **FAISS docs / guides** — common vector search backend used for retrieval.
* **Hugging Face & Meta blogs on RAG and longformer-like usage** — implementation notes, examples and code.

## Community discussions & non-academic sources (where manual search helps)

* **Reddit (r/MachineLearning / r/LanguageTechnology)** — threads discussing practical tradeoffs of chunking vs. long-context models and experiences with RAG.
* **Twitter / X threads** — quick takes from researchers/engineers about RETRO, RAG, or new long-context demos.
* **LinkedIn posts and short threads** — practitioner posts that summarize experience deploying RAG in enterprise apps (e.g., engineers announcing RAG or citation-footnote systems).
* **Blogs & Medium posts** — tutorial-style guides on chunking, prompt design, and hybrid search.

## Practical techniques (notes to mention in talk / README)

* **Chunking / splitting**: split by paragraph/section/semantic boundaries; include overlap between chunks to keep context.
* **Retrieval-Augmented Generation (RAG)**: index documents into vector DB; retrieve top-k passages per query; feed only top-k into LLM.
* **Reranking**: use a cross-encoder to rerank retrieved passages to prioritize the most relevant ones.
* **Evidence extraction**: extract salient sentences/quotes rather than full passages.
* **Hierarchical summarization**: summarize small chunks first, then summarize summaries to obtain a concise representation.
* **Long-context model families**: sparse-attention models (BigBird, Longformer), efficient transformers (Reformer), and retrieval-augmented transformer (RETRO).
* **Memory & external store**: use vector DB as long-term memory and only pull in relevant facts on demand.
* **Human/manual strategies**: skimming abstracts/conclusions, note-taking, cross-referencing across Google, Scholar, Reddit, Twitter, LinkedIn.

