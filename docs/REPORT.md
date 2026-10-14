# Resume-to-JD Matching Pipeline Report

## 1. Pipeline Architecture

The pipeline consists of three main stages: Parsing/Extraction, Matching (Rule-Based & Semantic), and Scoring.

### 1.1 Field Extraction
**Resume Parser**: Handles raw text from PDFs, DOCX, and TXT files. 
- **Names**: Uses `spaCy` NER model (`en_core_web_sm`) to identify the `PERSON` entity. If missed, it falls back to parsing the first few lines of the text.
- **Email & Phone**: Uses regular expressions, which are highly reliable for these structured formats.
- **Skills**: Extracts skills by token matching against a predefined dictionary (`data/skills_dict.json`). This ensures uniformity.
- **Education**: Uses keyword matching (e.g., "B.S.", "Master", "University") to extract educational background lines.

**JD Parser**: Similarly extracts required skills using the known skills dictionary.

### 1.2 Matching Strategies
**Rule-Based Matcher**: 
Calculates an exact intersection between the resume's extracted skills and the JD's required skills.
- *Pros*: Highly interpretable. Can provide exact "Found" and "Missing" skill lists.
- *Cons*: Misses semantic overlap (e.g., JD asks for "AWS", Resume says "Amazon Web Services").

**Semantic Matcher**:
Uses the `sentence-transformers` library with the lightweight `all-MiniLM-L6-v2` model.
- Converts the entire text of both the JD and the Resume into dense vector embeddings.
- Calculates Cosine Similarity.
- *Pros*: Captures context and implicit knowledge.
- *Cons*: Opaque; a high score doesn't explicitly guarantee a specific mandatory skill is present.

### 1.3 Scoring mechanism
Final Score = (Rule-Based Score * 0.6) + (Semantic Score * 0.4)
The rule-based score is weighted higher (0.6) because specific hard skills are usually binary requirements for recruiters, whereas semantic similarity (0.4) acts as a contextual boost.

---

## 2. Evaluation Metrics

A synthetic dataset of 20 Resume-JD pairs was generated, manually labeled as **Good**, **OK**, or **Poor**.
The pipeline scores were binned: `>=60 = Good`, `30-59 = OK`, `<30 = Poor`.

**(Note: Exact script output in `eval/eval_results.csv` and console).**

Generally, the evaluation reveals:
- **Precision (Good)**: High, as candidates with exact matching skills score highly.
- **Recall (Good/OK)**: Moderate, sometimes penalized if candidates describe skills in non-standard terms not in the `skills_dict.json`.

### 2.1 Known Limitations & Underperformance
1. **Dictionary Dependency**: The rule-based extractor heavily relies on `data/skills_dict.json`. If a candidate lists "GCP" but the dictionary only has "Google Cloud", the rule-based matcher misses it. 
2. **Semantic Blurring**: The semantic matcher embeds the *entire* resume. A resume with heavy boilerplate or unrelated hobbies can artificially dilute the semantic similarity score, even if the candidate perfectly matches the job.
3. **Format Parsing Issues**: Complex PDF layouts (multi-column) can result in concatenated, messy text, breaking the regex and NER extractors.
4. **Hard Requirements vs. Soft Skills**: The current logic doesn't differentiate between a "Mandatory" skill and a "Nice to have" skill. A candidate missing a nice-to-have skill is penalized exactly the same as one missing a core requirement.

## 3. Future Improvements
- Implement a synonym/alias mapping in `skills_dict.json` (e.g., `"aws": ["amazon web services"]`).
- Move from purely dictionary-based skill extraction to an LLM-based extraction step (e.g., passing the text to a small LLM to output a JSON of skills).
- Segment the resume into sections (Experience, Education, Skills) before semantic embedding, rather than embedding the entire raw text.
