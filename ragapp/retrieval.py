"""Küçük yerel veri kümeleri için BM25 ve reciprocal rank fusion."""
from collections import Counter
import math
import re
import unicodedata


# Kod tanımlayıcıları ve tek harfli seçenekler (ör. w) korunur.
STOPWORDS = frozenset("bir bu şu ve veya ile için nasıl nedir hangi ne mı mi mu mü da de the an is of to and".split())


def tokenize(text):
    normalized = unicodedata.normalize("NFKC", text).casefold().replace("i\u0307", "i")
    return [word for word in re.findall(r"\w+", normalized) if word not in STOPWORDS]


def lexical_scores(question, contents):
    """Dönüş: her parça için (BM25 puanı, eşleşen sorgu terimleri)."""
    documents = [Counter(tokenize(content)) for content in contents]
    if not documents:
        return []
    query = set(tokenize(question))
    frequencies = Counter(term for doc in documents for term in doc)
    lengths = [sum(doc.values()) for doc in documents]
    average = sum(lengths) / len(documents) or 1.0
    results = []
    for doc, length in zip(documents, lengths):
        terms = sorted(query.intersection(doc))
        score = 0.0
        for term in terms:
            idf = math.log1p((len(documents) - frequencies[term] + 0.5) / (frequencies[term] + 0.5))
            tf = doc[term]
            score += idf * tf * 2.2 / (tf + 1.2 * (0.25 + 0.75 * length / average))
        results.append((score, tuple(terms)))
    return results


def rank_candidates(question, candidates, threshold, mode):
    """candidates: (Chunk, cosine). Puanlar olasılık veya doğruluk garantisi değildir."""
    if mode not in {"semantic", "hybrid"}:
        raise ValueError("Arama modu semantic veya hybrid olmalı.")
    ordered = sorted(candidates, key=lambda item: (-item[1], item[0].source, item[0].page, item[0].position))
    if mode == "semantic":
        return [(chunk, score, 0.0, 0.0, ()) for chunk, score in ordered if score >= threshold]
    lexical = lexical_scores(question, [chunk.content for chunk, _ in ordered])
    # Uzun soruda tek ortak sözcük eşik altındaki bir parçayı tek başına kurtarmasın.
    # Tek terimlik kod sorgularında ise o terimin tam eşleşmesi yeterlidir.
    minimum_matches = min(2, len(set(tokenize(question)))) or 1
    # Sıralama ile eşik altındaki parçaları içeri alma farklı kararlardır.
    # Eşik üstündeki belgede tek bir tam eşleşme de sıralamaya katkı yapar.
    # Eşik altını kurtarmak için uzun sorudaki iki eşleşme şartı korunur.
    lexical_order = sorted((i for i, (score, terms) in enumerate(lexical)
                            if score > 0),
                           key=lambda i: (-lexical[i][0], i))
    lexical_ranks = {index: rank for rank, index in enumerate(lexical_order, 1)}
    result = []
    for i, (chunk, cosine_score) in enumerate(ordered):
        bm25, terms = lexical[i]
        if cosine_score < threshold and len(terms) < minimum_matches:
            continue
        fusion = 1 / (60 + i + 1)
        if i in lexical_ranks:
            fusion += 1 / (60 + lexical_ranks[i])
        result.append((chunk, cosine_score, bm25, fusion, terms))
    return sorted(result, key=lambda item: (-item[3], -item[1], item[0].source, item[0].page, item[0].position))
