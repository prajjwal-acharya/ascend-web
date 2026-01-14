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
Here are the rules for fetching data from your two sources, strictly in pointers.

### **Source 1: Google Sheet (The Manager)**

* **Fetch the Identifier:** Extract the **Problem ID** and **Title Slug** (column with the URL-friendly name) to identify the target.
* **Fetch the Metadata:** Get **Difficulty** and **Like Ratio** to prioritize high-quality problems first.
* **Fetch the Status:** Read the **Status** column (e.g., "Done", "Todo") to filter out problems you have already processed.
* **Determine Order:** Use this source exclusively to decide **which** problem to process next; do not use it for problem descriptions.
* **Store State:** Update this source after a successful fetch (e.g., mark row as "In Jira") to prevent duplicate API calls.

### **Source 2: LeetCode GraphQL API (The Content Provider)**

* **Fetch the Content:** Request only specific fields: `content` (HTML description), `topicTags`, and `codeSnippets`.
* **Use the Golden Query:** Send a specific GraphQL payload asking only for the data missing from the Sheet (avoid requesting `stats` or `solutions` to keep payloads light).
* **Mimic a Human:** Always include `User-Agent`, `Referer` (`https://leetcode.com/`), and `Content-Type` (`application/json`) headers.
* **Randomize Delays:** Sleep for a random interval (e.g., `3` to `7` seconds) between every single request.
* **Limit Batch Size:** Process small batches (e.g., 20–50 problems) per run; never attempt to fetch the entire database at once.
* **Run Locally:** Execute the fetch script on a local machine (residential IP) rather than a cloud server (GitHub Actions/AWS) to avoid Cloudflare blocks.
* **Handle Errors:** If a `429` (Too Many Requests) or `403` (Forbidden) occurs, program the script to stop immediately and wait.