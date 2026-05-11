# Prompt and Parameter Experiment Notes

## Goal

This note identifies where the MLLM prompt is created and proposes small experiments for testing prompt and evaluation parameter changes. The goal is to understand the AI-side behavior before changing the main navigation logic.

## Main Prompt Location

The MLLM prompt appears to be built in:

- `modules/Other.py`

Important sections found through `grep`:

- `modules/Other.py:296-364`
  - Builds the prompt string sent to the MLLM.
- `modules/Other.py:363`
  - Queries the MLLM with the generated prompt.
- `modules/Other.py:382`
  - Parses waypoint coordinates from the MLLM response.
- `modules/Other.py:411`
  - Defines the `chat()` function used to communicate with the MLLM.

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

## Expected MLLM Output Format

The prompt asks the MLLM to respond in this format:

```text
[STRATEGY]: reason for generating the waypoint. [WAYPOINT]: (x, y).
```

## Completed Experiments

### Experiment 1: DataMap without MLLM

Settings:

```python
agent_type = "DataMap"
mllm_model = None
n_per_difficulty = 1
n_difficulties = 1
```

## Experiment Results

| Experiment | Agent | MLLM | Episodes | Accuracy | Notes |
|---|---|---|---:|---:|---|
| 1x1 baseline | DataMap | None | 1 | 100% | Quick baseline run |
| 1x1 MLLM | DataMap | gemma3:27b | 1 | 100% | Did not necessarily trigger MLLM waypoint generation |
| 5x1 baseline | DataMap | None | 5 | 100% | Small baseline run |
| 5x1 MLLM | DataMap | gemma3:27b | 5 | 100% | Small MLLM run |
| 10x1 baseline | DataMap | None | 10 | 90% | Larger quick baseline |
| 10x1 MLLM | DataMap | gemma3:27b | 10 | 90% | MLLM waypoint generation was triggered |

## MLLM Bug Found

During the 10x1 DataMap + gemma3:27b run, the evaluation reached the MLLM waypoint generation path and initially failed because `ollama` was not available/imported. Smaller MLLM runs did not expose this because they likely completed without triggering waypoint generation.

After fixing the Ollama import/package issue, the MLLM run completed successfully and generated a waypoint response.