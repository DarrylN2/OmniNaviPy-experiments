# Prompt and Parameter Experiment Notes

## Goal

This note tracks small prompt and parameter experiments for the MLLM waypoint logic in OmniNaviPy.

The goal is to understand the AI-side behavior before changing the main navigation logic, model, or perception pipeline.

Current focus:

```text
When should the MLLM be called?
```

The easiest controlled experiment is changing the MLLM stuck-detection parameters instead of changing the model or prompt first.

---

## Main Prompt Location

The MLLM prompt appears to be built in:

```text
modules/Other.py
```

Important sections found through `grep`:

- `modules/Other.py:296-364`
  - Builds the prompt string sent to the MLLM.
- `modules/Other.py:363`
  - Queries the MLLM with the generated prompt.
- `modules/Other.py:382`
  - Parses waypoint coordinates from the MLLM response.
- `modules/Other.py:411`
  - Defines the `chat()` function used to communicate with the MLLM.

---

## What the Prompt Seems To Do

The prompt tells the MLLM that it is supervising a robot that is trying to navigate to a target position.

The prompt includes information such as:

- The robot's current position
- The target position
- The start position
- The robot's path history
- Previously attempted waypoints
- Previous strategy reasoning
- A map/image representation of the current robot state

The prompt also explains the map colors:

- White pixels are obstacles.
- Black space is safe.
- Gray pixels are unknown.

The MLLM is asked to generate a safe intermediate waypoint that helps the robot get unstuck and make progress toward the target.

---

## Expected MLLM Output Format

The prompt asks the MLLM to respond in this format:

```text
[STRATEGY]: reason for generating the waypoint. [WAYPOINT]: (x, y).
```

The waypoint parser expects the response to contain:

```text
[WAYPOINT]: (x, y)
```

If the output does not follow the expected format, the waypoint may not be parsed correctly.

---

## Relevant Trigger Parameters

The high-level MLLM waypoint logic is controlled mainly by these parameters:

| Parameter | Meaning |
|---|---|
| `progress_threshold` | Minimum progress toward the target required over the recent path window |
| `waypoint_threshold` | Distance needed to consider a waypoint reached |
| `n_points` | Number of recent path points used to check whether the drone is stuck |
| `pause_after_waypoint` | Whether to pause MLLM checks after a waypoint is generated |

The stuck detector checks whether the drone has made enough progress toward the target over the last `n_points`.

In simple terms:

- Higher `progress_threshold` makes the stuck detector more sensitive.
- Lower `n_points` makes the MLLM check for stuck behavior earlier.
- Higher `n_points` makes the MLLM wait longer before deciding the drone is stuck.
- `pause_after_waypoint=True` helps avoid repeatedly calling the MLLM too quickly.

---

## Completed Quick Experiments

Early small tests:

| Experiment | Agent | MLLM | Episodes | Accuracy | Notes |
|---|---|---|---:|---:|---|
| 1x1 baseline | DataMap | None | 1 | 100% | Quick baseline run |
| 1x1 MLLM | DataMap | gemma3:27b | 1 | 100% | Did not necessarily trigger MLLM waypoint generation |
| 5x1 baseline | DataMap | None | 5 | 100% | Small baseline run |
| 5x1 MLLM | DataMap | gemma3:27b | 5 | 100% | Small MLLM run |
| 10x1 baseline | DataMap | None | 10 | 90% | Larger quick baseline |
| 10x1 MLLM | DataMap | gemma3:27b | 10 | 90% | MLLM waypoint generation was triggered |

---

## MLLM Bug Found

During the 10x1 DataMap + gemma3:27b run, the evaluation reached the MLLM waypoint generation path and initially failed because `ollama` was not available/imported.

Smaller MLLM runs did not expose this issue because they likely completed without triggering waypoint generation.

After fixing the Ollama import/package issue, the MLLM run completed successfully and generated waypoint responses.

---

## Baseline: DataMap without MLLM

Run folder:

```text
Agent_DataMap__MLLM_None__small_10x1
```

Settings:

