def rule_based_match(resume_skills, jd_skills):
    """
    Compare resume skills against JD required skills.
    Returns a 0-100 score and a human-readable reason string.
    """
    if not jd_skills:
        return 0.0, "No required skills listed in JD."

    resume_set = set(s.lower() for s in resume_skills)
    jd_set = set(s.lower() for s in jd_skills)

    found = sorted(jd_set & resume_set)
    missing = sorted(jd_set - resume_set)

    score = (len(found) / len(jd_set)) * 100 if jd_set else 0.0

    found_str = ", ".join(found) if found else "None"
    missing_str = ", ".join(missing) if missing else "None"
    reasons = f"Found: {found_str}; Missing: {missing_str}"

    return round(score, 2), reasons
