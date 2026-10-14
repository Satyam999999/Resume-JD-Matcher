import re
import spacy
import json
import os

try:
    nlp = spacy.load('en_core_web_sm')
except Exception:
    nlp = None

SKILLS_DICT_PATH = 'data/skills_dict.json'

def _load_skills_config():
    if os.path.exists(SKILLS_DICT_PATH):
        with open(SKILLS_DICT_PATH, 'r') as f:
            return json.load(f)
    return {"skills": [], "synonyms": {}, "ml_context_keywords": []}

def _normalize_text(text):
    """Apply synonym mapping to normalize skill mentions."""
    config = _load_skills_config()
    synonyms = config.get("synonyms", {})
    text_lower = text.lower()
    for variant, canonical in synonyms.items():
        text_lower = re.sub(r'\b' + re.escape(variant) + r'\b', canonical, text_lower)
    return text_lower

def extract_email(text):
    email_regex = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match = re.search(email_regex, text)
    return match.group(0) if match else None

def extract_phone(text):
    # Handles: (415) 882-9034 | +1 (929) 441-7823 | 555-123-4567 | +91 9876543210
    phone_regex = r'(\+?1?\s?)?(\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4})'
    match = re.search(phone_regex, text)
    return match.group(0).strip() if match else None

def extract_name(text):
    """Use spaCy PERSON entities first; fallback to first short line."""
    if nlp:
        # Only look in first 300 chars — names appear at the top
        doc = nlp(text[:300])
        for ent in doc.ents:
            if ent.label_ == 'PERSON' and 2 <= len(ent.text.split()) <= 4:
                return ent.text
    # Fallback: first line that looks like a name
    for line in text.strip().split('\n')[:5]:
        words = line.strip().split()
        if 1 < len(words) <= 4 and all(w[0].isupper() and w[1:].isalpha() for w in words if w):
            return line.strip()
    return None

def extract_education(text):
    """Extract education lines using degree/institution keywords."""
    edu_keywords = [
        'b.s.', 'b.a.', 'b.e.', 'b.tech', 'btech', 'b.sc',
        'm.s.', 'm.a.', 'm.e.', 'm.tech', 'mtech', 'm.sc', 'mba',
        'ph.d', 'phd', 'doctorate',
        'bachelor', 'master', 'doctor',
        'university', 'college', 'institute of technology', 'iit',
        'carnegie mellon', 'stanford', 'mit', 'harvard', 'uc '
    ]
    extracted_edu = []
    lines = text.split('\n')
    for line in lines:
        line_lower = line.lower()
        for kw in edu_keywords:
            if kw in line_lower and len(line.strip()) > 5:
                extracted_edu.append(line.strip())
                break
    return list(dict.fromkeys(extracted_edu))  # deduplicate while preserving order

def _is_ml_context(text, skill):
    """
    Check whether a skill appears near ML context keywords.
    This helps distinguish 'python in a DevOps script' vs 'python for ML modeling'.
    """
    config = _load_skills_config()
    ml_keywords = config.get("ml_context_keywords", [])
    if not ml_keywords:
        return True  # no context filtering if not configured
    text_lower = text.lower()
    # Find all positions of the skill
    skill_positions = [m.start() for m in re.finditer(r'\b' + re.escape(skill) + r'\b', text_lower)]
    for pos in skill_positions:
        context_window = text_lower[max(0, pos - 200): pos + 200]
        for kw in ml_keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', context_window):
                return True
    return False

def extract_skills(text, skills_dict_path=SKILLS_DICT_PATH, check_ml_context=False):
    """
    Extract skills from text with synonym normalization.
    If check_ml_context=True, only count a skill if it appears near ML context words
    (reduces false positives for generic skills like 'python' in non-ML resumes).
    """
    config = _load_skills_config()
    known_skills = config.get("skills", [])

    # Normalize text using synonym map
    normalized_text = _normalize_text(text)

    extracted = []
    for skill in known_skills:
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, normalized_text):
            if check_ml_context:
                # Only flag generic skills if they appear near ML context
                generic_skills = {"python", "sql", "java", "r", "aws", "gcp", "google cloud", "azure", "git", "linux"}
                if skill in generic_skills and not _is_ml_context(normalized_text, skill):
                    continue
            extracted.append(skill)
    return extracted

def _extract_section(text, section_headers):
    """
    Extract text from a specific section (e.g., 'SKILLS', 'EXPERIENCE').
    Returns the section text or falls back to full text.
    """
    lines = text.split('\n')
    in_section = False
    section_text = []
    section_end_keywords = [
        'education', 'experience', 'skills', 'summary', 'objective',
        'publications', 'certifications', 'projects', 'awards', 'references'
    ]
    for line in lines:
        line_lower = line.lower().strip()
        # Check if we hit our target section
        if any(h in line_lower for h in section_headers) and len(line.strip()) < 40:
            in_section = True
            continue
        # Check if we've moved into another section
        if in_section:
            if any(
                end_kw in line_lower and len(line.strip()) < 40
                for end_kw in section_end_keywords
                if end_kw not in section_headers
            ):
                break
            section_text.append(line)
    return '\n'.join(section_text) if section_text else text

def extract_skills_section_aware(text):
    """
    Extract skills from SKILLS and EXPERIENCE sections separately,
    giving higher confidence to skills listed in the SKILLS section.
    Returns combined deduplicated list.
    """
    # Try to extract from dedicated skills section first
    skills_section = _extract_section(text, ['skills', 'technical skills', 'core competencies', 'technologies'])
    exp_section = _extract_section(text, ['experience', 'work experience', 'professional experience'])

    skills_from_skills_section = extract_skills(skills_section, check_ml_context=False)
    skills_from_exp = extract_skills(exp_section, check_ml_context=True)

    # Merge: skills section is authoritative, experience adds context-validated extras
    combined = list(dict.fromkeys(skills_from_skills_section + skills_from_exp))
    return combined

def parse_resume(text, section_aware=True):
    """Parse resume text into structured fields."""
    return {
        'name': extract_name(text),
        'email': extract_email(text),
        'phone': extract_phone(text),
        'education': extract_education(text),
        'skills': extract_skills_section_aware(text) if section_aware else extract_skills(text)
    }
