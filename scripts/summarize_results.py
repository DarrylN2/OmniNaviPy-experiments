import json
from pathlib import Path

# Folder where all experiment result folders are saved.
# Example:
# ignore/results/Agent_DataMap__MLLM_None/
# ignore/results/Agent_DataMap__MLLM_gemma3_27b/
RESULTS_DIR = Path("ignore/results")


def parse_folder_name(folder_name):
    """
    Extract the agent name and MLLM name from a result folder name.

    Example:
    Agent_DataMap__MLLM_None
    becomes:
    agent = DataMap
    mllm = None
    """

    # The folder name uses "__" to separate each setting.
    parts = folder_name.split("__")

    # Default values in case the folder name does not include these fields.
    agent = "Unknown"
    mllm = "Unknown"

    # Look through each part of the folder name and extract useful info.
    for part in parts:
        if part.startswith("Agent_"):
            agent = part.replace("Agent_", "")
        elif part.startswith("MLLM_"):
            mllm = part.replace("MLLM_", "")

    return agent, mllm


def main():
    """
    Read every metrics.json file inside ignore/results
    and print a summary table.
    """

    # Stop early if the results folder does not exist.
    if not RESULTS_DIR.exists():
        print(f"Results folder not found: {RESULTS_DIR}")
        return

    # This list will store one row of summary data for each result folder.
    rows = []

    # Go through every folder inside ignore/results.
    for result_folder in sorted(RESULTS_DIR.iterdir()):

        # Skip anything that is not a folder.
        if not result_folder.is_dir():
            continue

        # Each result folder should contain a metrics.json file.
        metrics_path = result_folder / "metrics.json"

        # Skip folders that do not have metrics.json.
        if not metrics_path.exists():
            continue

        # Load the metrics.json file.
        with open(metrics_path, "r") as f:
            metrics = json.load(f)

        # Get the agent and MLLM setting from the folder name.
        agent, mllm = parse_folder_name(result_folder.name)

        # Get accuracy from the metrics file.
        # If accuracy does not exist, show "N/A".
        accuracy = metrics.get("accuracy", "N/A")

        # Save this experiment's summary as one row.
        rows.append((result_folder.name, agent, mllm, accuracy))

    # If no valid result folders were found, tell the user.
    if not rows:
        print("No metrics.json files found.")
        return

    # Print the table header.
    print(f"{'Folder':45} {'Agent':18} {'MLLM':18} {'Accuracy':10}")
    print("-" * 95)

    # Print each experiment result.
    for folder, agent, mllm, accuracy in rows:
        print(f"{folder:45} {agent:18} {mllm:18} {accuracy}")


if __name__ == "__main__":
    main()