| Parameter | Value |
|---|---|
| `agent_type` | `DataMap` |
| `mllm_model` | `None` |
| `n_per_difficulty` | 10 |
| `n_difficulties` | 1 |
| `seed` | 777 |

Result:

| Metric | Value |
|---|---:|
| Accuracy | 90.0% |
| Episodes | 10 |
| Successes | 9 |
| Failures | 1 |
| MLLM calls | 0 |
| Episodes with waypoints | 0 |

Important finding:

Episode 9 failed:

```text
termination = max_steps_exceeded
final distance ≈ 50.96
```

Interpretation:

Episode 9 appears to be a difficult trajectory even without MLLM.

---

## Baseline: DataMap with Default MLLM Trigger

Run folder:

```text
Agent_DataMap__MLLM_gemma3_27b__small_10x1
```

Settings:

| Parameter | Value |
|---|---|
| `agent_type` | `DataMap` |
| `mllm_model` | `gemma3:27b` |
| `progress_threshold` | 1 |
| `waypoint_threshold` | 4 |
| `n_points` | 8 |
| `pause_after_waypoint` | True |
| `n_per_difficulty` | 10 |
| `n_difficulties` | 1 |
| `seed` | 777 |

Result:

| Metric | Value |
|---|---:|
| Accuracy | 90.0% |
| Episodes | 10 |
| Successes | 9 |
| Failures | 1 |
| Episodes with MLLM calls | 1 |
| Episodes with waypoints | 1 |
| Total MLLM calls | 3 |
| Average steps | 8.4 |
| Average waypoints | 0.3 |

Important finding:

The MLLM only triggered in episode 9.

Episode 9 still failed:

```text
termination = max_steps_exceeded
steps = 32
MLLM calls = 3
waypoints = 3
final distance ≈ 50.0
```

Interpretation:

The default MLLM trigger activated on the hard episode, but it did not solve the failure.

---

## Experiment 1: Earlier Trigger Using Smaller `n_points`

Run folder:

```text
Agent_DataMap__MLLM_gemma3_27b__small_10x1__pt1_wp4_np5
```

Settings:

| Parameter | Value |
|---|---|
| `agent_type` | `DataMap` |
| `mllm_model` | `gemma3:27b` |
| `progress_threshold` | 1 |
| `waypoint_threshold` | 4 |
| `n_points` | 5 |
| `pause_after_waypoint` | True |
| `n_per_difficulty` | 10 |
| `n_difficulties` | 1 |
| `seed` | 777 |

Command:

```bash
python3 scripts/evaluate_navigation_mllm_trigger.py
```

Analysis commands:

```bash
python3 scripts/summarize_results.py
python3 scripts/analyze_episodes.py --run-folder Agent_DataMap__MLLM_gemma3_27b__small_10x1__pt1_wp4_np5
python3 scripts/analyze_episodes.py --run-folder Agent_DataMap__MLLM_gemma3_27b__small_10x1__pt1_wp4_np5 --mllm-only
python3 scripts/analyze_episodes.py --run-folder Agent_DataMap__MLLM_gemma3_27b__small_10x1__pt1_wp4_np5 --failures-only
```

Result:

| Metric | Value |
|---|---:|
| Accuracy | 90.0% |
| Episodes | 10 |
| Successes | 9 |
| Failures | 1 |
| Episodes with MLLM calls | 2 |
| Episodes with waypoints | 2 |
| Total MLLM calls | 9 |
| Average steps | 9.7 |
| Average waypoints | 0.9 |
| Average final distance | 10.43 |

Episode-level observations:

| Episode | Success | Termination | Steps | MLLM calls | Waypoints | Final distance |
|---|---|---|---:|---:|---:|---:|
| 5 | True | `goal_reached` | 24 | 3 | 3 | 8.0 |
| 9 | False | `max_steps_exceeded` | 32 | 6 | 6 | 50.96 |

Comparison with default MLLM trigger:

