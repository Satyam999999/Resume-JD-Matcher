from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def semantic_match(resume_text: str, jd_text: str) -> float:
    """
    Compute semantic similarity between resume and JD using TF-IDF cosine
    similarity. Pure-Python, no PyTorch required — fast and reliable on all
    platforms including macOS Apple Silicon.

    Returns a score in the range [0, 100].
    """
    if not resume_text or not jd_text:
        return 0.0

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),   # unigrams + bigrams for richer context
        sublinear_tf=True,    # log-scale TF to dampen very frequent terms
    )

    try:
        tfidf_matrix = vectorizer.fit_transform([resume_text, jd_text])
        similarity = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])[0][0]
        return max(0.0, float(similarity)) * 100
    except Exception:
        return 0.0

