# Summarize Evaluation Results

This script summarizes OmniNaviPy evaluation result folders into a readable table.

It is useful after running navigation evaluations because it collects important information from each result folder, such as the agent type, MLLM model, accuracy, number of saved episodes, and whether image or checkpoint files exist.

## Usage

From the root of the repository, run:

```bash
python3 scripts/summarize_results.py