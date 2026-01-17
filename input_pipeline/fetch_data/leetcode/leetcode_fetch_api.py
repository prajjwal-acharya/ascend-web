"""
LeetCode Fetch API Script

Hybrid approach to fetch LeetCode problems using multiple safe sources:
1. Static JSON baseline (2,913 problems - already have)
2. Alfa LeetCode API (third-party proxy, safe, rate-limited)
3. LeetCode Official API (public, limited data)

Usage:
    python3 leetcode_fetch_api.py --mode list       # Fetch problem list only
    python3 leetcode_fetch_api.py --mode details    # Fetch detailed problem data
    python3 leetcode_fetch_api.py --mode sync       # Sync new problems with existing data
    python3 leetcode_fetch_api.py --mode daily      # Get today's daily problem
"""
import os
import sys
import json
import time
import random
import argparse
import urllib.request
import urllib.error
from datetime import datetime
from typing import Optional, Dict, List, Any

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")
STATE_FILE = os.path.join(SCRIPT_DIR, "fetch_state.json")
MERGED_FILE = os.path.join(DATA_DIR, "merged_problems.json")
API_FETCHED_DIR = os.path.join(DATA_DIR, "api_fetched")

# API Endpoints
ALFA_API_BASE = "https://alfa-leetcode-api.onrender.com"
LEETCODE_OFFICIAL_API = "https://leetcode.com/api/problems/all/"

# Request settings
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
DEFAULT_TIMEOUT = 30


def setup_directories():
    """Create necessary directories."""
    if not os.path.exists(API_FETCHED_DIR):
        os.makedirs(API_FETCHED_DIR)


def load_state() -> Dict:
    """Load the fetch state file."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {
        "last_sync": None,
        "total_problems_known": 0,
        "fetched_slugs": [],
        "errors": []
    }


def save_state(state: Dict):
    """Save the fetch state file."""
    state["last_sync"] = datetime.now().isoformat()
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def api_request(url: str) -> Optional[Dict]:
    """Make a GET request to an API endpoint."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=DEFAULT_TIMEOUT) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"  HTTP Error {e.code}: {url}")
        return None
    except urllib.error.URLError as e:
        print(f"  URL Error: {e.reason}")
        return None
    except Exception as e:
        print(f"  Error: {e}")
        return None


def fetch_problem_list_alfa(limit: int = 50, skip: int = 0) -> Optional[Dict]:
    """Fetch problem list from Alfa API with pagination."""
    url = f"{ALFA_API_BASE}/problems?limit={limit}&skip={skip}"
    print(f"  Fetching: {url}")
    return api_request(url)


def fetch_problem_detail_alfa(title_slug: str) -> Optional[Dict]:
    """Fetch specific problem details from Alfa API."""
    url = f"{ALFA_API_BASE}/select?titleSlug={title_slug}"
    return api_request(url)


def fetch_daily_problem() -> Optional[Dict]:
    """Fetch today's daily problem from Alfa API."""
    url = f"{ALFA_API_BASE}/daily"
    return api_request(url)


def fetch_official_problem_list() -> Optional[Dict]:
    """Fetch all problems from LeetCode's official API (basic info only)."""
    print(f"  Fetching from official API: {LEETCODE_OFFICIAL_API}")
    return api_request(LEETCODE_OFFICIAL_API)


def load_existing_problems() -> Dict[str, Dict]:
    """Load existing problems from merged_problems.json."""
    existing = {}
    if os.path.exists(MERGED_FILE):
        with open(MERGED_FILE, "r") as f:
            data = json.load(f)
            questions = data.get("questions", data) if isinstance(data, dict) else data
            for q in questions:
                slug = q.get("problem_slug") or q.get("titleSlug", "")
                if slug:
                    existing[slug] = q
    return existing


def mode_list(args):
    """Mode: Fetch and display problem list summary."""
    print("=" * 60)
    print("MODE: PROBLEM LIST")
    print("=" * 60)
    
    # Fetch from official API for comprehensive list
    print("\n[1/2] Fetching from LeetCode Official API...")
    official_data = fetch_official_problem_list()
    if official_data:
        total = official_data.get("num_total", 0)
        pairs = official_data.get("stat_status_pairs", [])
        free_count = sum(1 for p in pairs if not p.get("paid_only", True))
        print(f"  -> Total problems: {total}")
        print(f"  -> Free problems: {free_count}")
    
    # Cross-check with Alfa API
    print("\n[2/2] Fetching from Alfa API...")
    alfa_data = fetch_problem_list_alfa(limit=1)
    if alfa_data:
        alfa_total = alfa_data.get("totalQuestions", 0)
        print(f"  -> Alfa reports: {alfa_total} problems")
    
    # Compare with existing
    existing = load_existing_problems()
    print(f"\n[Summary]")
    print(f"  Total on LeetCode: {total if official_data else 'Unknown'}")
    print(f"  Currently have: {len(existing)} problems")
    if official_data:
        print(f"  Missing: ~{total - len(existing)} problems")


