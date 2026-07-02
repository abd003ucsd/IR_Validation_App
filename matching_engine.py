from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import streamlit as st
from thefuzz import process as fuzz_process


@st.cache_data
def get_embedding(text: str) -> Optional[List[float]]:
    """Return an Ollama embedding for a text value."""
    try:
        import ollama

        response = ollama.embeddings(model="nomic-embed-text", prompt=text)
        return [float(x) for x in response["embedding"]]
    except Exception:
        return None


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    dot = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return float(dot / (norm1 * norm2))


@st.cache_data
def suggest_fuzzy_matches(
    cols1: List[str],
    cols2: List[str],
    threshold: int = 60,
) -> Dict[str, Tuple[str, int]]:
    """Suggest column matches using fuzzy string matching."""
    matches: Dict[str, Tuple[str, int]] = {}
    for col1 in cols1:
        if col1 in cols2:
            matches[col1] = (col1, 100)
            continue

        cols2_lower = [c.lower() for c in cols2]
        if col1.lower() in cols2_lower:
            idx = cols2_lower.index(col1.lower())
            matches[col1] = (cols2[idx], 99)
            continue

        best_match, score = fuzz_process.extractOne(col1, cols2)
        if score >= threshold:
            matches[col1] = (best_match, score)

    return matches


@st.cache_data
def suggest_ollama_matches(
    cols1: List[str],
    cols2: List[str],
    threshold: float = 0.75,
) -> Dict[str, Tuple[str, float]]:
    """Suggest column matches using Ollama embeddings and cosine similarity."""
    try:
        import ollama

        embeddings_1 = {col: np.array(get_embedding(col)) for col in cols1}
        embeddings_2 = {col: np.array(get_embedding(col)) for col in cols2}

        embeddings_1 = {k: v for k, v in embeddings_1.items() if v is not None and v.size > 0}
        embeddings_2 = {k: v for k, v in embeddings_2.items() if v is not None and v.size > 0}

        if not embeddings_1 or not embeddings_2:
            return {}

        matches: Dict[str, Tuple[str, float]] = {}
        for col1, emb1 in embeddings_1.items():
            best_col2 = None
            best_score = 0.0

            for col2, emb2 in embeddings_2.items():
                score = cosine_similarity(emb1, emb2)
                if score > best_score:
                    best_score = score
                    best_col2 = col2

            if best_score >= threshold:
                matches[col1] = (best_col2, best_score)

        return matches
    except Exception:
        return {}


def suggest_matches(
    cols1: List[str],
    cols2: List[str],
    matcher: str = "thefuzz",
    threshold: Optional[Union[int, float]] = None,
) -> Dict[str, str]:
    """Unified interface for column matching with hybrid logic and deduplication."""
    initial_matches = suggest_fuzzy_matches(cols1, cols2, threshold=85)

    b_to_a_best: Dict[str, Tuple[str, float]] = {}
    for col_a, (col_b, score) in initial_matches.items():
        if col_b not in b_to_a_best or score > b_to_a_best[col_b][1]:
            b_to_a_best[col_b] = (col_a, float(score))

    matched_cols1 = {v[0] for v in b_to_a_best.values()}
    remaining_cols1 = [c for c in cols1 if c not in matched_cols1]

    if remaining_cols1:
        if matcher == "ollama":
            if threshold is None or not isinstance(threshold, float):
                threshold = 0.75

            semantic_matches = suggest_ollama_matches(remaining_cols1, cols2, threshold)
            if not semantic_matches and matcher == "ollama":
                st.warning("Ollama returned no matches — falling back to fuzzy matching automatically.")

            for col_a, (col_b, score) in semantic_matches.items():
                if col_b not in b_to_a_best:
                    b_to_a_best[col_b] = (col_a, float(score))
                elif b_to_a_best[col_b][1] < 85 and float(score) > b_to_a_best[col_b][1]:
                    b_to_a_best[col_b] = (col_a, float(score))
        else:
            if threshold is None or not isinstance(threshold, int):
                threshold = 60

            remaining_fuzzy = suggest_fuzzy_matches(remaining_cols1, cols2, threshold)
            for col_a, (col_b, score) in remaining_fuzzy.items():
                if col_b not in b_to_a_best or score > b_to_a_best[col_b][1]:
                    b_to_a_best[col_b] = (col_a, float(score))

    return {col_a: col_b for col_b, (col_a, _) in b_to_a_best.items()}


@st.cache_resource(show_spinner=False, ttl=600)
def check_ollama() -> bool:
    """Return True when Ollama is reachable on the local machine."""
    try:
        import requests

        response = requests.get("http://localhost:11434/api/tags", timeout=1.0)
        return response.status_code == 200
    except Exception:
        return False


@st.cache_data
def calculate_union_count(df_a: pd.DataFrame, df_b: pd.DataFrame, key_a, key_b, case_sensitive: bool = False) -> int:
    """Return the number of unique keys across both dataframes.

    Supports both single-key (str) and composite-key (list of str) arguments.
    """
    keys_a = [key_a] if isinstance(key_a, str) else list(key_a)
    keys_b = [key_b] if isinstance(key_b, str) else list(key_b)

    def _mk_key(df, cols, cs):
        result = df[cols].astype(str).apply("|".join, axis=1).str.strip()
        if not cs:
            result = result.str.upper()
        return result

    normalized_keys_a = _mk_key(df_a, keys_a, case_sensitive)
    normalized_keys_b = _mk_key(df_b, keys_b, case_sensitive)
    return int(pd.concat([normalized_keys_a, normalized_keys_b]).nunique())
