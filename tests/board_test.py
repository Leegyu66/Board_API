import sys
import os
import unittest
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.base import Base
from app.deps import get_db
from app.core.auth import get_current_user
from app.models.user import User

# 테스트용 SQLite DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# DB 초기화
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

# DB 의존성 오버라이드
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# get_current_user 오버라이드
def override_get_current_user():
    db = TestingSessionLocal()
    return db.query(User).filter_by(id=1).first()

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)

class TestBoardAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # 테스트용 유저 생성
        db = TestingSessionLocal()
        user = User(
            id=1,
            name="test_user",
            email="test@example.com",
            login_id="test_login",
            password="test_password",  # NOT NULL 필드 채우기
            reg_dt=datetime.utcnow(),
            is_superuser=False
        )
        db.add(user)
        db.commit()
        db.close()

    def test_create_board(self):
        response = client.post("/board", json={"title": "Test Post", "content": "This is a test."})
        self.assertEqual(response.status_code, 201)
        self.assertIn("title", response.json())

    def test_read_board_list(self):
        response = client.get("/board")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_fetch_board_detail(self):
        create = client.post("/board", json={"title": "Detail Test", "content": "detail"})
        board_id = create.json()["id"]
        response = client.get(f"/board/{board_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], board_id)

    def test_update_board(self):
        create = client.post("/board", json={"title": "To Update", "content": "before"})
        board_id = create.json()["id"]
        response = client.patch(f"/board/{board_id}", json={"title": "Updated Title"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["title"], "Updated Title")

    def test_delete_board(self):
        create = client.post("/board", json={"title": "To Delete", "content": "bye"})
        board_id = create.json()["id"]
        response = client.delete(f"/board/{board_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], board_id)

    def test_get_user_posts(self):
        response = client.get("/board/user/1")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

if __name__ == "__main__":
    unittest.main()