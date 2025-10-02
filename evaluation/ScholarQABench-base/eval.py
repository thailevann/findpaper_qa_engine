import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from fpdf import FPDF
from IPython.display import display

# ==============================
# 1. Load and prepare data
# ==============================
file_path = "qa_evaluations.jsonl"

# Load JSONL into dataframe
data = []
with open(file_path, 'r', encoding='utf-8') as f:
    for line in f:
        record = json.loads(line.strip())
        metrics = record.get("metrics", {})
        data.append({
            "idx": record.get("idx"),
            "key_ingredients_id": record.get("key_ingredients_id"),
            "question": record.get("rewritten_query"),
            "correctness_score": metrics.get("correctness_score"),
            "coverage_score": metrics.get("coverage_score"),
            "reasoning_score": metrics.get("reasoning_score"),
            "relevance_score": metrics.get("relevance_score"),
            "completeness_score": metrics.get("completeness_score"),
            "answer_quality_score": metrics.get("answer_quality_score"),
            "passage_quality_score": metrics.get("passage_quality_score"),
            "overall_quality_score": metrics.get("overall_quality_score"),
            "elapsed_time_sec": metrics.get("elapsed_time_sec"),
            "time_efficiency_score": metrics.get("time_efficiency_score"),
            "quality_efficiency_score": metrics.get("quality_efficiency_score"),
            "overall_quality_category": metrics.get("overall_quality_category"),
            "time_category": metrics.get("time_category")
        })

df = pd.DataFrame(data)
print("Data loaded:", df.shape)
display(df.head())

# ==============================
# 2. Task 1 - Quality Analysis
# ==============================
output_dir = Path("analysis_outputs")
output_dir.mkdir(exist_ok=True)

# Histogram of main scores
score_cols = [
    "correctness_score", "coverage_score", "reasoning_score",
    "relevance_score", "completeness_score", "overall_quality_score"
]

for col in score_cols:
    plt.figure(figsize=(8, 5))
    sns.histplot(df[col], bins=10, kde=True)
    plt.title(f"Distribution of {col}")
    plt.xlabel(col)
    plt.ylabel("Count")
    plt.tight_layout()
    plt.savefig(output_dir / f"{col}_distribution.png")
    plt.close()

# Top 10 worst answers
worst_answers = df.sort_values(by="overall_quality_score", ascending=True).head(10)
print("Top 10 worst answers:")
display(worst_answers[["idx", "question", "overall_quality_score"]])

# Top 10 passages with lowest relevance
worst_passages = df.sort_values(by="relevance_score", ascending=True).head(10)
print("Top 10 lowest relevance passages:")
display(worst_passages[["idx", "question", "relevance_score"]])

# ==============================
# 3. Task 2 - Pattern Detection via Clustering
# ==============================
features = df[["correctness_score", "coverage_score", "reasoning_score", "relevance_score", "completeness_score"]].fillna(0)

# Scale the features
scaler = StandardScaler()
scaled_features = scaler.fit_transform(features)

# Apply KMeans clustering
kmeans = KMeans(n_clusters=3, random_state=42)
df["error_cluster"] = kmeans.fit_predict(scaled_features)

# Visualize clustering results
plt.figure(figsize=(8, 6))
sns.scatterplot(
    data=df, x="correctness_score", y="coverage_score",
    hue="error_cluster", palette="Set2"
)
plt.title("Clustering of Answer Errors")
plt.tight_layout()
plt.savefig(output_dir / "clustering_results.png")
plt.close()

# Analyze cluster characteristics
cluster_summary = df.groupby("error_cluster")[["correctness_score", "coverage_score", "reasoning_score"]].mean()
print("Cluster Summary:")
display(cluster_summary)

# ==============================
# 4. Task 3 - Efficiency vs Quality
# ==============================
plt.figure(figsize=(8, 6))
sns.scatterplot(data=df, x="elapsed_time_sec", y="overall_quality_score", hue="overall_quality_category", palette="Set1")
plt.title("Efficiency vs Quality")
plt.xlabel("Elapsed Time (sec)")
plt.ylabel("Overall Quality Score")
plt.tight_layout()
plt.savefig(output_dir / "efficiency_vs_quality.png")
plt.close()

# Correlation between time and quality
correlation = df["elapsed_time_sec"].corr(df["overall_quality_score"])
print(f"Correlation between time and quality: {correlation:.3f}")

# Identify problematic cases
slow_and_bad = df[(df["elapsed_time_sec"] > 30) & (df["overall_quality_score"] < 0.5)]
print("Slow and poor quality answers:")
display(slow_and_bad[["idx", "question", "elapsed_time_sec", "overall_quality_score"]])

# ==============================
# 5. Generate PDF Report
# ==============================
pdf = FPDF()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.add_page()
pdf.set_font("Arial", size=14)

pdf.cell(200, 10, txt="QA Evaluation Analysis Report", ln=True, align='C')

pdf.set_font("Arial", size=12)
pdf.ln(10)
pdf.cell(200, 10, txt=f"Total Evaluations: {len(df)}", ln=True)
pdf.cell(200, 10, txt=f"Average Overall Quality Score: {df['overall_quality_score'].mean():.3f}", ln=True)

pdf.ln(10)
pdf.cell(200, 10, txt="Cluster Analysis Summary:", ln=True)
for idx, row in cluster_summary.iterrows():
    pdf.cell(200, 8, txt=f"Cluster {idx}: Correctness={row['correctness_score']:.2f}, Coverage={row['coverage_score']:.2f}, Reasoning={row['reasoning_score']:.2f}", ln=True)

pdf.add_page()
pdf.cell(200, 10, txt="Figures", ln=True, align='C')

# Add some key figures
for img in [
    "overall_quality_score_distribution.png",
    "clustering_results.png",
    "efficiency_vs_quality.png"
]:
    img_path = output_dir / img
    if img_path.exists():
        pdf.image(str(img_path), x=10, w=180)
        pdf.ln(10)

pdf.output("analysis_report.pdf")

print("\nAnalysis completed! Outputs saved in:", output_dir)
