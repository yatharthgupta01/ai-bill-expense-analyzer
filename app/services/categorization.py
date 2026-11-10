"""
Automatic expense categorization service using semantic embeddings and contextual heuristics.
"""
from typing import List, Dict, Tuple, Optional
import re
import os

# Standard expense categories with rich contextual descriptions for semantic matching
STANDARD_CATEGORIES: Dict[str, str] = {
    "Food": "restaurants, cafes, dining out, fast food, pizza, burger, breakfast, lunch, dinner, bakery, starbucks, swiggy, zomato, mcdonalds",
    "Groceries": "supermarket, daily essentials, vegetables, fruits, dairy, milk, bread, pantry, supermarket, provisions, mart, dmart, bigbasket, blinkit, zepto",
    "Shopping": "clothing, apparel, fashion, electronics, gadgets, footwear, accessories, amazon, flipkart, zara, retail, online shopping, cosmetics",
    "Transportation": "taxi, cab, ride, uber, ola, auto, bus, train, metro, fuel, petrol, diesel, gas, parking, toll, transit",
    "Travel": "flights, airlines, hotels, resort, stay, tourism, booking.com, airbnb, makemytrip, train ticket, vacation",
    "Utilities": "electricity bill, power, water supply, sewage, gas cylinder, piped gas, broadband, internet, mobile recharge, wifi, dth",
    "Entertainment": "movies, cinema, multiplex, concert, event tickets, netflix, spotify, hotstar, prime video, gaming, amusement park",
    "Healthcare": "pharmacy, medicines, hospital, clinic, doctor consultation, medical tests, lab diagnostics, dentist, prescription drugs, apollo",
    "Education": "tuition fees, college fees, school books, course, certification, udemy, coursera, textbooks, stationary, exam fees",
    "Rent / Housing": "house rent, apartment rent, society maintenance, flat maintenance, landlord, property tax, home repair, plumbing, electrical maintenance",
    "Bills": "credit card bill, insurance premium, subscription renewals, loan emi, mobile postpaid, recurring municipal charges",
    "Other": "miscellaneous, general expenses, unclassified charges, gifts, donations"
}

# Rule-based / Keyword fallback dictionary for fast deterministic matching
KEYWORD_MAPPINGS: Dict[str, List[str]] = {
    "Food": ["restaurant", "cafe", "dhaba", "pizza", "burger", "swiggy", "zomato", "bistro", "coffee", "kitchen", "bar & grill", "bakery", "diner", "subway", "kfc", "domino"],
    "Groceries": ["supermarket", "grocery", "mart", "provisions", "dmart", "blinkit", "zepto", "bigbasket", "fruits", "vegetables", "kirana", "spices", "dairy", "milk"],
    "Shopping": ["amazon", "flipkart", "myntra", "retail", "clothing", "apparel", "electronics", "store", "mall", "fashion", "footwear", "zara", "h&m", "croma", "reliance digital"],
    "Transportation": ["uber", "ola", "fuel", "petrol", "diesel", "hpcl", "bpcl", "iocl", "metro", "bus", "taxi", "cab", "parking", "toll", "fastag"],
    "Travel": ["hotel", "resort", "airline", "airways", "flight", "makemytrip", "airbnb", "goibibo", "irctc", "boarding pass", "railway ticket"],
    "Utilities": ["electricity", "power", "water board", "gas bill", "broadband", "wifi", "airtel", "jio", "vi", "bsnl", "bescom", "tneb", "torrent power", "act fibernet"],
    "Entertainment": ["pvr", "inox", "cinema", "theatre", "movie", "netflix", "spotify", "prime", "hotstar", "bookmyshow", "concert", "game"],
    "Healthcare": ["pharmacy", "medical", "chemist", "hospital", "clinic", "doctor", "diagnostic", "pathology", "apollo", "medplus", "1mg", "pharmeasy"],
    "Education": ["university", "college", "school", "tuition", "academy", "udemy", "coursera", "bookstore", "stationery", "exam", "education"],
    "Rent / Housing": ["rent", "landlord", "maintenance", "society", "realty", "apartment", "housing", "plumbing", "carpenter"],
    "Bills": ["credit card", "billdesk", "emi", "insurance", "lic", "policy", "premium", "postpaid", "tax payment"]
}

