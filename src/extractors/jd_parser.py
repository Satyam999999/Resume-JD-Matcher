import json
import os
import re

SKILLS_DICT_PATH = 'data/skills_dict.json'

def _load_skills_config():
    if os.path.exists(SKILLS_DICT_PATH):
        with open(SKILLS_DICT_PATH, 'r') as f:
            return json.load(f)
    return {"skills": [], "synonyms": {}}

def _normalize_text(text):
    """Apply synonym mapping to normalize skill mentions."""
    config = _load_skills_config()
    synonyms = config.get("synonyms", {})
    text_lower = text.lower()
    for variant, canonical in synonyms.items():
        text_lower = re.sub(r'\b' + re.escape(variant) + r'\b', canonical, text_lower)
    return text_lower

def extract_jd_skills(text, skills_dict_path=SKILLS_DICT_PATH):
    config = _load_skills_config()
    known_skills = config.get("skills", [])
    normalized_text = _normalize_text(text)
    extracted = []
    for skill in known_skills:
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, normalized_text):
            extracted.append(skill)
    return extracted

def parse_jd(text):
    return {
        'required_skills': extract_jd_skills(text)
    }
