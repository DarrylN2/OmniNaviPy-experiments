# Summarize Evaluation Results

## Overview

`scripts/summarize_results.py` is a utility script for summarizing OmniNaviPy evaluation results.

After running navigation experiments, the project saves outputs into result folders under:

```bash
ignore/results/
```

Each result folder may contain files such as:

```bash
metrics.json
episodes.p
image_display.png
checkpoints/
```

This script scans the result folders and prints a readable summary table in the terminal. It can also export the same information to a CSV file for easier comparison.

The goal is to make it easier to compare different evaluation runs, such as:

```text
DataMap without MLLM
DataMap with MLLM
MicrosoftAirSim without MLLM
small test runs
larger evaluation runs
```

---

## Why this is useful

Manually checking each result folder can be slow, especially when there are many experiments.

This script helps quickly answer questions like:

- Which runs completed successfully?
- What accuracy did each run get?
- How many episodes were evaluated?
- How many episodes succeeded or failed?
- How many steps did episodes take on average?
- Was the MLLM actually called?
- How many waypoints were generated?
- What were the termination reasons?

This is useful for analyzing the current waypoint-based MLLM behavior.

For example, if an MLLM run has the same accuracy as the non-MLLM baseline, the summary can still show whether the MLLM was actually triggered during the run.

---

## How to run

From the root of the repository, run:

```bash
python3 scripts/summarize_results.py
```

This prints a summary table in the terminal.

To also save the summary as a CSV file, run:

```bash
python3 scripts/summarize_results.py --csv ignore/results_summary.csv
```

The CSV file can be opened in a spreadsheet or saved for later comparison.

---

## Optional arguments

### `--results-dir`

Use this if the result folders are stored somewhere other than `ignore/results`.

```bash
python3 scripts/summarize_results.py --results-dir path/to/results
```

### `--csv`

Use this to save the summary table as a CSV file.

```bash
python3 scripts/summarize_results.py --csv ignore/results_summary.csv
```

Both can be used together:

```bash
python3 scripts/summarize_results.py --results-dir ignore/results --csv ignore/results_summary.csv
```

---

## What files the script reads

For each result folder, the script checks for:

| File or folder | Purpose |
|---|---|
| `metrics.json` | Stores run-level metrics such as accuracy |
| `episodes.p` | Stores saved episode objects |
| `image_display.png` | Shows whether a display image was generated |
| `checkpoints/` | Shows whether checkpoint files were saved |

The script only reads these files. It does not modify experiment results.

---

## Folder naming format

The script expects result folders to follow a format like:

```text
Agent_DataMap__MLLM_None
Agent_DataMap__MLLM_gemma3_27b
Agent_DataMap__MLLM_None__small_10x1
Agent_DataMap__MLLM_gemma3_27b__small_10x1
Agent_MicrosoftAirSim__MLLM_None
```

From the folder name, the script extracts:

| Parsed value | Example |
|---|---|
| Agent | `DataMap` |
| MLLM | `None` or `gemma3_27b` |
| Label | `small_10x1`, `small_5x1`, or `N/A` |

The label is useful for marking smaller test runs or special experiment settings.

---

## Summary columns

The terminal table and CSV output include these columns:

| Column | Meaning |
|---|---|
| `folder` | Name of the result folder |
| `agent` | Agent type, such as `DataMap` or `MicrosoftAirSim` |
| `mllm` | MLLM model used, such as `None` or `gemma3_27b` |
| `label` | Extra label parsed from the folder name, such as `small_10x1` |
| `difficulty` | Difficulty information if found in saved episodes |
| `accuracy` | Accuracy loaded from `metrics.json` |
| `episodes` | Number of episodes loaded from `episodes.p` |
| `successes` | Number of episodes that ended with `goal_reached` |
| `failures` | Number of episodes that did not end with `goal_reached` |
| `avg_steps` | Average number of actions taken per episode |
| `avg_waypoints` | Average number of waypoints generated per episode |
| `episodes_with_waypoints` | Number of episodes that used at least one waypoint |
| `total_mllm_calls` | Total number of detected MLLM calls |
| `avg_mllm_calls` | Average number of MLLM calls per episode |
| `termination_reasons` | Count of termination reasons, such as `goal_reached` or `max_steps_exceeded` |
| `has_image` | Whether `image_display.png` exists |
| `has_checkpoints` | Whether a `checkpoints/` folder exists |
| `status` | Whether the result folder appears complete |

