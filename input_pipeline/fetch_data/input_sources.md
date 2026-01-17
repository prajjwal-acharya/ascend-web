# Input Sources:
1. Codeforces
2. Leetcode
3. 3rd party sources

## Codeforces:
I have implemented the codeforces_sync.py script to efficiently fetch and organize Codeforces contest and problem data:

- Fetches Contest Index: Retrieves all contests from Codeforces API and filters for FINISHED and non-gym contests.
- Fetches Master Problem List: Downloads the entire problem set in one API call.
- Local Processing: Groups all problems by their contestId.
- Data Persistence: specific per-contest JSON files in input_pipeline/fetch_data/codeforces/data/{contestId}.json.

## Leetcode:
LeetCode problems are available via multiple sources:

### **1. Static Dataset (Baseline)**
- **File**: `data/merged_problems.json`
- **Total**: 2,913 problems with full details
- **Source**: [neenza/leetcode-problems](https://github.com/neenza/leetcode-problems)

### **2. API Fetching (Updates)**
Use `leetcode_fetch_api.py` to sync new problems:

```bash
# Check problem counts and what's missing
python3 leetcode_fetch_api.py --mode list

# Find new problems (syncs with official API)
python3 leetcode_fetch_api.py --mode sync --show-new

# Fetch detailed data for missing problems
python3 leetcode_fetch_api.py --mode details --limit 20

# Get today's daily problem
python3 leetcode_fetch_api.py --mode daily --save
```

**APIs Used:**
| API | Purpose | Data |
|-----|---------|------|
| [Alfa LeetCode API](https://alfa-leetcode-api.onrender.com/) | Problem details | Full (description, hints, snippets) |
| `leetcode.com/api/problems/all/` | Problem listing | Basic (id, title, difficulty) |

**Output:**
- `data/api_fetched/{slug}.json` - Newly fetched problems
- `data/new_problems.json` - List of missing problems

### **Schema**
Each problem contains:
| Field | Description |
|-------|-------------|
| `title` | Problem name |
| `problem_id` / `questionId` | Internal ID |
| `difficulty` | Easy/Medium/Hard |
| `problem_slug` / `titleSlug` | URL-friendly name |
| `topics` / `topicTags` | Topic tags |
| `description` / `question` | Problem statement |
| `examples` | Input/output examples |
| `constraints` | Problem constraints |
| `hints` | Solving hints |
| `code_snippets` | Starter code (18+ languages) |