| Setting | Accuracy | Episodes with MLLM calls | Total MLLM calls | Average steps |
|---|---:|---:|---:|---:|
| Default MLLM, `pt1_wp4_np8` | 90.0% | 1 | 3 | 8.4 |
| Earlier trigger, `pt1_wp4_np5` | 90.0% | 2 | 9 | 9.7 |

Interpretation:

Reducing `n_points` from 8 to 5 made the stuck detector trigger more often.

The MLLM became more active, but the accuracy did not improve.

Episode 9 still failed. The MLLM was called more times on episode 9, but the final distance stayed around 50.96.

Episode 5 is also interesting because it succeeded but required 24 steps and 3 MLLM calls. This may mean the smaller `n_points` value caused the MLLM to intervene in an episode that may not have needed help.

Conclusion:

```text
Using n_points = 5 made the trigger more sensitive, but it did not improve success rate.
It increased MLLM calls from 3 to 9 and did not fix the hard failed episode.
This setting may be too sensitive.
```

### Generated waypoints for MLLM-triggered episodes

For `pt1_wp4_np5`, the MLLM was triggered in episodes 5 and 9.

Episode 5 succeeded:

```text
steps = 24
MLLM calls = 3
waypoints = 3
final distance = 8.0
generated waypoints = (25, 69); (28, 65); (34, 66)
```

The strategy text repeatedly suggested moving to the right around a complex obstacle. This episode eventually reached the goal, but it required more steps than the other successful episodes.

Episode 9 failed:

```text
termination = max_steps_exceeded
steps = 32
MLLM calls = 6
waypoints = 6
final distance = 50.96
generated waypoints = (-20, 22); (-15, 20); (-20, 22); (-20, 22); (-20, 22); (-20, 22)
```

The MLLM mostly repeated the same waypoint `(-20, 22)`.

Observation:

Reducing `n_points` from 8 to 5 caused the MLLM to trigger more often, but the extra calls did not fix episode 9. In the failed episode, the generated waypoints were repetitive, suggesting that simply calling the MLLM more often may not be enough.

Interpretation:

The problem may be waypoint quality rather than only stuck-detection timing. A future improvement could check for repeated waypoints or modify the prompt to ask for a substantially different waypoint when previous suggestions failed.

---

## Experiment 2: Higher `progress_threshold` With Original `n_points`

Run folder:

```text
Agent_DataMap__MLLM_gemma3_27b__small_10x1__pt3_wp4_np8
```

Settings:

| Parameter | Value |
|---|---|
| `agent_type` | `DataMap` |
| `mllm_model` | `gemma3:27b` |
| `progress_threshold` | 3 |
| `waypoint_threshold` | 4 |
| `n_points` | 8 |
| `pause_after_waypoint` | True |
| `n_per_difficulty` | 10 |
| `n_difficulties` | 1 |
| `seed` | 777 |

Command:

```bash
python3 scripts/evaluate_navigation_mllm_trigger.py
```

Analysis commands:

```bash
python3 scripts/summarize_results.py
python3 scripts/analyze_episodes.py --run-folder Agent_DataMap__MLLM_gemma3_27b__small_10x1__pt3_wp4_np8
python3 scripts/analyze_episodes.py --run-folder Agent_DataMap__MLLM_gemma3_27b__small_10x1__pt3_wp4_np8 --mllm-only
python3 scripts/analyze_episodes.py --run-folder Agent_DataMap__MLLM_gemma3_27b__small_10x1__pt3_wp4_np8 --failures-only
```

Result:

| Metric | Value |
|---|---:|
| Accuracy | 90.0% |
| Episodes | 10 |
| Successes | 9 |
| Failures | 1 |
| Episodes with MLLM calls | 1 |
| Episodes with waypoints | 1 |
| Average steps | 8.4 |
| Average final distance | 9.94 |
| Total MLLM calls | 3 |

Episode-level observation:

| Episode | Success | Termination | Steps | MLLM calls | Waypoints | Final distance |
|---|---|---|---:|---:|---:|---:|
| 9 | False | `max_steps_exceeded` | 32 | 3 | 3 | 50.0 |

Generated waypoints for episode 9:

```text
(-20, 22); (-18, 22); (-15, 22)
```

