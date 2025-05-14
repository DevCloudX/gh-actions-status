from github import Github
import yaml
import base64
import os
from collections import defaultdict, Counter
from tabulate import tabulate

GITHUB_TOKEN = os.getenv("GH_PAT")
ORG_NAME = os.getenv("ORG_NAME")

if not GITHUB_TOKEN:
    raise ValueError("GH_PAT token is not set.")
if not ORG_NAME:
    raise ValueError("ORG_NAME is not set.")

g = Github(GITHUB_TOKEN)
org = g.get_organization(ORG_NAME)

action_usage = defaultdict(lambda: {"runs": 0, "success": 0, "failure": 0})
total_actions = Counter()

print(f"Scanning organization: {ORG_NAME} ...")

for repo in org.get_repos():
    try:
        workflows = repo.get_contents(".github/workflows")
    except:
        continue

    actions_in_repo = set()

    for wf in workflows:
        if not wf.name.endswith((".yml", ".yaml")):
            continue
        try:
            content = base64.b64decode(wf.content).decode()
            data = yaml.safe_load(content)
            jobs = data.get("jobs", {})
            for job in jobs.values():
                for step in job.get("steps", []):
                    if "uses" in step:
                        action = step["uses"].split("@")[0]
                        actions_in_repo.add(action)
                        total_actions[action] += 1
        except Exception as e:
            print(f"Error parsing workflow {wf.name} in {repo.name}: {e}")
            continue

    # Analyze workflow runs
    try:
        runs = repo.get_workflow_runs(status="completed")
        for run in runs:
            run_status = run.conclusion
            for action in actions_in_repo:
                action_usage[action]["runs"] += 1
                if run_status == "success":
                    action_usage[action]["success"] += 1
                else:
                    action_usage[action]["failure"] += 1
    except Exception as e:
        print(f"Error fetching runs for repo {repo.name}: {e}")
        continue

# Prepare table
table = []
for action, stats in action_usage.items():
    runs = stats["runs"]
    success = stats["success"]
    failure = stats["failure"]
    ratio = (success / runs * 100) if runs else 0
    table.append([action, runs, success, failure, f"{ratio:.2f}%"])

table.sort(key=lambda x: x[1], reverse=True)

# Output table to stdout and save to file
print("\n📊 GitHub Actions Usage Report:\n")
print(tabulate(table, headers=["Action", "Total Runs", "Success", "Failure", "Success Ratio (%)"], tablefmt="github"))

with open("gh-actions-usage-summary.txt", "w") as f:
    f.write(tabulate(table, headers=["Action", "Total Runs", "Success", "Failure", "Success Ratio (%)"], tablefmt="github"))
