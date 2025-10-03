# Manual Search Report: Text Summarization (NLP)

---

## Search Flow

flowchart TD
    A[Q: Find Papers on Context Length Limitation] --> B[Step 1: Extract Keywords]
    B --> B1[Keywords: context length, long document, LLM, survey]

    B1 --> C[Step 2: Search Google Scholar]
    C --> C1["Query: context length limitation LLM survey 2024"]

    C1 --> D[Step 3: Identify Survey Papers]
    D --> D1["Survey 1: Beyond the Limits (arXiv:2402.02244)"]
    D --> D2["Survey 2: What Why How (arXiv:2401.07872)"]
    D --> D3["Survey 3: Context Engineering (arXiv:2507.13334)"]

    D1 --> E[Step 4: Read Abstracts + Full Text]
    D2 --> E
    D3 --> E

    E --> F[Step 5: Extract SOTA Techniques]
    F --> F1[Taxonomy: 50+ techniques]

    F1 --> G[Step 6: Identify Key Papers]
    G --> G1[Examples: InftyThink, CURIE, LongReason]

    G1 --> H[Step 7: Search for Specific Papers]
    H --> H1["Query: arxiv long context reasoning 2025"]

    H1 --> I[Step 8: Collect Papers from Other Sources]
    I --> I1[Medium/Blogs]
    I --> I2[GitHub Awesome Lists]

    I1 --> J[Step 9: Compile Results]
    I2 --> J
    H1 --> J
    F1 --> J

    J --> K[Step 10: Validate Each Paper]
    K --> K1{Relevant?}
    K1 -->|Yes| L[Keep Paper]
    K1 -->|No| M[Discard]

    L --> N[Final Output: 10 Highly Relevant Papers]

    %% Styling
    style A fill:#e1f5ff,stroke:#0366d6,stroke-width:1px
    style D fill:#fff4e1,stroke:#d17d00,stroke-width:1px
    style F1 fill:#ffe1e1,stroke:#d10000,stroke-width:1px
    style N fill:#e1ffe1,stroke:#00a000,stroke-width:1px

---

## Complete Results

# 📚 Ten Solid Papers

1. **A Systematic Survey of Text Summarization: From Statistical Methods to Large Language Models** — Haopeng Zhang, Philip S. Yu, Jiawei Zhang (2024), *arXiv*  
   Comprehensive: covers the evolution from statistical methods → deep learning → PLMs → LLM-era.

2. **A Comprehensive Survey on Process-Oriented Automatic Text Summarization with Exploration of LLM-Based Methods** — Hanlei Jin et al. (2024), *arXiv*  
   Process-oriented perspective, including discussion of LLMs in summarization.

3. **A Comprehensive Survey of Abstractive Text Summarization: Dataset, Models, and Metrics** — Gospel Ozioma Nnadi, Flavio Bertini (2024), *arXiv*  
   Dedicated to abstractive summarization: models, datasets, and evaluation metrics.

4. **A Survey on Automatic Text Summarization** — (2022), *ACM Computing Surveys*  
   A widely cited broad overview, often used as an entry point into the field.

5. **A Survey for Biomedical Text Summarization: From Pre-trained to Large Language Models** — Qianqian Xie, Zheheng Luo, Benyou Wang, Sophia Ananiadou (2023), *arXiv*  
   Domain-specific: summarization in biomedical and healthcare contexts.

6. **A Survey on Text Summarization Techniques** — (2023), *ResearchGate*  
   General overview of summarization techniques, helpful for mapping main directions.

7. **A Comprehensive Survey for Automatic Text Summarization** — M. Luo et al. (2024), *ScienceDirect*  
   Updated survey highlighting techniques, applications, and trends.

8. **A Survey of Text Summarization: Techniques, Evaluation & Trends** — A. P. Wibawa et al. (2024), *ScienceDirect*  
   Focuses on techniques and evaluation, with insights into emerging trends.

9. **A Survey of Various Text Summarization Techniques using NLP** — (IJCSPub, rjpn.org)  
   Not from a top-tier venue but easy to read; summarizes common practical techniques.

10. **A Survey of DL-Based Abstractive Summarization (Dataset, Models, Metrics)** — M. Zhang et al. (2022), *PMC*  
    Concentrates on abstractive summarization under the deep learning framework.

---

# 📰 Medium / Blog / Practical Articles & Posts

- **LLM Summarization: Getting To Production** — Arize blog (2024), *Arize AI*  
  Practical guide: challenges and solutions in deploying LLM-based summarization.

- **Large Language Models and Text Summarization (A Powerful Combination)** — Singh Rajni (Medium)  
  Explains the concepts and how LLMs are applied to summarization — accessible for beginners.

- **How I Used Python to Create an AI That Summarizes My Notes Automatically** — *Python in Plain English*  
  A personal case study using Python + transformer models for automatic note summarization.

- **Choosing the Right Approach: LLMs vs. Traditional Machine Learning for Text Summarization** — Kyle Garcia (2024), *Enterprise Knowledge*  
  Comparison between traditional approaches and LLM-based methods for real-world use cases.


