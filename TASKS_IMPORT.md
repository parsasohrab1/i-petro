# Tasks Import Instructions

## Overview

The `tasks_seed.json` file contains 24 manual submission tasks:
- 16 tasks for scholarship/PhD applications (assigned to نرگس)
- 8 tasks for paper submissions (assigned to پارسا بابایی)

## Task Structure

Each task includes:
- `id`: Unique task identifier
- `title`: Task title in Persian
- `desc`: Task description
- `assignee`: User ID of the assignee
- `assignee_name`: Display name of the assignee
- `status`: "pending" (initial status)
- `priority`: "normal"
- `type`: "task"
- `kind`: "human_scholar" for scholarships, "submit" for papers
- `related_record_id`: ID of the related scholarship or paper record
- `related_record_type`: "scholarship" or "paper"
- `due`: Deadline date (if known)

## Import to Database

To load these tasks into the dashboard, use the server management command:

```bash
# Create a platform export manifest first
python3 << 'EOF'
import json
from pathlib import Path

# Read tasks
with open('tasks_seed.json', 'r', encoding='utf-8') as f:
    tasks_data = json.load(f)

# Create export structure
export_dir = Path('data/tasks_export')
export_dir.mkdir(parents=True, exist_ok=True)

# Write individual task files
batches = []
for task in tasks_data['tasks']:
    task_file = export_dir / f"{task['id']}.json"
    task_file.write_text(json.dumps(task, ensure_ascii=False, indent=2), encoding='utf-8')
    batches.append({
        "collection": "tasks",
        "doc_id": task['id'],
        "file_path": str(task_file)
    })

# Write manifest
manifest = {"batches": [batches]}
manifest_file = export_dir / 'manifest.json'
manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')

print(f"Created export manifest: {manifest_file}")
EOF

# Import using the server management command
python -m server.manage import-export data/tasks_export/manifest.json
```

## Assignee ID Note

The assignee ID for نرگس (`u_narges_scholarship_01`) is a placeholder. Before importing, update this ID in `tasks_seed.json` to match the actual user ID in the database. You can find user IDs with:

```bash
python -m server.manage list-members
```

The assignee ID for پارسا بابایی (`u_3czIynzDj3Ni9EAS_R637g`) is taken from the existing `agent/data_registry.json` file.
