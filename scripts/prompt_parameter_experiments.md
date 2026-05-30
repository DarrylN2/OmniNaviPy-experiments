# Prompt and Parameter Experiment Notes

## Goal

This note tracks small prompt and parameter experiments for the MLLM waypoint logic in OmniNaviPy.

The goal is to understand the AI-side behavior before changing the main navigation logic, model, or perception pipeline.

Current focus:

```text
When should the MLLM be called, and can prompt changes improve the quality of generated waypoints?
```

The initial controlled experiments changed the MLLM stuck-detection parameters. After those experiments showed that more MLLM calls did not improve success rate, the next experiment tested whether stronger prompt wording could reduce repeated waypoint suggestions.

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

## Relevant Trigger and Prompt Parameters

The high-level MLLM waypoint logic is controlled mainly by these parameters:

| Parameter | Meaning |
|---|---|
| `progress_threshold` | Minimum progress toward the target required over the recent path window |
| `waypoint_threshold` | Distance needed to consider a waypoint reached |
| `n_points` | Number of recent path points used to check whether the drone is stuck |
| `pause_after_waypoint` | Whether to pause MLLM checks after a waypoint is generated |
| `avoid_repeat_waypoints` | Whether to add stronger prompt wording that discourages repeated waypoint suggestions |
| `obstruction_aware_waypoints` | Whether to add prompt wording that asks for reachable, obstruction-aware waypoints |

The stuck detector checks whether the drone has made enough progress toward the target over the last `n_points`.

In simple terms:

- Higher `progress_threshold` makes the stuck detector more sensitive.
- Lower `n_points` makes the MLLM check for stuck behavior earlier.
- Higher `n_points` makes the MLLM wait longer before deciding the drone is stuck.
- `pause_after_waypoint=True` helps avoid repeatedly calling the MLLM too quickly.
- `avoid_repeat_waypoints=True` asks the MLLM to avoid previous failed waypoints and choose a substantially different waypoint.
- `obstruction_aware_waypoints=True` asks the MLLM to avoid blocked/unreachable waypoints and prefer reachable subgoals around obstacles.

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

| Episode | Success | Termination | Steps | MLLM calls | Waypoints | Repeated waypoints | Final distance |
|---|---|---|---:|---:|---:|---:|---:|
| 5 | True | `goal_reached` | 24 | 3 | 3 | 0 | 8.0 |
| 9 | False | `max_steps_exceeded` | 32 | 6 | 6 | 4 | 50.96 |

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
repeated waypoints = 4
final distance = 50.96
generated waypoints = (-20, 22); (-15, 20); (-20, 22); (-20, 22); (-20, 22); (-20, 22)
```

The MLLM mostly repeated the same waypoint `(-20, 22)`.

Observation:

Reducing `n_points` from 8 to 5 caused the MLLM to trigger more often, but the extra calls did not fix episode 9. In the failed episode, the generated waypoints were repetitive, suggesting that simply calling the MLLM more often may not be enough.

Interpretation:

The problem may be waypoint quality rather than only stuck-detection timing. This motivated adding repeated-waypoint analysis to `analyze_episodes.py` and testing a stronger anti-repeat prompt.

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

| Episode | Success | Termination | Steps | MLLM calls | Waypoints | Repeated waypoints | Final distance |
|---|---|---|---:|---:|---:|---:|---:|
| 9 | False | `max_steps_exceeded` | 32 | 3 | 3 | 0 | 50.0 |

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

## Experiment 3: Anti-repeat Prompt

Run folder:

```text
Agent_DataMap__MLLM_gemma3_27b__small_10x1__pt1_wp4_np5__avoidrepeat
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
| `avoid_repeat_waypoints` | True |
| `n_per_difficulty` | 10 |
| `n_difficulties` | 1 |
| `seed` | 777 |

Code changes tested:

- Added an optional `avoid_repeat_waypoints` flag to `HighLevelPolicy`.
- Added stronger prompt wording asking the MLLM not to repeat or slightly modify previous attempted waypoints.
- Changed waypoint setting to use `episode.add_waypoint(waypoint)` so generated waypoints are saved in `episode.waypoint_history`.

Command:

```bash
python3 scripts/evaluate_navigation_mllm_trigger.py
```

Analysis commands:

