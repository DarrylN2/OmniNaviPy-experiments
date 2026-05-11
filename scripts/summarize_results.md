# Summarize Evaluation Results

This script summarizes OmniNaviPy evaluation result folders into a readable table.

It is useful after running navigation evaluations because it collects important information from each result folder, such as the agent type, MLLM model, accuracy, number of saved episodes, and whether image or checkpoint files exist.

The summary script now includes a Difficulty column. Current result folders show N/A because difficulty is not saved directly in metrics.json or episodes.p. A possible future improvement is to save experiment metadata such as n_difficulties, n_per_difficulty, seed, agent_type, and mllm_model into metrics.json during evaluation.

## Usage

From the root of the repository, run:

```bash
python3 scripts/summarize_results.py