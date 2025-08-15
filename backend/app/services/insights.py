def make_sprint_insights(issues) -> dict:
    return {
        "completed": 0,
        "remaining": 0,
        "total_issues": 0,
        "contributors": [],
        "scope_changes": [],
        "burndown": []
    }