The strategy text was repetitive. The MLLM repeatedly described the robot as being stuck near a complex obstacle and suggested moving left or laterally to clear the obstacle.

Interpretation:

Increasing `progress_threshold` from 1 to 3 while keeping `n_points = 8` did not change the overall behavior compared with the default MLLM setting.

The MLLM still only triggered in episode 9, and episode 9 still failed with `max_steps_exceeded`.

Conclusion:

```text
Changing progress_threshold from 1 to 3 did not improve performance.
The issue may not only be when the MLLM is called.
The generated waypoint quality or the hard trajectory itself may need deeper analysis.
```

---

## Comparison Across Trigger Experiments

| Setting | Accuracy | Episodes with MLLM calls | Total MLLM calls | Average steps | Episode 9 result |
|---|---:|---:|---:|---:|---|
| Default MLLM, `pt1_wp4_np8` | 90.0% | 1 | 3 | 8.4 | Failed |
| Earlier trigger, `pt1_wp4_np5` | 90.0% | 2 | 9 | 9.7 | Failed |
| Higher threshold, `pt3_wp4_np8` | 90.0% | 1 | 3 | 8.4 | Failed |

Overall interpretation:

Changing the trigger parameters changed how often the MLLM was called, but it did not improve the success rate.

The `pt1_wp4_np5` setting caused more MLLM calls, but episode 9 still failed. The generated waypoints for episode 9 were repetitive:

```text
(-20, 22); (-15, 20); (-20, 22); (-20, 22); (-20, 22); (-20, 22)
```

This suggests that simply calling the MLLM more often is not enough.

Main finding:

```text
More MLLM calls does not automatically mean better navigation.
```

The hard failure, episode 9, remains unsolved across the baseline MLLM run and both trigger-parameter experiments.

The results suggest that the issue may not only be when the MLLM is called. The generated waypoint quality may also need to be analyzed.

---

## Experiment Naming Convention

For controlled experiments, include the important parameter settings in the run folder name.

Example:

```text
Agent_DataMap__MLLM_gemma3_27b__small_10x1__pt1_wp4_np5
```

Meaning:

| Part | Meaning |
|---|---|
| `Agent_DataMap` | DataMap agent was used |
| `MLLM_gemma3_27b` | gemma3:27b was used as the MLLM |
| `small_10x1` | 10 trajectories from 1 difficulty |
| `pt1` | `progress_threshold = 1` |
| `wp4` | `waypoint_threshold = 4` |
| `np5` | `n_points = 5` |

This helps avoid overwriting old result folders and makes experiment comparison easier.

---

## Useful Analysis Commands

Summarize all result folders:

```bash
python3 scripts/summarize_results.py
```

Analyze one run folder:

```bash
python3 scripts/analyze_episodes.py --run-folder Agent_DataMap__MLLM_gemma3_27b__small_10x1__pt1_wp4_np5
```

Analyze only MLLM-triggered episodes:

```bash
python3 scripts/analyze_episodes.py --run-folder Agent_DataMap__MLLM_gemma3_27b__small_10x1__pt1_wp4_np5 --mllm-only
```

Analyze only failures:

```bash
python3 scripts/analyze_episodes.py --run-folder Agent_DataMap__MLLM_gemma3_27b__small_10x1__pt1_wp4_np5 --failures-only
```

Export summaries to CSV:

```bash
python3 scripts/summarize_results.py --csv ignore/results_summary.csv
python3 scripts/analyze_episodes.py --csv ignore/episode_summary.csv
```

The CSV files are saved under `ignore/`, so they are local analysis outputs and usually should not be committed.

---

## Possible Next Directions

Based on these experiments, the next useful direction is probably not more trigger tuning yet.

Possible next steps:

1. Add repeated-waypoint analysis to `analyze_episodes.py`.
2. Add a prompt instruction asking the MLLM to avoid previous failed waypoints.
3. Add a waypoint-quality check before accepting MLLM output.
4. Compare generated waypoints against the map or path history.
5. Inspect episode 9 visually to understand why the suggested waypoints do not help.