```bash
python3 scripts/summarize_results.py
python3 scripts/analyze_episodes.py --run-folder Agent_DataMap__MLLM_gemma3_27b__small_10x1__pt1_wp4_np5__avoidrepeat --mllm-only
python3 scripts/analyze_episodes.py --run-folder Agent_DataMap__MLLM_gemma3_27b__small_10x1__pt1_wp4_np5__avoidrepeat --failures-only
python3 scripts/analyze_episodes.py --run-folder Agent_DataMap__MLLM_gemma3_27b__small_10x1__pt1_wp4_np5__avoidrepeat --csv ignore/episode_summary_pt1_wp4_np5_avoidrepeat.csv
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
| Episodes with repeated waypoints | 0 |
| Episodes with near repeats | 0 |
| Average steps | 9.1 |
| Average final distance | 11.23 |

Episode-level observations:

| Episode | Success | Termination | Steps | MLLM calls | Waypoints | Repeated waypoints | Final distance |
|---|---|---|---:|---:|---:|---:|---:|
| 5 | True | `goal_reached` | 18 | 3 | 3 | 0 | 16.03 |
| 9 | False | `max_steps_exceeded` | 32 | 6 | 6 | 0 | 50.96 |

Generated waypoints for episode 5:

```text
(25, 69); (33, 60); (10, 65)
```

Generated waypoints for episode 9:

```text
(-20, 22); (-20, 12); (-30, 30); (-40, 12); (-50, 15); (-60, 22)
```

Interpretation:

The anti-repeat prompt successfully reduced exact repeated waypoint suggestions. In the previous `pt1_wp4_np5` run, episode 9 had 4 repeated waypoint occurrences. In this anti-repeat run, episode 9 had 0 repeated waypoint occurrences.

However, episode 9 still failed with `max_steps_exceeded`, and the final distance stayed at 50.96.

Conclusion:

```text
The prompt change improved waypoint diversity, but it did not improve navigation success.
This suggests the next problem may be waypoint quality or waypoint reachability, not only repeated waypoint generation.
```

---

---

## Experiment 4: Obstruction-aware Prompt

Run folder:

```text
Agent_DataMap__MLLM_gemma3_27b__small_10x1__pt1_wp4_np5__avoidrepeat__obstructionaware
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
| `avoid_repeat_waypoints` | True |
| `obstruction_aware_waypoints` | True |
| `n_per_difficulty` | 10 |
| `n_difficulties` | 1 |
| `seed` | 777 |

Code changes tested:

- Added an optional `obstruction_aware_waypoints` flag to `HighLevelPolicy`.
- Added prompt wording asking the MLLM to choose immediately reachable subgoals.
- The prompt told the MLLM not to place waypoints behind obstacles and to choose waypoints near openings, corners, gaps, or passages.

Command:

```bash
python3 scripts/evaluate_navigation.py
```

Analysis commands:

```bash
python3 scripts/analyze_episodes.py \
  --run-folder Agent_DataMap__MLLM_gemma3_27b__small_10x1__pt1_wp4_np5__avoidrepeat__obstructionaware \
  --mllm-only \
  --csv ignore/results/obstructionaware_episode_analysis.csv

python3 scripts/analyze_episodes.py \
  --run-folder Agent_DataMap__MLLM_gemma3_27b__small_10x1__pt1_wp4_np5__avoidrepeat__obstructionaware \
  --failures-only \
  --mllm-only
```

Result:

| Metric | Value |
|---|---:|
| Accuracy | 80.0% |
| Episodes | 10 |
| Successes | 8 |
| Failures | 2 |
| Episodes with MLLM calls | 2 |
| Episodes with waypoints | 2 |
| Episodes with repeated waypoints | 0 |
| Episodes with near repeats | 0 |
| Average final distance for MLLM episodes | 32.14 |

Episode-level observations:

| Episode | Success | Termination | Steps | MLLM calls | Waypoints | Repeated waypoints | Final distance |
|---|---|---|---:|---:|---:|---:|---:|
| 5 | False | `max_steps_exceeded` | 32 | 4 | 4 | 0 | 21.84 |
| 9 | False | `max_steps_exceeded` | 32 | 6 | 6 | 0 | 42.44 |

Generated waypoints for episode 5:

```text
(24, 69); (10, 69); (1, 69); (18, 79)
```

Generated waypoints for episode 9:

```text
(-14, 22); (-20, 22); (-25, 22); (-18, 28); (-25, 28); (-28, 32)
```

Interpretation:

The obstruction-aware prompt successfully avoided exact repeated waypoints, but the overall accuracy decreased from 90% to 80%.

The prompt appeared to make the MLLM more willing to generate escape-like waypoints that moved around obstacles. However, this may have overcorrected and made the navigation less goal-directed.