_SENTENCE_MODEL = None
_MODEL_TRIED = False

def _get_sentence_transformer():
    """Lazily load sentence-transformers model if available."""
    global _SENTENCE_MODEL, _MODEL_TRIED
    if _SENTENCE_MODEL is None and not _MODEL_TRIED:
        _MODEL_TRIED = True
        try:
            from sentence_transformers import SentenceTransformer
            # Use cached model if present, or all-MiniLM-L6-v2
            _SENTENCE_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception:
            _SENTENCE_MODEL = None
    return _SENTENCE_MODEL

class CategorizationService:
    """Service to classify expenses using semantic similarity and keyword heuristics."""

    def __init__(self, custom_categories: Optional[Dict[str, str]] = None):
        self.categories = dict(STANDARD_CATEGORIES)
        if custom_categories:
            self.categories.update(custom_categories)
        self._category_embeddings = None

    def add_category(self, name: str, description: str):
        """Allow dynamic addition of custom categories."""
        self.categories[name] = description
        self._category_embeddings = None  # invalidate cache

    def _keyword_classify(self, text: str) -> Optional[Tuple[str, float]]:
        """Fast keyword-based rule matching."""
        text_lower = text.lower()
        best_cat = None
        best_score = 0.0

        for cat, keywords in KEYWORD_MAPPINGS.items():
            matches = sum(1 for kw in keywords if re.search(r"\b" + re.escape(kw) + r"\b", text_lower))
            if matches > 0:
                score = min(0.95, 0.65 + (matches * 0.1))
                if score > best_score:
                    best_score = score
                    best_cat = cat

        if best_cat:
            return best_cat, best_score
        return None

    def _semantic_classify(self, text: str) -> Optional[Tuple[str, float]]:
        """Zero-shot semantic matching using transformer embeddings."""
        model = _get_sentence_transformer()
        if model is None:
            return None

        try:
            import numpy as np
            cat_names = list(self.categories.keys())
            cat_descs = [f"{name}: {self.categories[name]}" for name in cat_names]

            if self._category_embeddings is None:
                self._category_embeddings = model.encode(cat_descs, normalize_embeddings=True)

            text_emb = model.encode([text], normalize_embeddings=True)[0]
            scores = np.dot(self._category_embeddings, text_emb)
            best_idx = int(np.argmax(scores))
            best_cat = cat_names[best_idx]
            best_score = float(scores[best_idx])

            # Normalize cosine similarity roughly into [0, 1] confidence
            confidence = max(0.0, min(1.0, best_score))
            return best_cat, confidence
        except Exception:
            return None

    def categorize(
        self,
        merchant: str = "",
        items: Optional[List[str]] = None,
        raw_text: str = ""
    ) -> Tuple[str, float]:
        """
        Classify an expense given merchant name, item names, and raw bill text.
        Returns: (category, confidence)
        """
        items_str = " ".join(items) if items else ""
        combined_text = f"{merchant} {items_str} {raw_text[:300]}".strip()
        
        if not combined_text:
            return "Other", 0.0

        # 1. Try keyword matching first for clear vendor / brand indicators
        kw_result = self._keyword_classify(combined_text)
        if kw_result and kw_result[1] >= 0.75:
            return kw_result

        # 2. Try semantic transformer embedding similarity
        semantic_result = self._semantic_classify(combined_text)
        if semantic_result and semantic_result[1] >= 0.40:
            return semantic_result

        # 3. Fallback to keyword match if any
        if kw_result:
            return kw_result

        return "Other", 0.30

# Singleton instance
categorizer = CategorizationService()
