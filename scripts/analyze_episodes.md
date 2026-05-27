# Analyze Episodes Script

## Overview

`scripts/analyze_episodes.py` is a utility script for analyzing individual saved evaluation episodes in OmniNaviPy.

While `summarize_results.py` summarizes each result folder, this script goes deeper and summarizes each episode inside `episodes.p`.

This is useful for understanding why certain runs succeed or fail, whether the MLLM waypoint logic was actually triggered during an episode, and whether the MLLM generated repeated waypoint suggestions.

---

## Purpose

The main goal of this script is to inspect saved evaluation episodes and answer questions such as:

- Which episodes failed?
- What was the termination reason?
- How many steps did each episode take?
- Was the MLLM called?
- How many waypoints were generated?
- Did the MLLM repeat waypoint suggestions?
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

For specific experiments, it can be useful to save the CSV with a more descriptive name:

```bash
python3 scripts/analyze_episodes.py --run-folder Agent_DataMap__MLLM_gemma3_27b__small_10x1__pt1_wp4_np5 --csv ignore/episode_summary_pt1_wp4_np5.csv
```

The CSV output is saved under `ignore/`, so it is intended as a local analysis file and usually does not need to be committed.

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
Total episodes:              10
Successes:                   9
Failures:                    1
Success rate:                90.0%
Episodes with MLLM calls:    2
Episodes with waypoints:     2
Episodes with repeated WPs:  1
Episodes with near repeats:  0
Average steps:               9.7
Average final distance:      10.43
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
| `RepWP` | Number of repeated waypoint occurrences |
| `FinalDist` | Final distance from the target |

Example:

```text
Run Folder                                      EpID   Success  Termination          Steps    MLLM   WP    RepWP  FinalDist
----------------------------------------------------------------------------------------------------------------------------------
Agent_DataMap__MLLM_gemma3_27b__small_10x1__p  5      True     goal_reached         24       3      3     0      8.0
Agent_DataMap__MLLM_gemma3_27b__small_10x1__p  9      False    max_steps_exceeded   32       6      6     4      50.96
```

This shows that episode 9 had repeated waypoint suggestions, while episode 5 did not.

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
| `n_waypoints_from_history` | Number of waypoints from `episode.waypoint_history` |
| `n_waypoints_from_response` | Number of parsed waypoints from MLLM responses |
| `n_mllm_calls` | Number of MLLM calls |
| `generated_waypoints` | Waypoints parsed from MLLM responses |
| `n_unique_waypoints` | Number of unique generated waypoints |
| `unique_waypoints` | Unique waypoint coordinates |
| `n_repeated_waypoints` | Number of repeated waypoint occurrences |
| `repeated_waypoints` | Waypoints that appeared more than once |
| `has_repeated_waypoints` | Whether exact repeated waypoints were found |
| `n_near_repeated_waypoints` | Number of waypoints close to earlier different waypoints |
| `near_repeated_waypoints` | Near-repeated waypoint coordinates |
| `has_near_repeated_waypoints` | Whether near-repeated waypoints were found |
| `near_repeat_threshold` | Distance threshold used for near-repeat detection |
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

## Repeated waypoint analysis

The script checks whether the MLLM generated repeated or near-repeated waypoints.

### Exact repeated waypoints

An exact repeated waypoint happens when the same coordinate appears more than once.

Example:

```text
(-20, 22); (-15, 20); (-20, 22); (-20, 22); (-20, 22); (-20, 22)
```

The script reports:

```text
n_unique_waypoints = 2
unique_waypoints = (-20, 22); (-15, 20)
n_repeated_waypoints = 4
repeated_waypoints = (-20, 22) x5
has_repeated_waypoints = True
```

The first `(-20, 22)` is counted as the original suggestion. The next 4 occurrences are counted as repeated waypoint occurrences.

---

### Near-repeated waypoints

A near-repeated waypoint happens when a waypoint is close to an earlier different waypoint.

The default near-repeat threshold is:

```text
near_repeat_threshold = 3
```

This means a waypoint is counted as near-repeated if it is within 3 meters of an earlier different waypoint.

Exact repeats are counted separately and are not counted as near repeats.

This helps distinguish between:

```text
same exact waypoint repeated
```

and:

```text
different but very similar waypoint suggested
```

---

## Example finding from current runs

Using:

