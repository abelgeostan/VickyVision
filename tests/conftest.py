import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set test environment
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.core.database import Base, get_db
from app.main import app
from app.services.agent_service import AgentService
from app.llm.base import BaseLLMProvider, LLMResponse

# Test In-Memory Database Engine
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class MockLLMProvider(BaseLLMProvider):
    def __init__(self, reply: str = "Mocked LLM agent response."):
        self.reply = reply

    def generate(self, prompt, model, system_prompt=None, options=None):
        return LLMResponse(content=self.reply, model=model, total_duration_ms=42.0)

    def chat(self, messages, model, system_prompt=None, options=None):
        return LLMResponse(content=self.reply, model=model, total_duration_ms=42.0)

    def check_health(self):
        return True

    def list_models(self):
        return ["mock-model:latest", "gemma3:4b"]


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    # Seed default agents for tests
    AgentService.init_default_agents(session)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
