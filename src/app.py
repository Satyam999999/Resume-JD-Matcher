import streamlit as st
import tempfile
import os
import pandas as pd

from extractors.text_utils import extract_text
from extractors.resume_parser import parse_resume
from extractors.jd_parser import parse_jd
from matchers.rule_based import rule_based_match
from matchers.semantic import semantic_match

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Resume ↔ JD Matcher",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Dark gradient background */
.stApp {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    min-height: 100vh;
}

/* Glassmorphism cards */
.glass-card {
    background: rgba(255, 255, 255, 0.07);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 20px;
}

/* Score ring container */
.score-container {
    text-align: center;
    padding: 20px;
}

.score-number {
    font-size: 4rem;
    font-weight: 700;
    background: linear-gradient(135deg, #a78bfa, #60a5fa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1;
}

.score-label {
    color: rgba(255,255,255,0.5);
    font-size: 0.85rem;
    margin-top: 4px;
    letter-spacing: 1px;
    text-transform: uppercase;
}

/* Badge */
.badge {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.5px;
}
.badge-good  { background: rgba(52,211,153,0.15); color: #34d399; border: 1px solid rgba(52,211,153,0.3); }
.badge-ok    { background: rgba(251,191,36,0.15);  color: #fbbf24; border: 1px solid rgba(251,191,36,0.3);  }
.badge-poor  { background: rgba(248,113,113,0.15); color: #f87171; border: 1px solid rgba(248,113,113,0.3); }

/* Skill chips */
.skill-found   { display:inline-block; margin:3px; padding:4px 10px; border-radius:12px;
                  background:rgba(52,211,153,0.12); color:#34d399;
                  border:1px solid rgba(52,211,153,0.25); font-size:0.78rem; }
.skill-missing { display:inline-block; margin:3px; padding:4px 10px; border-radius:12px;
                  background:rgba(248,113,113,0.12); color:#f87171;
                  border:1px solid rgba(248,113,113,0.25); font-size:0.78rem; }

/* Section headers */
h1 { color: #fff !important; font-weight: 700; }
h2, h3 { color: rgba(255,255,255,0.85) !important; font-weight: 600; }

/* Streamlit element overrides */
.stFileUploader > div { background: rgba(255,255,255,0.05) !important; border-radius: 12px !important; }
.stButton > button {
    background: linear-gradient(135deg, #7c3aed, #4f46e5) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    padding: 0.5rem 2rem !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(124, 58, 237, 0.4) !important;
}

/* Dataframe */
.stDataFrame { border-radius: 12px; overflow: hidden; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: rgba(255,255,255,0.03) !important;
    border-right: 1px solid rgba(255,255,255,0.08);
}
</style>
""", unsafe_allow_html=True)


# ── Helpers ────────────────────────────────────────────────────────────────────
def save_uploaded_file(uploaded_file):
    ext = uploaded_file.name.split('.')[-1]
    fd, path = tempfile.mkstemp(suffix=f".{ext}")
    with os.fdopen(fd, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    return path

def score_to_badge(score):
    if score >= 60:
        return '<span class="badge badge-good">Good Match</span>'
    elif score >= 30:
        return '<span class="badge badge-ok">Partial Match</span>'
    else:
        return '<span class="badge badge-poor">Poor Match</span>'

def render_skill_chips(found_str, missing_str):
    found = [s.strip() for s in found_str.split(",") if s.strip() and s.strip() != "None"]
    missing = [s.strip() for s in missing_str.split(",") if s.strip() and s.strip() != "None"]
    html = ""
    if found:
        html += "<div style='margin-bottom:8px;'><strong style='color:rgba(255,255,255,0.6);font-size:0.78rem;'>✅ MATCHED</strong><br>"
        html += "".join(f'<span class="skill-found">{s}</span>' for s in found[:20])
        if len(found) > 20:
            html += f'<span style="color:rgba(255,255,255,0.4);font-size:0.75rem;"> +{len(found)-20} more</span>'
        html += "</div>"
    if missing:
        html += "<div><strong style='color:rgba(255,255,255,0.6);font-size:0.78rem;'>❌ MISSING</strong><br>"
        html += "".join(f'<span class="skill-missing">{s}</span>' for s in missing[:20])
        if len(missing) > 20:
            html += f'<span style="color:rgba(255,255,255,0.4);font-size:0.75rem;"> +{len(missing)-20} more</span>'
        html += "</div>"
    return html

def process_single(resume_path, jd_text, jd_parsed, w_rule=0.6, w_sem=0.4):
    resume_text = extract_text(resume_path)
    resume_parsed = parse_resume(resume_text)
    rule_score, reasons = rule_based_match(resume_parsed['skills'], jd_parsed['required_skills'])
    sem_score = semantic_match(resume_text, jd_text)
    final_score = round(rule_score * w_rule + sem_score * w_sem, 2)
    return resume_text, resume_parsed, rule_score, sem_score, final_score, reasons


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Scoring Weights")
    st.caption("Rule-based focuses on exact skill matches. Semantic captures contextual similarity.")
    w_rule = st.slider("Rule-Based Weight", 0.0, 1.0, 0.60, 0.05)
    w_sem  = round(1.0 - w_rule, 2)
    st.metric("Semantic Weight", f"{w_sem:.2f}")
    st.divider()
    st.markdown("### 📊 Score Interpretation")
    st.markdown('<span class="badge badge-good">≥ 60</span> Good Match', unsafe_allow_html=True)
    st.markdown('<span class="badge badge-ok">30 – 59</span> Partial Match', unsafe_allow_html=True)
    st.markdown('<span class="badge badge-poor">< 30</span> Poor Match', unsafe_allow_html=True)
    st.divider()
    st.caption("Built with spaCy · sentence-transformers · Streamlit")


# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding: 2rem 0 1rem;">
    <div style="font-size:3rem; margin-bottom:8px;">🎯</div>
    <h1 style="font-size:2.4rem; margin:0;">Resume ↔ JD Matcher</h1>
    <p style="color:rgba(255,255,255,0.5); font-size:1rem; margin-top:8px;">
        AI-powered resume screening with rule-based + semantic matching
    </p>
</div>
""", unsafe_allow_html=True)

# ── Mode selector ──────────────────────────────────────────────────────────────
mode = st.radio(
    "Select Mode",
    ["🔍 Single Resume Match", "📋 Batch Ranking (Multiple Resumes)"],
    horizontal=True,
    label_visibility="collapsed"
)
st.markdown("---")


# ════════════════════════════════════════════════════════════════════════════════
# MODE 1: Single Resume Match
# ════════════════════════════════════════════════════════════════════════════════
if mode == "🔍 Single Resume Match":
    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.markdown("#### 📄 Job Description")
        jd_file = st.file_uploader("Upload JD", type=["txt", "pdf", "docx"], key="jd_single", label_visibility="collapsed")
    with col2:
        st.markdown("#### 👤 Resume")
        resume_file = st.file_uploader("Upload Resume", type=["txt", "pdf", "docx"], key="res_single", label_visibility="collapsed")

    if jd_file and resume_file:
        if st.button("⚡ Calculate Match", use_container_width=True):
            with st.spinner("Analyzing resume against JD…"):
                jd_path = save_uploaded_file(jd_file)
                res_path = save_uploaded_file(resume_file)
                jd_text = extract_text(jd_path)
                jd_parsed = parse_jd(jd_text)
                resume_text, resume_parsed, rule_score, sem_score, final_score, reasons = \
                    process_single(res_path, jd_text, jd_parsed, w_rule, w_sem)
                os.remove(jd_path)
                os.remove(res_path)

            # ── Result layout ──────────────────────────────────────────────
            st.markdown("---")
            left, mid, right = st.columns([1, 1, 1], gap="medium")

            with left:
                st.markdown(f"""
                <div class="glass-card score-container">
                    <div class="score-number">{final_score:.0f}</div>
                    <div class="score-label">Final Score / 100</div>
                    <div style="margin-top:12px;">{score_to_badge(final_score)}</div>
                </div>
                """, unsafe_allow_html=True)

            with mid:
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.markdown("**Score Breakdown**")
                st.progress(rule_score / 100, text=f"Rule-Based: {rule_score:.1f}/100")
                st.progress(sem_score / 100,  text=f"Semantic:   {sem_score:.1f}/100")
                st.caption(f"Weights → Rule: {w_rule:.0%} · Semantic: {w_sem:.0%}")
                st.markdown('</div>', unsafe_allow_html=True)

            with right:
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.markdown("**Candidate Info**")
                st.markdown(f"👤 **{resume_parsed.get('name') or 'Unknown'}**")
                st.markdown(f"✉️ {resume_parsed.get('email') or '—'}")
                st.markdown(f"📞 {resume_parsed.get('phone') or '—'}")
                edu = resume_parsed.get('education', [])
                if edu:
                    st.markdown(f"🎓 {edu[0][:60]}…" if len(edu[0]) > 60 else f"🎓 {edu[0]}")
                st.markdown('</div>', unsafe_allow_html=True)

            # ── Skill chips ────────────────────────────────────────────────
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("**Skill Match Analysis**")
            found_str, missing_str = reasons.split("; Missing: ", 1)
            found_str = found_str.replace("Found: ", "")
            st.markdown(render_skill_chips(found_str, missing_str), unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            # ── JD Required skills summary ─────────────────────────────────
            with st.expander("📋 JD Required Skills"):
                jd_skills = jd_parsed.get('required_skills', [])
                st.markdown(" ".join(f'<span class="skill-found">{s}</span>' for s in jd_skills), unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# MODE 2: Batch Ranking
# ════════════════════════════════════════════════════════════════════════════════
else:
    col1, col2 = st.columns([1, 2], gap="large")
    with col1:
        st.markdown("#### 📄 Job Description")
        jd_file = st.file_uploader("Upload JD", type=["txt", "pdf", "docx"], key="jd_batch", label_visibility="collapsed")
    with col2:
        st.markdown("#### 👥 Resumes (upload multiple)")
        resume_files = st.file_uploader(
            "Upload Resumes", type=["txt", "pdf", "docx"],
            accept_multiple_files=True, key="res_batch", label_visibility="collapsed"
        )

    if jd_file and resume_files:
        st.info(f"Ready to rank **{len(resume_files)} resume(s)** against **{jd_file.name}**")
        if st.button(f"🚀 Rank {len(resume_files)} Resumes", use_container_width=True):
            jd_path = save_uploaded_file(jd_file)
            jd_text = extract_text(jd_path)
            jd_parsed = parse_jd(jd_text)
            os.remove(jd_path)

            results = []
            prog = st.progress(0, text="Processing resumes…")
            for i, rf in enumerate(resume_files):
                res_path = save_uploaded_file(rf)
                try:
                    resume_text, resume_parsed, rule_score, sem_score, final_score, reasons = \
                        process_single(res_path, jd_text, jd_parsed, w_rule, w_sem)
                    found_str, missing_str = reasons.split("; Missing: ", 1)
                    found_str = found_str.replace("Found: ", "")
                    match_label = "Good" if final_score >= 60 else ("OK" if final_score >= 30 else "Poor")
                    results.append({
                        "Rank": None,
                        "File": rf.name,
                        "Name": resume_parsed.get('name') or "—",
                        "Email": resume_parsed.get('email') or "—",
                        "Final Score": final_score,
                        "Rule Score": rule_score,
                        "Semantic Score": sem_score,
                        "Match": match_label,
                        "Skills Found": found_str,
                        "Skills Missing": missing_str,
                    })
                except Exception as e:
                    results.append({
                        "Rank": None, "File": rf.name, "Name": "ERROR", "Email": "—",
                        "Final Score": 0.0, "Rule Score": 0.0, "Semantic Score": 0.0,
                        "Match": "Poor", "Skills Found": "", "Skills Missing": str(e),
                    })
                finally:
                    os.remove(res_path)
                prog.progress((i + 1) / len(resume_files), text=f"Processed {i+1}/{len(resume_files)}")

            prog.empty()

            # Sort and assign ranks
            df = pd.DataFrame(results).sort_values("Final Score", ascending=False).reset_index(drop=True)
            df["Rank"] = df.index + 1

            st.success(f"✅ Ranked {len(df)} resumes!")
            st.markdown("---")

            # ── Summary metrics ──────────────────────────────────────────
            c1, c2, c3 = st.columns(3)
            c1.metric("Best Score", f"{df['Final Score'].max():.1f}", f"by {df.iloc[0]['Name']}")
            c2.metric("Avg Score", f"{df['Final Score'].mean():.1f}")
            c3.metric("Good Matches", int((df['Match'] == 'Good').sum()))

            # ── Ranking table ────────────────────────────────────────────
            st.markdown("#### 🏆 Ranked Candidates")
            display_df = df[["Rank","Name","Email","File","Final Score","Rule Score","Semantic Score","Match"]].copy()

            # Color-code Match column
            def style_match(val):
                if val == "Good":
                    return "background-color: rgba(52,211,153,0.15); color: #34d399;"
                elif val == "OK":
                    return "background-color: rgba(251,191,36,0.15); color: #fbbf24;"
                return "background-color: rgba(248,113,113,0.15); color: #f87171;"

            styled = display_df.style.applymap(style_match, subset=["Match"]) \
                .background_gradient(subset=["Final Score"], cmap="RdYlGn", vmin=0, vmax=100) \
                .format({"Final Score": "{:.1f}", "Rule Score": "{:.1f}", "Semantic Score": "{:.1f}"})

            st.dataframe(styled, use_container_width=True, hide_index=True)

            # ── Skill details per candidate ──────────────────────────────
            st.markdown("#### 🔬 Per-Candidate Skill Breakdown")
            for _, row in df.iterrows():
                with st.expander(f"#{row['Rank']} {row['Name']} ({row['File']}) — {row['Final Score']:.1f}/100"):
                    st.markdown(render_skill_chips(row["Skills Found"], row["Skills Missing"]),
                                unsafe_allow_html=True)

            # ── Download CSV ─────────────────────────────────────────────
            st.markdown("---")
            csv_data = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="⬇️ Download Full Rankings CSV",
                data=csv_data,
                file_name="ranked_candidates.csv",
                mime="text/csv",
                use_container_width=True,
            )
