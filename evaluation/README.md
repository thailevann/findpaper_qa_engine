# Evaluation Framework

This folder contains evaluation tools for the FindPaper QA Engine retriever.

## What's Here

### Core Evaluation Tools
- **`test_api_evaluation.py`** (in root) - Main evaluation script that works reliably
- **`generate_csv_report.py`** (in root) - CSV report generator

### Advanced Tools (Optional)
- **`ragas_evaluator.py`** - RAGAS-based evaluation (requires complex dependencies)
- **`simple_evaluator.py`** - Direct system evaluation (has dependency issues)
- **`retriever_analysis.py`** - Analysis and reporting tools

## Recommended Usage

### For Regular Evaluation
```bash
# Run the main evaluation (most reliable)
python test_api_evaluation.py

# Generate CSV reports
python generate_csv_report.py
```

### For Advanced Analysis
```bash
# If you have RAGAS dependencies installed
python evaluation/ragas_evaluator.py
```

## Why This Structure?

1. **Separation of Concerns** - Evaluation logic separate from main application
2. **Modularity** - Different evaluation approaches for different needs
3. **Extensibility** - Easy to add new evaluation metrics
4. **Reproducibility** - Standardized evaluation process

## Dependencies

- **Basic**: `requests`, `json`, `csv` (already available)
- **Advanced**: `ragas`, `pandas`, `numpy` (optional, for RAGAS evaluation)

## Future Improvements

1. **Simplify** - Focus on the working API-based evaluation
2. **Standardize** - Create consistent evaluation protocols
3. **Automate** - Add CI/CD integration for continuous evaluation
4. **Monitor** - Track performance trends over time
