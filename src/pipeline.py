import os
import pandas as pd
from src.extractors.text_utils import extract_text
from src.extractors.resume_parser import parse_resume
from src.extractors.jd_parser import parse_jd
from src.matchers.rule_based import rule_based_match
from src.matchers.semantic import semantic_match

def process_resume(resume_path, jd_text, jd_parsed, weight_rule=0.6, weight_sem=0.4):
    resume_text = extract_text(resume_path)
    resume_parsed = parse_resume(resume_text)
    
    # 1. Rule-based matching on skills
    rule_score, rule_reasons = rule_based_match(
        resume_parsed['skills'], 
        jd_parsed['required_skills']
    )
    
    # 2. Semantic matching on full text
    sem_score = semantic_match(resume_text, jd_text)
    
    # 3. Combine scores
    final_score = (rule_score * weight_rule) + (sem_score * weight_sem)
    
    return {
        'File': os.path.basename(resume_path),
        'Name': resume_parsed.get('name', 'Unknown'),
        'Email': resume_parsed.get('email', 'Unknown'),
        'Phone': resume_parsed.get('phone', 'Unknown'),
        'Rule_Score': round(rule_score, 2),
        'Semantic_Score': round(sem_score, 2),
        'Final_Score': round(final_score, 2),
        'Reasons': rule_reasons
    }

def rank_resumes(resumes_dir, jd_path, output_csv=None):
    jd_text = extract_text(jd_path)
    jd_parsed = parse_jd(jd_text)
    
    results = []
    
    for filename in os.listdir(resumes_dir):
        if filename.endswith('.pdf') or filename.endswith('.docx') or filename.endswith('.txt'):
            resume_path = os.path.join(resumes_dir, filename)
            try:
                res = process_resume(resume_path, jd_text, jd_parsed)
                results.append(res)
            except Exception as e:
                print(f"Error processing {filename}: {e}")
                
    df = pd.DataFrame(results)
    if not df.empty:
        # Sort by Final_Score descending
        df = df.sort_values(by='Final_Score', ascending=False)
        
        if output_csv:
            df.to_csv(output_csv, index=False)
            
    return df
