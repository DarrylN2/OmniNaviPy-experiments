import argparse
import pickle
from pathlib import Path

import matplotlib.pyplot as plt


DEFAULT_RESULTS_DIR = Path("ignore/results")


def load_pickle(path):
    if not path.exists():
        raise FileNotFoundError(f"Could not find: {path}")

    with open(path, "rb") as f:
        return pickle.load(f)


def get_episode(episodes, episode_id):
    if isinstance(episodes, dict):
        if episode_id in episodes:
            return episodes[episode_id]

        if str(episode_id) in episodes:
            return episodes[str(episode_id)]

        raise KeyError(f"Episode {episode_id} not found. Available keys: {list(episodes.keys())}")

    return episodes[episode_id]


def add_point(points, point):
    if point is not None:
        points.append((point.x, point.y))


def plot_episode(episode, run_folder, episode_id, output_path=None, margin=10):
    path_history = getattr(episode, "path_history", [])
    waypoint_history = getattr(episode, "waypoint_history", [])
    start_point = getattr(episode, "start_point", None)
    target_point = getattr(episode, "target_point", None)
    termination = getattr(episode, "termination", "unknown")

    if not path_history:
        print("No path_history found.")
        return

    path_x = [point.x for point in path_history]
    path_y = [point.y for point in path_history]

    fig, ax = plt.subplots(figsize=(10, 8))

    # Robot path
    ax.plot(path_x, path_y, marker="o", linewidth=2, markersize=4, label="Path")

    # Start
    if start_point is not None:
        ax.scatter(start_point.x, start_point.y, marker="P", s=180, label="Start")
        ax.text(start_point.x, start_point.y, " Start", fontsize=10)

    # Target
    if target_point is not None:
        ax.scatter(target_point.x, target_point.y, marker="*", s=250, label="Target")
        ax.text(target_point.x, target_point.y, " Target", fontsize=10)

    # Final position
    final_point = path_history[-1]
    ax.scatter(final_point.x, final_point.y, marker="X", s=180, label="Final")
    ax.text(final_point.x, final_point.y, " Final", fontsize=10)

    # Waypoints
    if waypoint_history:
        wp_x = [point.x for point in waypoint_history]
        wp_y = [point.y for point in waypoint_history]
        ax.scatter(wp_x, wp_y, marker="^", s=140, label="Waypoints")

        for idx, point in enumerate(waypoint_history, start=1):
            ax.text(point.x, point.y, f" WP{idx}", fontsize=10)

    # Label some path steps
    for idx, point in enumerate(path_history):
        if idx == 0 or idx == len(path_history) - 1 or idx % 5 == 0:
            ax.text(point.x, point.y, str(idx), fontsize=8)

    # Auto zoom around useful points
    all_points = []
    for point in path_history:
        add_point(all_points, point)
    for point in waypoint_history:
        add_point(all_points, point)
    add_point(all_points, start_point)
    add_point(all_points, target_point)

    xs = [x for x, y in all_points]
    ys = [y for x, y in all_points]

    ax.set_xlim(min(xs) - margin, max(xs) + margin)
    ax.set_ylim(min(ys) - margin, max(ys) + margin)

    ax.set_title(f"{run_folder}\nEpisode {episode_id} | termination = {termination}")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.axis("equal")
    ax.grid(True)
    ax.legend(loc="best")
    plt.tight_layout()

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=200)
        print(f"Saved plot to: {output_path}")
    else:
        plt.show()


def main():
    parser = argparse.ArgumentParser(description="Plot path and waypoints for one OmniNaviPy episode.")

    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--run-folder", type=str, required=True)
    parser.add_argument("--episode-id", type=int, required=True)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--margin", type=float, default=10)

    args = parser.parse_args()

    episodes_path = args.results_dir / args.run_folder / "episodes.p"
    episodes = load_pickle(episodes_path)
    episode = get_episode(episodes, args.episode_id)

    plot_episode(
        episode=episode,
        run_folder=args.run_folder,
        episode_id=args.episode_id,
        output_path=args.output,
        margin=args.margin,
    )


if __name__ == "__main__":
    main()