# ScholarQABench Evaluation System

This system provides comprehensive evaluation tools for your QA system using the ScholarQABench dataset.

## Overview

The evaluation pipeline consists of three main steps:

1. **Data Processing**: Extract key ingredients from metadata
2. **QA Results Generation**: Call your QA system to generate answers
3. **Evaluation**: Use GPT-4o to evaluate the quality of answers

## File Structure

```
evaluation/ScholarQABench-base/
├── original/
│   ├── qa_metadata_all (1).jsonl    # Original metadata
│   └── output_snippets.jsonl         # Extracted snippets
├── key_ingredients/                  # Generated requirements
│   ├── 1_1.txt, 1_2.txt            # Question 1 requirements
│   ├── 2_1.txt, 2_2.txt            # Question 2 requirements
│   └── ...
├── qa_nlp.jsonl                     # 33 NLP questions (provided)
├── qa_results.jsonl                 # System answers (generated)
└── qa_evaluations.jsonl             # Evaluation results (generated)
```

## Scripts

### 1. `process_scholarqa_data.py`
Extracts key ingredients from metadata and creates requirement files.

**Usage:**
```bash
python process_scholarqa_data.py
```

**Output:** Creates `key_ingredients/` directory with files like `{idx}_{1|2}.txt`

### 2. `generate_qa_results.py`
Calls your QA system API to generate answers for all questions.

**Usage:**
```bash
python generate_qa_results.py
```

**Requirements:**
- Your QA system must be running on `http://localhost:8000`
- API endpoint `/qa` must be available

**Output:** Creates `qa_results.jsonl` with system answers

### 3. `generate_qa_evaluations_updated.py`
Uses GPT-4o to evaluate the quality of system answers.

**Usage:**
```bash
export OPENAI_API_KEY='your-api-key'
python generate_qa_evaluations_updated.py
```

**Output:** Creates `qa_evaluations.jsonl` with evaluation scores

### 4. `run_evaluation_pipeline.py`
Runs the complete evaluation pipeline.

**Usage:**
```bash
python run_evaluation_pipeline.py
```

### 5. `check_evaluation_results_updated.py`
Analyzes and displays evaluation results.

**Usage:**
```bash
python check_evaluation_results_updated.py
```

## API Integration

The system integrates with your existing QA API:

### Main API Endpoint: `/qa`
**Request:**
```json
{
    "query": "What is machine learning?",
    "limit": 50,
    "max_themes": 5,
    "model": null
}
```

**Response:**
```json
{
    "original_query": "What is machine learning?",
    "rewritten_query": "...",
    "qa_result": {
        "query": "What is machine learning?",
        "filtered_passages": ["passage1", "passage2", ...],
        "themes": [
            {
                "name": "Introduction/Background",
                "quotes": ["quote1", "quote2", ...]
            }
        ],
        "final_report": "Comprehensive answer...",
        "processing_info": {...}
    },
    "finding_info": {...},
    "pipeline_info": {...}
}
```

## Evaluation Metrics

The system evaluates answers on multiple dimensions:

### Answer Evaluation
- **correctness_score** (0-1): Accuracy of information
- **coverage_score** (0-1): Coverage of requirements
- **reasoning_score** (0-1): Quality of reasoning

### Passages Evaluation  
- **relevance_score** (0-1): Relevance to question
- **completeness_score** (0-1): Completeness of information

### Performance Metrics
- **elapsed_time_sec**: Response time
- **time_feedback**: "fast" (< 10s), "acceptable" (10-30s), or "slow" (> 30s)

## Key Ingredients Structure

### `{idx}_1.txt` - Most Important Requirements
Contains **mandatory** requirements that answers must include:
- Supporting quotes from documents
- Specific information that must be covered
- Critical details for answering the question

### `{idx}_2.txt` - Nice to Have Requirements  
Contains **optional** requirements that enhance answers:
- Additional context
- Supplementary information
- Nice-to-have details

## Usage Examples

### 1. Complete Evaluation Pipeline
```bash
# Step 1: Extract key ingredients
python process_scholarqa_data.py

# Step 2: Start your QA system
# (Make sure your QA API is running on localhost:8000)

# Step 3: Generate answers
python generate_qa_results.py

# Step 4: Evaluate answers (requires OpenAI API key)
export OPENAI_API_KEY='your-api-key'
python generate_qa_evaluations_updated.py

# Step 5: Check results
python check_evaluation_results_updated.py
```

### 2. Automated Pipeline
```bash
# Run everything automatically
python run_evaluation_pipeline.py
```

### 3. Check Results
```bash
python check_evaluation_results_updated.py
```

## Requirements

### System Requirements
- Python 3.8+
- Your QA system running on `http://localhost:8000`
- OpenAI API key for evaluation

### Python Dependencies
```bash
pip install requests openai pathlib
```

### Environment Variables
```bash
export OPENAI_API_KEY='your-openai-api-key'
```

## Output Files

### `qa_results.jsonl`
Each line contains:
```json
{
    "idx": 1,
    "question": "What is machine learning?",
    "response": {
        "qa_result": {
            "final_report": "Answer text...",
            "filtered_passages": ["passage1", "passage2"],
            "themes": [...]
        }
    },
    "elapsed_time_sec": 15.2
}
```

### `qa_evaluations.jsonl`
Each line contains:
```json
{
    "idx": 1,
    "key_ingredients_id": "1",
    "system_final_report": "Answer text...",
    "evidence": "Key ingredients text...",
    "evaluation": {
        "answer_evaluation": {
            "correctness_score": 0.85,
            "coverage_score": 0.90,
            "reasoning_score": 0.80,
            "summary": "Good answer with minor gaps"
        },
        "passages_evaluation": {
            "relevance_score": 0.88,
            "completeness_score": 0.85,
            "summary": "Relevant passages selected"
        },
        "time_feedback": "acceptable"
    }
}
```

## Troubleshooting

### Common Issues

1. **API Connection Error**
   - Ensure your QA system is running on `http://localhost:8000`
   - Check the `/health` endpoint

2. **OpenAI API Error**
   - Verify your API key: `export OPENAI_API_KEY='your-key'`
   - Check API quota and billing

3. **Missing Files**
   - Run `process_scholarqa_data.py` first to create key_ingredients
   - Ensure `qa_nlp.jsonl` exists in the directory

4. **Evaluation Errors**
   - Check GPT-4o response format
   - Verify JSON parsing in evaluation script

### Debug Mode
Add debug prints to scripts to see detailed processing information.

## Performance Notes

- **QA Results**: ~2-5 minutes for 33 questions
- **Evaluations**: ~10-15 minutes for 66 evaluations (33 questions × 2 key_ingredients)
- **Total Time**: ~15-20 minutes for complete pipeline

## Next Steps

1. **Customize Evaluation**: Modify prompts in `generate_qa_evaluations_updated.py`
2. **Add Metrics**: Include additional evaluation dimensions
3. **Batch Processing**: Optimize for larger datasets
4. **Visualization**: Create charts and reports from results