def mode_details(args):
    """Mode: Fetch detailed problem data for missing problems."""
    print("=" * 60)
    print("MODE: FETCH DETAILS")
    print("=" * 60)
    
    setup_directories()
    state = load_state()
    fetched_slugs = set(state.get("fetched_slugs", []))
    
    # Get existing problems
    existing = load_existing_problems()
    print(f"Existing problems: {len(existing)}")
    print(f"Already fetched via API: {len(fetched_slugs)}")
    
    # Fetch problem list from Alfa to find new ones
    limit = args.limit or 20
    print(f"\nFetching up to {limit} new problems...")
    
    all_problems = []
    skip = 0
    batch_size = min(100, limit)
    
    while len(all_problems) < limit:
        data = fetch_problem_list_alfa(limit=batch_size, skip=skip)
        if not data or not data.get("problemsetQuestionList"):
            break
        
        problems = data.get("problemsetQuestionList", [])
        all_problems.extend(problems)
        skip += batch_size
        
        if len(problems) < batch_size:
            break
        
        time.sleep(random.uniform(0.5, 1.5))  # Rate limiting
    
    print(f"Found {len(all_problems)} problems in list")
    
    # Filter for missing problems
    missing = []
    for p in all_problems:
        slug = p.get("titleSlug", "")
        if slug and slug not in existing and slug not in fetched_slugs:
            if not p.get("isPaidOnly", False):  # Skip premium
                missing.append(p)
    
    print(f"Missing free problems: {len(missing)}")
    
    if not missing:
        print("No new problems to fetch.")
        return
    
    # Fetch details for missing problems
    fetched = 0
    errors = []
    
    for p in missing[:limit]:
        slug = p.get("titleSlug", "")
        print(f"\n[{fetched + 1}/{min(len(missing), limit)}] {slug}")
        
        detail = fetch_problem_detail_alfa(slug)
        if detail:
            # Save to file
            filename = os.path.join(API_FETCHED_DIR, f"{slug}.json")
            detail["_fetched_at"] = datetime.now().isoformat()
            detail["_source"] = "alfa_api"
            
            with open(filename, "w") as f:
                json.dump(detail, f, indent=2)
            
            print(f"  ✓ Saved to api_fetched/{slug}.json")
            fetched_slugs.add(slug)
            fetched += 1
        else:
            print(f"  ✗ Failed to fetch")
            errors.append(slug)
        
        # Rate limiting - be nice to the API
        time.sleep(random.uniform(1, 2))
    
    # Save state
    state["fetched_slugs"] = list(fetched_slugs)
    state["errors"] = errors
    save_state(state)
    
    print(f"\n{'=' * 60}")
    print(f"Done. Fetched {fetched} problems.")
    if errors:
        print(f"Errors: {len(errors)}")


def mode_sync(args):
    """Mode: Sync and identify new problems."""
    print("=" * 60)
    print("MODE: SYNC")
    print("=" * 60)
    
    existing = load_existing_problems()
    print(f"Existing: {len(existing)} problems")
    
    # Fetch full list from official API
    official = fetch_official_problem_list()
    if not official:
        print("Failed to fetch from official API")
        return
    
    total = official.get("num_total", 0)
    pairs = official.get("stat_status_pairs", [])
    
    # Find new problems
    new_problems = []
    for p in pairs:
        stat = p.get("stat", {})
        slug = stat.get("question__title_slug", "")
        paid = p.get("paid_only", False)
        
        if slug and slug not in existing and not paid:
            new_problems.append({
                "id": stat.get("frontend_question_id"),
                "title": stat.get("question__title"),
                "slug": slug,
                "difficulty": p.get("difficulty", {}).get("level", 0),
            })
    
    print(f"Total on LeetCode: {total}")
    print(f"New free problems found: {len(new_problems)}")
    
    if new_problems and args.show_new:
        print("\nNew problems:")
        for p in new_problems[:20]:
            diff = ["", "Easy", "Medium", "Hard"][p.get("difficulty", 0)]
            print(f"  {p['id']}. {p['title']} ({diff})")
        if len(new_problems) > 20:
            print(f"  ... and {len(new_problems) - 20} more")
    
    # Save new problem slugs to file for later fetching
    if new_problems:
        new_file = os.path.join(DATA_DIR, "new_problems.json")
        with open(new_file, "w") as f:
            json.dump(new_problems, f, indent=2)
        print(f"\nSaved to: {new_file}")


def mode_daily(args):
    """Mode: Get today's daily problem."""
    print("=" * 60)
    print("MODE: DAILY PROBLEM")
    print("=" * 60)
    
    daily = fetch_daily_problem()
    if not daily:
        print("Failed to fetch daily problem")
        return
    
    print(f"\n📅 Date: {daily.get('date')}")
    print(f"📝 Title: {daily.get('questionTitle')}")
    print(f"🔗 Link: {daily.get('questionLink')}")
    print(f"⚡ Difficulty: {daily.get('difficulty')}")
    print(f"🏷️  Topics: {', '.join(t.get('name', '') for t in daily.get('topicTags', []))}")
    
    if args.save:
        setup_directories()
        slug = daily.get("titleSlug", "daily")
        filename = os.path.join(API_FETCHED_DIR, f"{slug}.json")
        daily["_fetched_at"] = datetime.now().isoformat()
        daily["_source"] = "alfa_api_daily"
        
        with open(filename, "w") as f:
            json.dump(daily, f, indent=2)
        print(f"\n✓ Saved to api_fetched/{slug}.json")


def main():
    parser = argparse.ArgumentParser(description="LeetCode Fetch API - Hybrid Approach")
    parser.add_argument("--mode", choices=["list", "details", "sync", "daily"],
                        default="list", help="Operation mode")
    parser.add_argument("--limit", type=int, default=20,
                        help="Number of problems to fetch (for details mode)")
    parser.add_argument("--show-new", action="store_true",
                        help="Show list of new problems (for sync mode)")
    parser.add_argument("--save", action="store_true",
                        help="Save fetched data to file (for daily mode)")
    args = parser.parse_args()
    
    modes = {
        "list": mode_list,
        "details": mode_details,
        "sync": mode_sync,
        "daily": mode_daily,
    }
    
    modes[args.mode](args)


if __name__ == "__main__":
    main()
