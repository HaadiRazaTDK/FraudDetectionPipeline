import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "src" / "cfg" / "config.json"


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


def run_for_repo(repo_url, branch, start_date, end_date, commits="1"):
    config = load_config()
    config["repository"] = repo_url
    config["branch"] = branch
    config["commits"] = commits
    config["starting_date"] = start_date
    config["ending_date"] = end_date

    with open(CONFIG_PATH, "w", encoding="utf-8") as handle:
        json.dump(config, handle, indent=2)

    print(f"Running for {repo_url} on branch {branch} from {start_date} to {end_date}")
    subprocess.run([sys.executable, str(ROOT / "main.py")], cwd=ROOT, input=f"{repo_url}\n{branch}\n{commits}\npy\n{start_date}\n{end_date}\n", text=True, check=False)


def main():
    repos = [
        {
            "url": "https://github.com/yourname/data-science-eda.git",
            "branch": "main",
            "start": "2023,01,01",
            "end": "2024,01,01",
            "commits": "1",
        },
        {
            "url": "https://github.com/yourname/ml-pipeline-project.git",
            "branch": "main",
            "start": "2024,01,01",
            "end": "2025,01,01",
            "commits": "1",
        },
        {
            "url": "https://github.com/yourname/time-series-forecast.git",
            "branch": "main",
            "start": "2025,01,01",
            "end": "2026,07,01",
            "commits": "1",
        },
    ]

    for repo in repos:
        run_for_repo(
            repo_url=repo["url"],
            branch=repo["branch"],
            start_date=repo["start"],
            end_date=repo["end"],
            commits=repo["commits"],
        )


if __name__ == "__main__":
    main()
