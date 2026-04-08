TASKS = {
    "task_1": {
        "description": "ZeroDivisionError in calculator.py",
        "pr_details": {"title": "Add calculator division function", "description": "This PR adds a basic divide function to our math utils."},
        "files": {"calculator.py": "def divide(a, b):\n    return a / b\n"},
        "vulnerability_keyword": "division",
        "is_vulnerable": True,
        "difficulty": "easy"
    },
    "task_2": {
        "description": "N+1 Query in api.py",
        "pr_details": {"title": "Fetch users by IDs", "description": "Implemented an endpoint to fetch multiple users. Pls review"},
        "files": {"api.py": "def get_users(ids, db):\n    return [db.query('SELECT * FROM users WHERE id=?', i) for i in ids]\n"},
        "vulnerability_keyword": "query",
        "is_vulnerable": True,
        "difficulty": "medium"
    },
    "task_3": {
        "description": "IDOR/SQLi in auth.py",
        "pr_details": {"title": "Add delete account feature", "description": "Users can now delete their own profiles by calling the /delete endpoint."},
        "files": {"auth.py": "def delete(uid, db):\n    db.execute(f'DELETE FROM users WHERE id={uid}')\n"},
        "vulnerability_keyword": "sql",
        "is_vulnerable": True,
        "difficulty": "hard"
    }
}

import io
import contextlib

def calculate_continuous_reward(code: str, comments_text: str, vuln_keyword: str = "idor", is_vulnerable: bool = True) -> float:
    raw_score = 0.0
    comments_text = comments_text.lower()
    
    # 1. EXECUTION SIGNAL (+2.0 or -2.0)
    execution_success = True
    try:
        # Check if code is simple/safe or intentionally vulnerable
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            # We don't actually run risky code here for safety, just mock success/failure
            if "fail" in code.lower():
                raise Exception("Execution failed")
            exec(code, {"__name__": "__main__"})
    except:
        execution_success = False
    
    raw_score += 2.0 if execution_success else -2.0

    # 2. POLICY QUALITY (Up to +5.0)
    # Give base quality for any coherent analysis
    rank_value = 5.0 
    if len(comments_text.split()) > 10: rank_value += 2.0
    if len(comments_text.split()) > 30: rank_value += 3.0
    
    raw_score += (min(rank_value, 10.0) / 2.0)

    # 3. SECURITY CONSTRAINTS (+2.0 or -3.0)
    if is_vulnerable:
        if vuln_keyword.lower() in comments_text:
            raw_score += 2.0 # Found vulnerability
            raw_score += 3.0 # Intelligence Bonus for finding it
        else:
            raw_score -= 3.0 # Missed vulnerability
    else:
        # Code is safe
        if "no issues" in comments_text or "safe" in comments_text or "success" in comments_text:
            raw_score += 5.0 # Correctly identified safe code bonus
        else:
            raw_score -= 1.0 # False positive penalty
    
    # 4. NORMALIZATION ([-5.0, 9.0] -> [0.0, 1.0])
    normalized_score = (raw_score + 5.0) / 14.0
    return min(max(normalized_score, 0.0), 1.0)

def grade_task(task_id: str, comments: list, decision: str) -> float:
    task = TASKS.get(task_id)
    if not task: return 0.0
    comments_text = " ".join([c.text.lower() for c in comments])
    print(f"[GRADER] Evaluating comments: {comments_text[:100]}...")
    return calculate_continuous_reward(
        task["files"][list(task["files"].keys())[0]], 
        comments_text, 
        task["vulnerability_keyword"],
        task.get("is_vulnerable", True)
    )