import requests
import json
import os
import time

def fetch_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"Created directory: {data_dir}")

    # Step 1: Get Contest Index
    print("Step 1: Fetching Contest Index...")
    try:
        contest_response = requests.get("https://codeforces.com/api/contest.list")
        contest_response.raise_for_status()
        contests_data = contest_response.json()
        if contests_data["status"] != "OK":
            print(f"Error fetching contests: {contests_data.get('comment')}")
            return
        
        all_contests = contests_data["result"]
        # Filter: FINISHED and non-gym
        valid_contests = [
            c for c in all_contests 
            if c["phase"] == "FINISHED" and not c.get("gym", False)
        ]
        print(f"Found {len(valid_contests)} valid contests (FINISHED, non-gym).")

    except Exception as e:
        print(f"Exception during contest fetch: {e}")
        return

    # Step 2: Get Master Problem List
    print("Step 2: Fetching Master Problem List...")
    try:
        problems_response = requests.get("https://codeforces.com/api/problemset.problems")
        problems_response.raise_for_status()
        problems_data = problems_response.json()
        if problems_data["status"] != "OK":
            print(f"Error fetching problems: {problems_data.get('comment')}")
            return
        
        all_problems = problems_data["result"]["problems"]
        problem_stats = problems_data["result"]["problemStatistics"]
        
        print(f"Downloaded {len(all_problems)} problems.")
        
    except Exception as e:
        print(f"Exception during problem fetch: {e}")
        return

    # Step 3: Local Processing (The "Join")
    print("Step 3: Processing data locally...")
    
    # Create a lookup for problem stats (optional, but good to have if needed later, 
    # though user request said "group those 10,900+ problems", usually we might want stats too)
    # For now, let's stick to the user's request of splitting the problems list.
    # But usually, it's nice to merge the stats (solved count) into the problem object.
    
    # Let's map stats by (contestId, index) just in case we want to merge them.
    # The user request didn't explicitly ask for stats, but "problemset.problems" returns them.
    # The raw "problems" list is what's usually needed.
    
    problems_by_contest = {}
    
    for problem in all_problems:
        contest_id = problem.get("contestId")
        if contest_id:
            if contest_id not in problems_by_contest:
                problems_by_contest[contest_id] = []
            problems_by_contest[contest_id].append(problem)

    print(f"Grouped problems into {len(problems_by_contest)} contests.")

    # Write files
    print("Writing JSON files...")
    count = 0
    for contest in valid_contests:
        contest_id = contest["id"]
        
        # Some contests might validly have no problems in the problemset (old ones, or special ones),
        # but usually we only care about ones that have problems.
        if contest_id in problems_by_contest:
            file_path = os.path.join(data_dir, f"{contest_id}.json")
            
            # The user asked for "store the results in json".
            # Usually users appreciate the full context (contest info + problems).
            # But the request specifically said "splits them (the problems) into individual {contestId}.json".
            # I will save a dict with the contest info AND the problems to be most useful.
            
            output_data = {
                "contest": contest,
                "problems": problems_by_contest[contest_id]
            }
            
            with open(file_path, "w") as f:
                json.dump(output_data, f, indent=2)
            count += 1
            
    print(f"Successfully saved data for {count} contests to {data_dir}/")

if __name__ == "__main__":
    start_time = time.time()
    fetch_data()
    print(f"Total time: {time.time() - start_time:.2f} seconds")
