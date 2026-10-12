# LexIntel-AI Evaluation Figures

Run the plotting script from any working directory:

```bash
cd backend
python evaluation/plots.py
```

The six 300-DPI PNG images are written to
`backend/evaluation/generated_plots/`. The output directory can be changed with
`--output-dir`. The similarity histogram is a reproducible synthetic
illustration (default: 1,000 scores and random seed 42), not a benchmark result.
The other plotted metric values are the fixed comparison values specified for
the project report; they should not be interpreted as output from a new
evaluation run.

## Section 7 placement

| Image | Suggested report subsection | Purpose |
| --- | --- | --- |
| `precision_recall.png` | 7.2 Retrieval Evaluation | Shows precision and recall together for Keyword Search, Semantic Search, and Hybrid Retrieval. |
| `similarity_distribution.png` | 7.2 Retrieval Evaluation | Illustrates the distribution of similarity scores in the 0.4–1.0 range. The synthetic nature of the data should remain clear in the caption. |
| `retrieval_comparison.png` | 7.2 Retrieval Evaluation | Compares the supplied precision and recall scores for the three retrieval configurations. |
| `response_quality_radar.png` | 7.4 Response Quality Analysis | Summarizes the supplied accuracy, relevance, completeness, clarity, and grounding scores. |
| `citation_accuracy.png` | 7.3 Response Evaluation | Shows the supplied citation-accuracy values across pipeline versions. |
| `rag_latency.png` | 7.6 Final System Performance | Displays the supplied retrieval and LLM-generation latency components and their combined total. |

Install the plotting dependencies from the backend dependency manifest before
running the script:

```bash
python -m pip install -r requirements.txt
```
