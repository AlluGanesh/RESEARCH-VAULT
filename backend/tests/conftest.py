import pytest
import os
import sys

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set test environment
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_researchvault.db"
os.environ["EMBEDDING_PROVIDER"] = "fast-numpy"
os.environ["DEFAULT_LLM_PROVIDER"] = "mock"
