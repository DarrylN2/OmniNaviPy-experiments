# Analyze Episodes Script

## Overview

`scripts/analyze_episodes.py` is a utility script for analyzing individual saved evaluation episodes in OmniNaviPy.

While `summarize_results.py` summarizes each result folder, this script goes deeper and summarizes each episode inside `episodes.p`.

This is useful for understanding why certain runs succeed or fail, and whether the MLLM waypoint logic was actually triggered during an episode.

---

## Purpose

The main goal of this script is to inspect saved evaluation episodes and answer questions such as:

- Which episodes failed?
- What was the termination reason?
- How many steps did each episode take?
- Was the MLLM called?
- How many waypoints were generated?
- How far was the final position from the target?
- Did the MLLM help with the failed episode?

This is especially useful for analyzing waypoint-based MLLM behavior.

---

## How to run

From the root of the repository, run:

```bash
python3 scripts/analyze_episodes.py
```

This will analyze all result folders inside:

```bash
ignore/results/
```

and print a summary table in the terminal.

---

## Save results to CSV

To save the per-episode analysis to a CSV file, run:

```bash
python3 scripts/analyze_episodes.py --csv ignore/episode_summary.csv
```

The CSV file can be opened in a spreadsheet for easier comparison.

---

## Useful command options

### Analyze only failed episodes

```bash
python3 scripts/analyze_episodes.py --failures-only
```

This is useful for quickly finding which episodes failed and why.

---

### Analyze only episodes where the MLLM was called

```bash
python3 scripts/analyze_episodes.py --mllm-only
```

This is useful for checking whether the MLLM waypoint logic was triggered.

---

### Analyze one result folder

```bash
python3 scripts/analyze_episodes.py --run-folder Agent_DataMap__MLLM_gemma3_27b__small_10x1
```

This is useful when focusing on one specific experiment run.

---

### Limit number of printed rows

```bash
python3 scripts/analyze_episodes.py --max-rows 50
```

By default, the script only prints the first 30 rows in the terminal.

---

## What files the script reads

For each result folder, the script reads:

```bash
episodes.p
```

This file contains saved episode objects from an evaluation run.

The script does not modify the saved experiment results. It only reads them.

---

## Summary output

The script first prints a general summary, such as:

```text
Episode Analysis Summary
------------------------
Total episodes:              134
Successes:                   126
Failures:                    8
Success rate:                94.03%
Episodes with MLLM calls:    1
Episodes with waypoints:     1
Average steps:               16.75
Average final distance:      11.94
```

This gives a quick overview of all analyzed episodes.

---

## Table columns

The terminal table includes:

| Column | Meaning |
|---|---|
| `Run Folder` | The result folder the episode came from |
| `EpID` | Episode ID or path index |
| `Success` | Whether the episode reached the goal |
| `Termination` | Why the episode ended |
| `Steps` | Number of action steps in the episode |
| `MLLM` | Number of MLLM calls |
| `WP` | Number of generated waypoints |
| `FinalDist` | Final distance from the target |

---

## CSV columns

The CSV output includes more detailed information than the terminal table.

Important columns include:

| Column | Meaning |
|---|---|
| `run_folder` | Result folder name |
| `episode_id` | Episode ID |
| `agent` | Agent type, such as `DataMap` or `MicrosoftAirSim` |
| `mllm` | MLLM model used, such as `None` or `gemma3_27b` |
| `label` | Extra run label, such as `small_10x1` |
| `success` | Whether the episode reached the goal |
| `termination` | Termination reason |
| `n_steps` | Number of action steps |
| `n_path_points` | Number of saved path points |
| `n_waypoints` | Number of generated waypoints |
| `n_mllm_calls` | Number of MLLM calls |
| `generated_waypoints` | Waypoints parsed from MLLM responses |
| `strategies` | Strategy text parsed from MLLM responses |
| `final_distance_to_target` | Distance from final position to target |
| `start_x`, `start_y`, `start_z` | Starting position |
| `final_x`, `final_y`, `final_z` | Final position |
| `target_x`, `target_y`, `target_z` | Target position |

---

## How success is counted

An episode is counted as successful if its termination reason is:

```text
goal_reached
```

Any other termination reason is counted as a failure.

For example:

```text
max_steps_exceeded
```

means the robot did not reach the goal before the step limit.

---

## How MLLM calls are counted

The script checks the saved episode states for:

```text
high_level_policy_response
```

Each saved response is counted as one MLLM call.

The script also tries to parse waypoints from responses formatted like:

```text
[WAYPOINT]: (x, y)
```

This helps measure when the MLLM waypoint system was actually used.

---

## Example finding from current runs

Using:

```bash
python3 scripts/analyze_episodes.py --mllm-only
```

the current results showed:

```text
Agent_DataMap__MLLM_gemma3_27b__small_10x1
Episode 9
Success: False
Termination: max_steps_exceeded
Steps: 32
MLLM calls: 3
Waypoints: 3
Final distance: 50.0
```

This means the MLLM was triggered in episode 9 and generated 3 waypoints, but the episode still failed because it exceeded the maximum number of steps.

The non-MLLM version of the same small run also failed on episode 9:

```text
Agent_DataMap__MLLM_None__small_10x1
Episode 9
Success: False
Termination: max_steps_exceeded
Steps: 32
Final distance: 50.96
```

This suggests episode 9 may be a difficult trajectory where both the baseline and MLLM version struggle.

---

## Why this is useful for the project

This script helps move beyond only looking at final accuracy.

For example, a run might have the same accuracy with and without MLLM, but this script can show whether:

- the MLLM was never called
- the MLLM was called but did not help
- the MLLM generated waypoints in failed episodes
- failures happen because of max steps
- failures happen far from the target

This makes it easier to understand the behavior of the current waypoint system before changing the main navigation pipeline.

---

## Relationship to `summarize_results.py`

The two scripts are complementary:

```text
summarize_results.py
    summarizes each result folder

analyze_episodes.py
    summarizes each episode inside each result folder
```

A typical workflow is:

```bash
python3 scripts/summarize_results.py
python3 scripts/analyze_episodes.py
python3 scripts/analyze_episodes.py --failures-only
python3 scripts/analyze_episodes.py --mllm-only
```

---

## Possible future improvements

Possible next steps include:

1. Add a `--details` flag to print generated waypoints and strategy text in the terminal.
2. Add success rate comparison for episodes with MLLM calls vs without MLLM calls.
3. Add success rate comparison for episodes with waypoints vs without waypoints.
4. Add per-run summary grouped by result folder.
5. Add sorting options, such as sorting by final distance or step count.
6. Add a simple plot or visualization of failed episodes.
7. Add waypoint quality checks, such as repeated waypoints or waypoints far from safe areas.
8. Compare the same episode ID between MLLM and non-MLLM runs.

---

## Files added

Main script:

```bash
scripts/analyze_episodes.py
```

Documentation:

```bash
scripts/analyze_episodes.md
```

Optional local CSV output:

```bash
ignore/episode_summary.csv
```

The CSV output is saved under `ignore/`, so it is intended as a local analysis file and usually does not need to be committed.