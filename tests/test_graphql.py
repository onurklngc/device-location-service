import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main_web import app, get_context, database_service
from src.model import Base

TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    # Override the get_db dependency to use the test database session
    def _get_db_override():
        try:
            yield db_session
        finally:
            db_session.close()

    # Override the context to include the test database session
    def _get_context_override():
        return {"db": db_session}

    app.dependency_overrides[database_service.get_db] = _get_db_override
    app.dependency_overrides[get_context] = _get_context_override

    return TestClient(app)


def test_read_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}


def test_create_device(client):
    query = """
    mutation {
        createDevice(input: { name: "Test Device" }) {
            id
            name
        }
    }
    """
    response = client.post("/graphql", json={"query": query})
    data = response.json()

    assert response.status_code == 200
    assert data["data"]["createDevice"]["name"] == "Test Device"
    assert data["data"]["createDevice"]["id"] is not None


def test_delete_device(client):
    query = """
    mutation {
        createDevice(input: { name: "Test Device" }) {
            id
            name
        }
    }
    """
    response = client.post("/graphql", json={"query": query})
    device_create_result = response.json()
    query = """
    mutation {
        deleteDevice(input: { id: DEVICE_ID }) {
            id
            name
        }
    }
    """.replace("DEVICE_ID", str(device_create_result["data"]["createDevice"]["id"]))
    response = client.post("/graphql", json={"query": query})
    data = response.json()

    assert response.status_code == 200
    assert data["data"]["deleteDevice"]["name"] == device_create_result["data"]["createDevice"]["name"]
    assert data["data"]["deleteDevice"]["id"] is not None


def test_all_devices(client):
    create_query = """
    mutation {
        createDevice(input: { name: "Test Device" }) {
            id
            name
        }
    }
    """
    client.post("/graphql", json={"query": create_query})

    query = """
    query {
        allDevices {
            id
            name
        }
    }
    """
    response = client.post("/graphql", json={"query": query})
    data = response.json()

    assert response.status_code == 200
    assert len(data["data"]["allDevices"]) > 0