# 🔍 Query Used for Literature Search

## arXiv
- "text summarization survey 2024"  
- "automatic text summarization review" AND LLM  
- "abstractive summarization survey dataset models metrics"  
- "biomedical summarization survey pre-trained large language models"  

## Google Scholar
- "survey of text summarization techniques"  
- "text summarization comprehensive survey ACM Computing Surveys"  
- "deep learning abstractive summarization survey"  
- "process-oriented summarization LLM"  

## ResearchGate
- "A survey on text summarization techniques 2023 ResearchGate"  
- "automatic text summarization overview methods applications"  

## ScienceDirect
- "comprehensive survey automatic text summarization 2024 ScienceDirect"  
- "evaluation metrics for summarization techniques"  

## Other Queries (General Google)
- "LLM summarization blog production site:arize.com"  
- "text summarization medium.com LLM"  
- "python automatic summarization transformer blog"  
- "LLM vs traditional summarization Enterprise Knowledge"  

---

# 🧩 Keywords & Knowledge Extracted from Papers

## 1. Core Methods
- **Statistical methods** → frequency-based, TF-IDF, graph-based (TextRank, LexRank).  
- **Neural networks** → RNN, Seq2Seq with attention.  
- **Transformer-based PLMs** → BERTSUM, PEGASUS, BART, T5.  
- **LLM-based summarization** → GPT family, LLaMA, PaLM 2, fine-tuned or zero-shot prompting.  

## 2. Summarization Paradigms
- Extractive vs Abstractive summarization  
- Hybrid approaches  
- Process-oriented summarization → pipeline stages: preprocessing → representation → sentence scoring/selection → generation  

## 3. Datasets
- **General domain**: CNN/DailyMail, XSum, Gigaword, Reddit TIFU, WikiHow.  
- **Scientific domain**: arXiv, PubMed, SciSummNet.  
- **Biomedical domain**: CORD-19, clinical trial abstracts, biomedical QA datasets.  

## 4. Evaluation Metrics
- **Traditional automatic metrics**: ROUGE, BLEU, METEOR.  
- **Semantic similarity metrics**: BERTScore, MoverScore, QuestEval.  
- **Human evaluation**: coherence, fluency, factual consistency, coverage.  
- **New directions**: LLM-as-a-judge for summarization quality.  

## 5. Trends & Challenges
- Hallucination in abstractive/LLM summaries.  
- Domain adaptation (biomedical, legal, financial).  
- Multi-document summarization.  
- Controllable summarization (length, style, focus).  
- Evaluation gap: ROUGE vs actual semantic quality.  
- LLMs → shift from training task-specific summarizers to prompting/few-shot methods.  

## 6. Practical Insights (from Blogs/Posts)
- Deployment challenges: cost, latency, context length.  
- Comparison: LLMs (flexibility, quality) vs. traditional methods (efficiency, predictability).  
- Engineering concerns: prompt design, chunking, post-processing.  
- Example pipelines: Python + HuggingFace Transformers for personal note summarization.  



# 📌 Review of ASTA System & Recommended Improvements

## Limitations of ASTA (system.md)
- Query rewrite is too generic → no taxonomy expansion, missing survey/review emphasis.
- Keyword query has only one variation ("text summarization NLP") → very limited coverage.
- No negative filters → irrelevant papers (economics, bibliometrics) easily included.
- No boosting based on datasets/metrics → hard to prioritize benchmark-driven papers.
- Reranker only uses cross-encoder relevance, with no constraint checks (e.g., keyword frequency of "summarization").
- No seeding of core papers → risks missing foundational works (TextRank, Pointer-Generator, etc.).
- Overall: low precision, noisy recall, results not domain-focused.

## Improvements Applied (3_10.md)
1. **Query Rewrite Layer**  
   - Taxonomy-aware expansion (extractive, abstractive, transformer-based, datasets, evaluation).  
   - Explicit emphasis on survey/review keywords.  
   - Added `intitle:summarization` rule to focus on relevant titles.  

2. **Keyword Query Layer**  
   - Multiple variations: abstractive / extractive / long-document.  
   - Negative filters to exclude irrelevant domains (economics, bibliometrics, etc.).  

3. **Semantic Search Layer**  
   - Boost papers mentioning benchmark datasets (CNN/DailyMail, XSum, PubMed).  
   - Boost if metrics appear (ROUGE, BLEU, BERTScore).  

4. **Reranking Improvements**  
   - Constraint check: abstract/title must contain “summarization” ≥2 times.  
   - Boost if evaluation terms (ROUGE, evaluation metric) are present.  
   - Downrank off-topic results.  

5. **Seed Anchoring**  
   - Whitelist influential papers (TextRank, Pointer-Generator, BART, PEGASUS).  
   - Guarantees canonical works appear in top results.

## Expected Outcomes
- 🎯 Higher precision: results are domain-specific and focused on summarization.  
- 📚 Sufficient recall but with irrelevant noise filtered out.  
- 🏆 Key benchmark and survey papers reliably included in top results.  
- 🔎 Domain-aware pipeline, adaptable to other research tasks.
