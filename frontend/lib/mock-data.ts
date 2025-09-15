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
        {
          paper_id: "arxiv:2023.12345",
          title: "Transformer Architecture Improvements for Large Language Models",
          evidence:
            "Recent advances in transformer architectures have shown significant improvements in computational efficiency and model performance. The introduction of sparse attention mechanisms reduces computational complexity from O(n²) to O(n log n).",
          cross_score: 0.92,
          final_score: 0.89,
        },
        {
          paper_id: "arxiv:2023.67890",
          title: "Self-Supervised Learning in Computer Vision: A Comprehensive Survey",
          evidence:
            "Self-supervised learning has emerged as a powerful paradigm that leverages unlabeled data to learn meaningful representations. Methods like contrastive learning and masked image modeling have achieved state-of-the-art results.",
          cross_score: 0.88,
          final_score: 0.85,
        },
        {
          paper_id: "arxiv:2024.11111",
          title: "Federated Learning with Differential Privacy: Challenges and Solutions",
          evidence:
            "Federated learning enables training machine learning models across decentralized data sources while preserving privacy. Recent work addresses communication efficiency and convergence guarantees in heterogeneous environments.",
          cross_score: 0.85,
          final_score: 0.82,
        },
      ],
      themes: [
        {
          theme_name: "Architectural Innovations",
          quotes: [
            {
              paper_id: "arxiv:2023.12345",
              title: "Transformer Architecture Improvements for Large Language Models",
              evidence:
                "The introduction of sparse attention mechanisms reduces computational complexity while maintaining model expressiveness.",
              cross_score: 0.92,
            },
            {
              paper_id: "arxiv:2024.22222",
              title: "Efficient Neural Network Architectures for Edge Computing",
              evidence:
                "Novel pruning techniques and quantization methods enable deployment of sophisticated models on resource-constrained devices.",
              cross_score: 0.87,
            },
          ],
        },
        {
          theme_name: "Learning Paradigms",
          quotes: [
            {
              paper_id: "arxiv:2023.67890",
              title: "Self-Supervised Learning in Computer Vision: A Comprehensive Survey",
              evidence:
                "Contrastive learning methods have revolutionized representation learning by maximizing agreement between differently augmented views of the same data.",
              cross_score: 0.88,
            },
            {
              paper_id: "arxiv:2024.33333",
              title: "Meta-Learning for Few-Shot Classification",
              evidence:
                "Model-agnostic meta-learning (MAML) enables rapid adaptation to new tasks with minimal training examples.",
              cross_score: 0.84,
            },
          ],
        },
        {
          theme_name: "Privacy and Security",
          quotes: [
            {
              paper_id: "arxiv:2024.11111",
              title: "Federated Learning with Differential Privacy: Challenges and Solutions",
              evidence:
                "Differential privacy mechanisms provide formal guarantees about individual data point privacy while enabling collaborative learning.",
              cross_score: 0.85,
            },
            {
              paper_id: "arxiv:2024.44444",
              title: "Adversarial Robustness in Deep Neural Networks",
              evidence:
                "Certified defense methods provide provable guarantees against adversarial attacks within specified threat models.",
              cross_score: 0.81,
            },
          ],
        },
      ],
      final_report: `Based on the analysis of recent research papers, several key advances in machine learning have emerged:

**Architectural Innovations**: The field has seen significant improvements in neural network architectures, particularly in transformer models. Sparse attention mechanisms have reduced computational complexity while maintaining performance, making large language models more efficient. Additionally, novel architectures designed for edge computing enable deployment of sophisticated models on resource-constrained devices.

**Learning Paradigms**: Self-supervised learning has become a dominant paradigm, with contrastive learning methods showing remarkable success in computer vision tasks. Meta-learning approaches like MAML have enabled few-shot learning capabilities, allowing models to quickly adapt to new tasks with minimal data.

**Privacy and Security**: There's growing emphasis on privacy-preserving machine learning, with federated learning and differential privacy becoming standard practices. Adversarial robustness research has produced certified defense methods that provide formal guarantees against attacks.

These advances collectively point toward more efficient, adaptable, and secure machine learning systems that can operate effectively in diverse real-world scenarios while respecting privacy constraints.`,
      processing_info: {
        papers_found: 1247,
        quotes_selected: 156,
        themes_generated: 3,
        processing_time: 12.4,
      },
    },
    finding_info: {
      total_passages_found: 1247,
      passages_used_for_qa: 156,
    },
  }
}