Episode 5 became a new failure, even though it succeeded in the anti-repeat experiment.

Conclusion:

```text
The obstruction-aware prompt changed waypoint behavior, but it reduced accuracy.
The prompt may have encouraged too much obstacle-avoidance or escape behavior without enough target-directed progress.
```

---

## Experiment 5: Balanced Obstruction-aware Prompt

Run folder:

```text
Agent_DataMap__MLLM_gemma3_27b__small_10x1__pt1_wp4_np5__avoidrepeat__balanced_obstructionaware
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
| `avoid_repeat_waypoints` | True |
| `obstruction_aware_waypoints` | True |
| `n_per_difficulty` | 10 |
| `n_difficulties` | 1 |
| `seed` | 777 |

Code changes tested:

- Kept the obstruction-aware waypoint idea.
- Changed the prompt to be more conservative.
- Added wording that prefers nearby reachable waypoints, reasonable target progress, and the smallest necessary detour.

Command:

```bash
python3 scripts/evaluate_navigation.py
```

Analysis commands:

```bash
python3 scripts/analyze_episodes.py \
  --run-folder Agent_DataMap__MLLM_gemma3_27b__small_10x1__pt1_wp4_np5__avoidrepeat__balanced_obstructionaware \
  --mllm-only \
  --csv ignore/results/balanced_obstructionaware_episode_analysis.csv

python3 scripts/analyze_episodes.py \
  --run-folder Agent_DataMap__MLLM_gemma3_27b__small_10x1__pt1_wp4_np5__avoidrepeat__balanced_obstructionaware \
  --failures-only \
  --mllm-only
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
| Episodes with repeated waypoints | 0 |
| Episodes with near repeats | 1 |
| Average final distance for MLLM episodes | 30.68 |

Episode-level observations:

| Episode | Success | Termination | Steps | MLLM calls | Waypoints | Repeated waypoints | Near-repeated waypoints | Final distance |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 5 | True | `goal_reached` | 20 | 3 | 3 | 0 | 0 | 8.06 |
| 9 | False | `max_steps_exceeded` | 32 | 6 | 6 | 0 | 1 | 53.31 |

Generated waypoints for episode 5:

```text
(17, 69); (28, 69); (40, 69)
```

Generated waypoints for episode 9:

```text
(-14, 20); (-20, 15); (-25, 22); (-15, 28); (-18, 28); (-25, 35)
```

Interpretation:

The balanced obstruction-aware prompt recovered accuracy from 80% back to 90%.

Episode 5 succeeded again, meaning the balanced wording avoided the extra failure caused by the stronger obstruction-aware prompt.

However, episode 9 still failed. It had no exact repeated waypoints, but it had one near-repeated waypoint. Its final distance was worse than the anti-repeat run.

Conclusion:

```text
The balanced obstruction-aware prompt was better than the stronger obstruction-aware prompt, but it still did not solve episode 9.
This suggests prompt-only changes can influence waypoint behavior, but they may not be enough for the hardest failure case.
```


## Comparison Across Experiments

| Setting | Accuracy | Episodes with MLLM calls | Total MLLM calls | Repeated waypoint issue | Average steps | Episode 9 result |
|---|---:|---:|---:|---|---:|---|
| Default MLLM, `pt1_wp4_np8` | 90.0% | 1 | 3 | Low / not measured deeply | 8.4 | Failed |
| Earlier trigger, `pt1_wp4_np5` | 90.0% | 2 | 9 | Episode 9 repeated waypoint 4 times | 9.7 | Failed |
| Higher threshold, `pt3_wp4_np8` | 90.0% | 1 | 3 | No exact repeat, but similar direction | 8.4 | Failed |
| Anti-repeat prompt, `pt1_wp4_np5__avoidrepeat` | 90.0% | 2 | 9 | Exact repeats reduced to 0 | 9.1 | Failed |
| Obstruction-aware prompt, `pt1_wp4_np5__avoidrepeat__obstructionaware` | 80.0% | 2 | 10 | Exact repeats 0, but extra failure introduced | 32.0 for failed MLLM episodes | Failed |
| Balanced obstruction-aware prompt, `pt1_wp4_np5__avoidrepeat__balanced_obstructionaware` | 90.0% | 2 | 9 | Exact repeats 0, near repeat 1 | 26.0 for MLLM episodes | Failed |

Overall interpretation:

Changing the trigger parameters changed how often the MLLM was called, but it did not improve the success rate.

The anti-repeat prompt improved waypoint diversity, but it still did not solve episode 9.

