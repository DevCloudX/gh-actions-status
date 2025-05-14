# .github/scripts/org_action_usage_report.py

from github import Github
import yaml
import base64
import matplotlib.pyplot as plt
from collections import Counter
import os

GITHUB_TOKEN = os.getenv("GH_PAT")
ORG_NAME = os.getenv("ORG_NAME")

g = Github(GITHUB_TOKEN)
org = g.get_organization(ORG_NAME)

action_usage = Counter()

for repo in org.get_repos():
    try:
        contents = repo.get_contents(".github/workflows")
    except:
        continue

    for file in contents:
        if file.name.endswith((".yml", ".yaml")):
            content = base64.b64decode(file.content).decode()
            try:
                workflow = yaml.safe_load(content)
                jobs = workflow.get("jobs", {})
                for job in jobs.values():
                    for step in job.get("steps", []):
                        if "uses" in step:
                            action = step["uses"].split("@")[0]
                            action_usage[action] += 1
            except Exception as e:
                print(f"Error parsing {file.name} in {repo.full_name}: {e}")

top_actions = action_usage.most_common(10)
labels, counts = zip(*top_actions) if top_actions else ([], [])

plt.figure(figsize=(10, 6))
plt.bar(labels, counts, color='dodgerblue')
plt.xticks(rotation=45, ha='right')
plt.title(f"Top GitHub Actions in Org '{ORG_NAME}'")
plt.ylabel("Usage Count")
plt.tight_layout()
plt.savefig("gh-actions-usage-bar.png")
plt.show()

plt.figure(figsize=(8, 8))
plt.pie(counts, labels=labels, autopct='%1.1f%%', startangle=140)
plt.title("Usage Ratio of Top GitHub Actions")
plt.tight_layout()
plt.savefig("gh-actions-usage-pie.png")
plt.show()