---

## How success and failure are counted

The script checks the `termination` value for each saved episode.

If the termination reason is:

```text
goal_reached
```

then the episode is counted as a success.

Any other termination reason is counted as a failure.

For example:

```text
goal_reached:9, max_steps_exceeded:1
```

means:

```text
9 successful episodes
1 failed episode due to max steps
```

---

## How MLLM calls are counted

The script checks each episode's saved `states`.

When the MLLM is called, the high-level policy stores a response in:

```text
high_level_policy_response
```

The script counts these saved responses as MLLM calls.

It also tries to parse generated waypoints from responses formatted like:

```text
[WAYPOINT]: (x, y)
```

This helps measure whether the MLLM waypoint logic was actually used during an evaluation run.

---

## Example interpretation

Example result:

```text
Agent_DataMap__MLLM_gemma3_27b__small_10x1
accuracy = 90.0
episodes = 10
successes = 9
failures = 1
avg_steps = 8.4
avg_waypoints = 0.3
episodes_with_waypoints = 1
total_mllm_calls = 3
termination_reasons = goal_reached:9, max_steps_exceeded:1
```

This means:

- The run used the `DataMap` agent.
- The run used the `gemma3_27b` MLLM.
- It evaluated 10 episodes.
- 9 episodes reached the goal.
- 1 episode failed because it exceeded the maximum number of steps.
- The MLLM was called 3 times total.
- At least one episode used a generated waypoint.
- The final accuracy was 90%.

This is useful because it shows that the MLLM was not active in every episode. It only triggered when the high-level policy detected that the robot was stuck.

---

## Current limitation with difficulty

The script includes a `difficulty` column, but current saved episodes may not directly store difficulty information.

Because of that, the difficulty column may show:

```text
N/A
```

This is expected for now.

A possible future improvement is to save experiment metadata during evaluation, such as:

```text
n_difficulties
n_per_difficulty
seed
agent_type
mllm_model
map_name
policy_name
```

This could make future result summaries more complete.

---

## Status meanings

| Status | Meaning |
|---|---|
| `Complete` | The result folder has readable metrics |
| `Missing metrics.json` | The result folder does not contain `metrics.json` |
| `Invalid metrics.json` | `metrics.json` exists but could not be read |

If `episodes.p` is missing or cannot be read, episode-level values may show as:

```text
N/A
```

---

## Files changed

Main script:

```bash
scripts/summarize_results.py
```

Documentation:

```bash
scripts/summarize_results.md
```

Generated local CSV output:

```bash
ignore/results_summary.csv
```

The CSV output is stored under `ignore/`, so it is meant as a local result file and usually does not need to be committed.

---

## How this relates to the MLLM waypoint project

The current MLLM logic is not called on every step. It is mainly triggered when the robot appears to be stuck.

This script helps analyze that behavior by reporting:

```text
total_mllm_calls
avg_mllm_calls
avg_waypoints
episodes_with_waypoints
termination_reasons
```

These metrics can help answer whether the MLLM is helping, not helping, or simply not being triggered often enough.

This is useful before making larger changes to the waypoint generation pipeline.

---

## Possible future improvements

Some possible next improvements are:

1. Add a per-episode CSV output where each row is one episode.
2. Add final distance to target for failed episodes.
3. Save generated waypoint coordinates in the CSV.
4. Compare success rate for episodes with waypoints vs episodes without waypoints.
5. Add command-line filters, such as only showing `DataMap` runs or only showing MLLM runs.
6. Save experiment metadata directly into `metrics.json`.
7. Add a short summary at the end comparing MLLM vs non-MLLM runs.
8. Add optional sorting by accuracy, agent, MLLM model, or label.

---

## Example workflow

A typical workflow could be:

```bash
python3 scripts/evaluate_navigation.py
python3 scripts/summarize_results.py
python3 scripts/summarize_results.py --csv ignore/results_summary.csv
```

Then compare the results across different experiment settings.

For example:

```text
DataMap + no MLLM
DataMap + gemma3_27b
MicrosoftAirSim + no MLLM
```

This makes it easier to track experiment results and decide what to test next.