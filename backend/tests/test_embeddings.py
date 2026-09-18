import pytest
from researchvault.embeddings.fast_numpy_provider import FastNumpyFallbackProvider


def test_fast_numpy_embedding():
    provider = FastNumpyFallbackProvider(dimension=128)
    assert provider.get_dimension() == 128

    vec1 = provider.generate_embedding("Retrieval-Augmented Generation for NLP")
    vec2 = provider.generate_embedding("Dense passage retrieval and transformer embeddings")
    vec3 = provider.generate_embedding("Quantum thermodynamics and molecular dynamics")

    assert len(vec1) == 128
    assert len(vec2) == 128
    
    # Compute dot product (cosine similarity since normalized)
    import numpy as np
    sim_1_2 = float(np.dot(vec1, vec2))
    sim_1_3 = float(np.dot(vec1, vec3))
    
    # Vectors should be valid floats
    assert -1.0 <= sim_1_2 <= 1.0
    assert -1.0 <= sim_1_3 <= 1.0


def test_batch_embedding():
    provider = FastNumpyFallbackProvider(dimension=64)
    texts = ["Machine Learning", "Artificial Intelligence", "Deep Neural Networks"]
    batch = provider.generate_batch_embeddings(texts)
    assert len(batch) == 3
    assert len(batch[0]) == 64