```bash
python3 scripts/analyze_episodes.py --run-folder Agent_DataMap__MLLM_gemma3_27b__small_10x1__pt1_wp4_np5 --mllm-only
```

the results showed:

```text
Episode Analysis Summary
------------------------
Total episodes:              2
Successes:                   1
Failures:                    1
Success rate:                50.0%
Episodes with MLLM calls:    2
Episodes with waypoints:     2
Episodes with repeated WPs:  1
Episodes with near repeats:  0
Average steps:               28.0
Average final distance:      29.48
```

Episode-level result:

```text
Episode 5
Success: True
Termination: goal_reached
Steps: 24
MLLM calls: 3
Waypoints: 3
Repeated waypoints: 0
Final distance: 8.0

Episode 9
Success: False
Termination: max_steps_exceeded
Steps: 32
MLLM calls: 6
Waypoints: 6
Repeated waypoints: 4
Final distance: 50.96
```

This suggests that episode 9 failed even though the MLLM was called several times. The repeated waypoint count shows that the MLLM mostly repeated the same waypoint instead of producing meaningfully different recovery suggestions.

---

## Why this is useful for the project

This script helps move beyond only looking at final accuracy.

For example, a run might have the same accuracy with and without MLLM, but this script can show whether:

- the MLLM was never called
- the MLLM was called but did not help
- the MLLM generated waypoints in failed episodes
- the MLLM repeated previous waypoint suggestions
- failures happen because of max steps
- failures happen far from the target

This makes it easier to understand the behavior of the current waypoint system before changing the main navigation pipeline.

The repeated-waypoint analysis is especially useful because more MLLM calls do not automatically mean better navigation. If the MLLM is called multiple times but keeps producing the same waypoint, the issue may be waypoint quality rather than trigger timing.

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

## Comparing trigger experiments

This script is useful for comparing controlled MLLM trigger experiments.

Example folders:

```text
Agent_DataMap__MLLM_None__small_10x1
Agent_DataMap__MLLM_gemma3_27b__small_10x1
Agent_DataMap__MLLM_gemma3_27b__small_10x1__pt1_wp4_np5
Agent_DataMap__MLLM_gemma3_27b__small_10x1__pt3_wp4_np8
```

A useful workflow is:

```bash
python3 scripts/analyze_episodes.py --run-folder Agent_DataMap__MLLM_gemma3_27b__small_10x1__pt1_wp4_np5
python3 scripts/analyze_episodes.py --run-folder Agent_DataMap__MLLM_gemma3_27b__small_10x1__pt1_wp4_np5 --mllm-only
python3 scripts/analyze_episodes.py --run-folder Agent_DataMap__MLLM_gemma3_27b__small_10x1__pt1_wp4_np5 --failures-only
python3 scripts/analyze_episodes.py --run-folder Agent_DataMap__MLLM_gemma3_27b__small_10x1__pt1_wp4_np5 --csv ignore/episode_summary_pt1_wp4_np5.csv
```

Important questions to check:

- Did the failed episode become successful?
- Did the final distance improve?
- Did the MLLM get called earlier or more often?
- Did the generated waypoints help, or did they make the episode worse?
- Did the MLLM repeat waypoint suggestions?
- Did any previously successful episodes fail after changing the trigger settings?

---

## Possible future improvements

Possible next steps include:

1. Add a `--details` flag to print generated waypoints and strategy text in the terminal.
2. Add success rate comparison for episodes with MLLM calls vs without MLLM calls.
3. Add success rate comparison for episodes with waypoints vs without waypoints.
4. Add per-run summary grouped by result folder.
5. Add sorting options, such as sorting by final distance, step count, or repeated waypoint count.
6. Add a simple plot or visualization of failed episodes.
7. Add waypoint quality checks, such as repeated waypoints or waypoints far from safe areas.
8. Compare the same episode ID between MLLM and non-MLLM runs.
9. Add a filter such as `--repeated-waypoints-only`.
10. Add a configurable near-repeat threshold argument.

---

## Files added or changed

Main script:

```bash
scripts/analyze_episodes.py
```

Documentation:

```bash
scripts/analyze_episodes.md
```

Optional local CSV output examples:

```bash
ignore/episode_summary.csv
ignore/episode_summary_pt1_wp4_np5.csv
```

The CSV output is saved under `ignore/`, so it is intended as a local analysis file and usually does not need to be committed.