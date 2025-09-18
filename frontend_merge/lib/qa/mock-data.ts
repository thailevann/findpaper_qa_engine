import type { QAResult } from "@/app/page"

export const generateMockData = (query: string): QAResult => {
  return {
    original_query: query,
    rewritten_query: `Enhanced query: ${query} with advanced filtering`,
    keyword_query: `machine learning OR "artificial intelligence" OR "deep learning" OR "neural networks"`,
    gemini_filters: {
      year_range: "2020-2024",
      domains: ["computer science", "artificial intelligence"],
      confidence_threshold: 0.8,
    },
    raw_gemini_output:
      "Applied semantic filtering and relevance scoring to identify the most pertinent research papers.",
    qa_result: {
      query: query,
      filtered_passages: [
        "Recent advances in transformer architectures have shown significant improvements in computational efficiency and model performance. The introduction of sparse attention mechanisms reduces computational complexity from O(n²) to O(n log n).",
        "Self-supervised learning has emerged as a powerful paradigm that leverages unlabeled data to learn meaningful representations. Methods like contrastive learning and masked image modeling have achieved state-of-the-art results.",
        "Federated learning enables training machine learning models across decentralized data sources while preserving privacy. Recent work addresses communication efficiency and convergence guarantees in heterogeneous environments.",
        "The introduction of sparse attention mechanisms reduces computational complexity while maintaining model expressiveness.",
        "Novel pruning techniques and quantization methods enable deployment of sophisticated models on resource-constrained devices.",
        "Contrastive learning methods have revolutionized representation learning by maximizing agreement between differently augmented views of the same data.",
        "Model-agnostic meta-learning (MAML) enables rapid adaptation to new tasks with minimal training examples.",
        "Differential privacy mechanisms provide formal guarantees about individual data point privacy while enabling collaborative learning.",
        "Certified defense methods provide provable guarantees against adversarial attacks within specified threat models."
      ],
      themes: [
        {
          name: "Introduction/Background",
          quotes: [
            "Machine learning has evolved rapidly with transformer architectures becoming the foundation for most modern AI systems.",
            "The field has shifted from supervised learning paradigms toward more efficient self-supervised approaches."
          ]
        },
        {
          name: "Architectural Innovations",
          quotes: [
            "The introduction of sparse attention mechanisms reduces computational complexity while maintaining model expressiveness.",
            "Novel pruning techniques and quantization methods enable deployment of sophisticated models on resource-constrained devices."
          ]
        },
        {
          name: "Learning Paradigms",
          quotes: [
            "Contrastive learning methods have revolutionized representation learning by maximizing agreement between differently augmented views of the same data.",
            "Model-agnostic meta-learning (MAML) enables rapid adaptation to new tasks with minimal training examples."
          ]
        },
        {
          name: "Privacy and Security",
          quotes: [
            "Differential privacy mechanisms provide formal guarantees about individual data point privacy while enabling collaborative learning.",
            "Certified defense methods provide provable guarantees against adversarial attacks within specified threat models."
          ]
        }
      ],
      final_report: `Based on the analysis of recent research papers, several key advances in machine learning have emerged:

**Architectural Innovations**: The field has seen significant improvements in neural network architectures, particularly in transformer models. Sparse attention mechanisms have reduced computational complexity while maintaining performance, making large language models more efficient. Additionally, novel architectures designed for edge computing enable deployment of sophisticated models on resource-constrained devices.

**Learning Paradigms**: Self-supervised learning has become a dominant paradigm, with contrastive learning methods showing remarkable success in computer vision tasks. Meta-learning approaches like MAML have enabled few-shot learning capabilities, allowing models to quickly adapt to new tasks with minimal data.

**Privacy and Security**: There's growing emphasis on privacy-preserving machine learning, with federated learning and differential privacy becoming standard practices. Adversarial robustness research has produced certified defense methods that provide formal guarantees against attacks.

These advances collectively point toward more efficient, adaptable, and secure machine learning systems that can operate effectively in diverse real-world scenarios while respecting privacy constraints.`,
      processing_info: {
        total_passages: 1247,
        selected_quotes: 9,
        themes_generated: 4,
        papers_used: 156,
      },
    },
    finding_info: {
      total_passages_found: 1247,
      passages_used_for_qa: 156,
    },
  }
}
