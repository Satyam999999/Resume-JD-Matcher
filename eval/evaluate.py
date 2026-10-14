import os
import sys
import pandas as pd
from sklearn.metrics import classification_report, precision_recall_fscore_support

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pipeline import process_resume
from src.extractors.text_utils import extract_text
from src.extractors.jd_parser import parse_jd

def score_to_label(score):
    if score >= 60:
        return "Good"
    elif score >= 30:
        return "OK"
    else:
        return "Poor"

def run_evaluation():
    labels_file = "eval/labels.csv"
    if not os.path.exists(labels_file):
        print("Labels file not found. Run generate_data.py first.")
        return

    df = pd.read_csv(labels_file)
    
    y_true = []
    y_pred = []
    results = []

    for index, row in df.iterrows():
        resume_name = row['Resume']
        jd_name = row['JD']
        true_label = row['True_Label']
        
        resume_path = os.path.join("data/resumes", resume_name)
        jd_path = os.path.join("data/jds", jd_name)
        
        jd_text = extract_text(jd_path)
        jd_parsed = parse_jd(jd_text)
        
        try:
            res = process_resume(resume_path, jd_text, jd_parsed)
            pred_label = score_to_label(res['Final_Score'])
            
            y_true.append(true_label)
            y_pred.append(pred_label)
            
            results.append({
                'Resume': resume_name,
                'JD': jd_name,
                'True_Label': true_label,
                'Pred_Label': pred_label,
                'Score': res['Final_Score'],
                'Reasons': res['Reasons']
            })
        except Exception as e:
            print(f"Error evaluating {resume_name}: {e}")
            
    # Calculate metrics
    print("Evaluation Results:\n")
    print(classification_report(y_true, y_pred, target_names=["Good", "OK", "Poor"], zero_division=0))
    
    # Save detailed results
    results_df = pd.DataFrame(results)
    results_df.to_csv("eval/eval_results.csv", index=False)
    print("Detailed results saved to eval/eval_results.csv")

if __name__ == "__main__":
    run_evaluation()