The stronger obstruction-aware prompt changed waypoint behavior but reduced accuracy from 90% to 80%. It introduced a new failure in episode 5, likely because the prompt encouraged too much escape-like obstacle avoidance without enough target-directed progress.

The balanced obstruction-aware prompt recovered accuracy back to 90% and fixed episode 5, but episode 9 still failed.

Main findings:

```text
More MLLM calls does not automatically mean better navigation.
Reducing repeated waypoints does not automatically mean better navigation.
Obstruction-aware prompt wording can change waypoint behavior, but overly strong obstacle-avoidance wording can hurt performance.
Balanced wording is safer than strong escape-style wording, but prompt-only changes still did not solve episode 9.
```

The hard failure, episode 9, remains unsolved across the baseline MLLM run, trigger-parameter experiments, anti-repeat prompt experiment, and obstruction-aware prompt experiments.

The results suggest that the issue may not only be when the MLLM is called, whether it repeats waypoints, or whether it is told to avoid obstacles. The generated waypoints may need to be evaluated for quality, reachability, and whether the low-level DQN policy can actually move toward them.


---

## Experiment Naming Convention

For controlled experiments, include the important parameter settings in the run folder name.

Example:

```text
Agent_DataMap__MLLM_gemma3_27b__small_10x1__pt1_wp4_np5__avoidrepeat
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
| `avoidrepeat` | Prompt variant discouraging repeated waypoint suggestions |

This helps avoid overwriting old result folders and makes experiment comparison easier.

Additional examples:

| Run suffix | Meaning |
|---|---|
| `avoidrepeat` | Prompt discourages exact or slight repeats of previous failed waypoints |
| `obstructionaware` | Prompt asks for reachable waypoints around obstacles/openings |
| `balanced_obstructionaware` | Prompt asks for reachable waypoints but also emphasizes nearby points, small detours, and target-directed progress |


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
python3 scripts/analyze_episodes.py --run-folder Agent_DataMap__MLLM_gemma3_27b__small_10x1__pt1_wp4_np5__avoidrepeat --csv ignore/episode_summary_pt1_wp4_np5_avoidrepeat.csv
```

The CSV files are saved under `ignore/`, so they are local analysis outputs and usually should not be committed.

---

## Possible Next Directions

Based on these experiments, the next useful direction is probably not more trigger tuning or simple prompt-only changes.

Completed so far:

1. Added repeated-waypoint analysis to `analyze_episodes.py`.
2. Added a prompt instruction asking the MLLM to avoid previous failed waypoints.
3. Confirmed that the anti-repeat prompt reduced exact repeated waypoints from 4 to 0 in episode 9.
4. Confirmed that episode 9 still failed even with more diverse waypoints.
5. Added obstruction-aware prompt wording.
6. Found that the stronger obstruction-aware prompt reduced accuracy from 90% to 80% and introduced a new failure in episode 5.
7. Added a balanced obstruction-aware prompt.
8. Found that the balanced obstruction-aware prompt recovered accuracy to 90% and fixed episode 5, but episode 9 still failed.

Possible next steps:

1. Add waypoint-following analysis:
   - Did the drone actually move closer to each generated waypoint after it was set?
   - Did the drone ever get within `waypoint_threshold` of the waypoint?
   - If not, the issue may be that the low-level DQN cannot reach the waypoint.
2. Add waypoint-quality analysis:
   - Is the waypoint closer to the target than the robot's current position?
   - Is the waypoint too far away?
   - Is the waypoint near obstacles or outside safe regions?
3. Compare generated waypoints against path history:
   - Did the waypoint send the robot back into an already failed area?
   - Did the waypoint lead to a new region of the map?
4. Inspect episode 9 visually:
   - Open `image_display.png` or saved map images for the failed run.
   - Check whether the generated waypoints are actually reasonable.
5. Test waypoint-aware stuck detection:
   - Currently, the stuck detector measures progress toward the final target.
   - When an intermediate waypoint is active, it may be better to measure progress toward the active waypoint.
   - This matters because obstacle-avoidance waypoints may require the drone to move sideways or temporarily away from the final target.
6. Add a code-level waypoint filter:
   - Reject exact repeated waypoints.
   - Reject near-repeated waypoints.
   - Reject waypoints that are too far from the current robot position.
   - Reject waypoints that do not improve reachability or appear blocked.

Most likely next direction:

```text
Prompt-only changes can change waypoint behavior, but they have not solved episode 9.
The next experiment should probably analyze waypoint reachability or test waypoint-aware stuck detection.
```
