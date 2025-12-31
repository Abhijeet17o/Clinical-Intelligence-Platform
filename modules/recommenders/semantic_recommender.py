"""
Semantic Similarity Recommender (local)

Uses a local SentenceTransformer to compute relevance scores between patient symptoms
and medicine descriptions. Falls back to a TF-IDF cosine similarity if SentenceTransformer
is not available in the environment.
"""
import numpy as np
from typing import List, Dict
import logging
import os
import json

# Try to use SentenceTransformer locally; fallback to TF-IDF if not available
try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None

from scipy.spatial.distance import cosine
from .base_recommender import BaseRecommender

logger = logging.getLogger(__name__)


class SemanticRecommender(BaseRecommender):
    """
    Local Semantic Recommender using SentenceTransformer embeddings (local only).

    Falls back to a TF-IDF cosine similarity if SentenceTransformer is not installed.
    """

    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """Initialize and set up lazy-loading for the local model."""
        self.model_name = model_name
        self._model = None

    @property
    def model(self):
        """Lazy-load the SentenceTransformer model if available."""
        if self._model is None:
            if SentenceTransformer is None:
                logger.warning('SentenceTransformer not available; will use TF-IDF fallback')
                self._model = None
            else:
                logger.info(f'Loading SentenceTransformer model: {self.model_name}')
                self._model = SentenceTransformer(self.model_name)
                logger.info('✓ SentenceTransformer loaded')
        return self._model

    def get_name(self) -> str:
        return 'semantic'

    def recommend(self, symptoms: str, medicines: List[Dict]) -> np.ndarray:
        """Return similarity scores between symptoms and each medicine.

        Uses SentenceTransformer if available, otherwise TF-IDF vector similarity.
        """
        if not symptoms or not medicines:
            return np.zeros(len(medicines))

        medicine_texts = [f"{m['name']}: {m.get('description','')}" for m in medicines]

        # Try sentence-transformers
        try:
            model = self.model
            if model is not None:
                # encode returns numpy arrays
                sym_emb = model.encode([symptoms], convert_to_numpy=True)[0]
                meds_emb = model.encode(medicine_texts, convert_to_numpy=True)

                scores = []
                for i in range(len(meds_emb)):
                    a = sym_emb
                    b = meds_emb[i]
                    # handle edge cases
                    try:
                        sim = 1.0 - cosine(a, b)
                        if sim != sim:  # NaN
                            sim = 0.0
                    except Exception:
                        sim = 0.0
                    scores.append(max(0.0, min(1.0, float(sim))))
                return np.array(scores)
        except Exception as e:
            logger.warning(f'SentenceTransformer scoring failed: {e} — falling back to TF-IDF')

        # Fallback: TF-IDF cosine similarity
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            vec = TfidfVectorizer(max_features=2000)
            corpus = [symptoms] + medicine_texts
            X = vec.fit_transform(corpus)
            sym_v = X[0].toarray()[0]
            meds_v = X[1:].toarray()
            scores = []
            for v in meds_v:
                try:
                    sim = 1.0 - cosine(sym_v, v)
                    if sim != sim:
                        sim = 0.0
                except Exception:
                    sim = 0.0
                scores.append(max(0.0, min(1.0, float(sim))))
            return np.array(scores)
        except Exception as e:
            logger.error(f'No viable local method for semantic scoring: {e}')
            # As a last resort, return zeros
            return np.zeros(len(medicines))

    def get_feature_contributions(self, symptoms: str, medicine: Dict) -> Dict[str, float]:
        """Estimate feature contributions based on word overlap."""
        symptom_words = symptoms.lower().split()
        med_text = f"{medicine['name']}: {medicine.get('description', '')}".lower()
        contributions = {}
        for word in symptom_words:
            if len(word) > 3:
                contributions[word] = 0.3 if word in med_text else 0.1
        total = sum(contributions.values())
        if total > 0:
            contributions = {k: v/total for k, v in contributions.items()}
        return contributions
