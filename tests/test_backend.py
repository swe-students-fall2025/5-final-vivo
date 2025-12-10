import os
import json
import pytest
from pymongo import MongoClient
from dotenv import load_dotenv
import webapp.app as app_module


load_dotenv(".env.test")

TEST_DB_NAME = "vivo_test"


def get_test_db():
    uri = os.environ.get("MONGO_URI")
    client = MongoClient(uri)
    return client[TEST_DB_NAME]


@pytest.fixture
def test_db():
    db = get_test_db()
    db["bathrooms"].delete_many({})
    db["users"].delete_many({})
    return db


@pytest.fixture
def app_client(test_db, monkeypatch):
    monkeypatch.setattr(app_module, "bathrooms_collection", test_db["bathrooms"])
    monkeypatch.setattr(app_module, "users_collection", test_db["users"])
    app_module.app.testing = True
    with app_module.app.test_client() as client:
        yield client


def login(app_client, email="tester@nyu.edu", name="Tester"):
    with app_client.session_transaction() as sess:
        sess["user"] = {"email": email, "name": name, "id": "TESTUSER"}


def test_index_redirects_when_not_logged_in(app_client, test_db):
    resp = app_client.get("/")
    assert resp.status_code in (302, 303)


def test_login_page_ok(app_client, test_db):
    resp = app_client.get("/login")
    assert resp.status_code == 200


def test_add_bathroom_and_get_full(app_client, test_db):
    resp = app_client.post(
        "/api/bathrooms/add",
        json={"osm_id": 1, "lat": 40.0, "lon": -73.0},
    )
    assert resp.status_code in (200, 201)
    resp = app_client.get("/api/bathrooms/full")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "bathrooms" in data
    assert len(data["bathrooms"]) == 1
    assert data["bathrooms"][0]["osm_id"] == 1


def test_add_bathroom_missing_field(app_client, test_db):
    resp = app_client.post(
        "/api/bathrooms/add",
        json={"lat": 40.0, "lon": -73.0},
    )
    assert resp.status_code == 400


def test_get_bathroom_detail_found(app_client, test_db):
    test_db["bathrooms"].insert_one(
        {
            "osm_id": "123",
            "lat": 40.1,
            "lon": -73.9,
            "tags": {"name": "Detail Bathroom"},
            "reviews": [],
            "average_rating": None,
            "rating_count": 0,
        }
    )
    resp = app_client.get("/api/bathrooms/123")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["osm_id"] == "123"
    assert data["tags"]["name"] == "Detail Bathroom"


def test_get_bathroom_detail_not_found(app_client, test_db):
    resp = app_client.get("/api/bathrooms/999999")
    assert resp.status_code == 404


def test_get_bathroom_reviews_invalid_osm_id(app_client, test_db):
    resp = app_client.get("/api/bathrooms/abc/reviews")
    assert resp.status_code == 400


def test_get_bathroom_reviews_not_found(app_client, test_db):
    resp = app_client.get("/api/bathrooms/9999/reviews")
    assert resp.status_code in (400, 404)


def test_add_review_requires_login(app_client, test_db):
    test_db["bathrooms"].insert_one(
        {
            "osm_id": 200,
            "lat": 0,
            "lon": 0,
            "tags": {},
            "reviews": [],
            "average_rating": None,
            "rating_count": 0,
        }
    )
    resp = app_client.post(
        "/api/bathrooms/200/reviews",
        json={"rating": 5, "comment": "test"},
    )
    assert resp.status_code == 401


def test_full_review_flow(app_client, test_db):
    test_db["bathrooms"].insert_one(
        {
            "osm_id": 300,
            "lat": 40.0,
            "lon": -73.0,
            "tags": {"name": "Review Bathroom"},
            "reviews": [],
            "average_rating": None,
            "rating_count": 0,
        }
    )
    login(app_client, email="flow@nyu.edu", name="Flow User")
    resp = app_client.post(
        "/api/bathrooms/300/reviews",
        json={"rating": 5, "comment": "great"},
    )
    assert resp.status_code in (200, 201)
    resp = app_client.get("/api/bathrooms/300/reviews")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data["reviews"]) == 1
    assert data["reviews"][0]["comment"] == "great"
    resp = app_client.post(
        "/api/bathrooms/300/reviews",
        json={"rating": 3, "comment": "updated"},
    )
    assert resp.status_code in (200, 201)
    resp = app_client.get("/api/bathrooms/300/reviews")
    data = resp.get_json()
    assert len(data["reviews"]) == 1
    assert data["reviews"][0]["rating"] == 3
    assert data["reviews"][0]["comment"] == "updated"
    resp = app_client.delete("/api/bathrooms/300/reviews")
    assert resp.status_code == 200
    resp = app_client.get("/api/bathrooms/300/reviews")
    data = resp.get_json()
    assert len(data["reviews"]) == 0


def test_get_my_reviews_requires_login(app_client, test_db):
    resp = app_client.get("/api/my-reviews")
    assert resp.status_code == 401


def test_get_my_reviews_only_current_user(app_client, test_db):
    test_db["bathrooms"].insert_one(
        {
            "osm_id": 400,
            "lat": 40.7,
            "lon": -73.9,
            "tags": {"name": "Multi Review Bathroom"},
            "reviews": [
                {
                    "user_email": "user1@nyu.edu",
                    "user_name": "User1",
                    "rating": 4,
                    "comment": "from user1",
                    "created_at": "2025-01-01T00:00:00Z",
                },
                {
                    "user_email": "user2@nyu.edu",
                    "user_name": "User2",
                    "rating": 2,
                    "comment": "from user2",
                    "created_at": "2025-01-02T00:00:00Z",
                },
            ],
            "average_rating": 3,
            "rating_count": 2,
        }
    )
    login(app_client, email="user1@nyu.edu", name="User1")
    resp = app_client.get("/api/my-reviews")
    assert resp.status_code == 200
    data = resp.get_json()
    reviews = data["reviews"]
    assert len(reviews) == 1
    assert reviews[0]["comment"] == "from user1"
    assert reviews[0]["bathroom_name"] == "Multi Review Bathroom"


def test_delete_review_requires_login(app_client, test_db):
    test_db["bathrooms"].insert_one(
        {
            "osm_id": 500,
            "lat": 0,
            "lon": 0,
            "tags": {},
            "reviews": [],
            "average_rating": None,
            "rating_count": 0,
        }
    )
    resp = app_client.delete("/api/bathrooms/500/reviews")
    assert resp.status_code in (400, 401)


def test_delete_review_no_review_for_user(app_client, test_db):
    test_db["bathrooms"].insert_one(
        {
            "osm_id": 600,
            "lat": 0,
            "lon": 0,
            "tags": {},
            "reviews": [
                {
                    "user_email": "other@nyu.edu",
                    "rating": 4,
                    "comment": "not mine",
                    "created_at": "2025-01-01T00:00:00Z",
                }
            ],
            "average_rating": 4,
            "rating_count": 1,
        }
    )
    login(app_client, email="me@nyu.edu", name="Me")
    resp = app_client.delete("/api/bathrooms/600/reviews")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get("message") == "No review from this user to delete."


def test_get_bathrooms_basic_list(app_client, test_db):
    test_db["bathrooms"].insert_one(
        {
            "osm_id": 700,
            "lat": 40.71,
            "lon": -73.99,
            "tags": {"name": "A"},
            "reviews": [],
            "average_rating": 4,
            "rating_count": 1,
        }
    )
    test_db["bathrooms"].insert_one(
        {
            "osm_id": 701,
            "lat": 40.72,
            "lon": -73.98,
            "tags": {"name": "B"},
            "reviews": [],
            "average_rating": 2,
            "rating_count": 5,
        }
    )
    resp = app_client.get("/api/bathrooms")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "bathrooms" in data
    assert len(data["bathrooms"]) == 2


def test_get_bathrooms_with_filters_and_sort(app_client, test_db):
    test_db["bathrooms"].insert_one(
        {
            "osm_id": 800,
            "lat": 40.70,
            "lon": -73.90,
            "tags": {"name": "Filter A"},
            "reviews": [],
            "average_rating": 5,
            "rating_count": 2,
        }
    )
    test_db["bathrooms"].insert_one(
        {
            "osm_id": 801,
            "lat": 40.71,
            "lon": -73.91,
            "tags": {"name": "Filter B"},
            "reviews": [],
            "average_rating": 3,
            "rating_count": 10,
        }
    )
    resp = app_client.get(
        "/api/bathrooms?min_lat=40.69&max_lat=40.72&min_lon=-73.92&max_lon=-73.89&sort=rating&limit=1"
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert "bathrooms" in data
    assert len(data["bathrooms"]) == 1


def test_add_review_invalid_rating(app_client, test_db):
    test_db["bathrooms"].insert_one(
        {
            "osm_id": 850,
            "lat": 40.0,
            "lon": -73.0,
            "tags": {},
            "reviews": [],
            "average_rating": None,
            "rating_count": 0,
        }
    )
    login(app_client, email="rating@nyu.edu", name="Rating User")

    resp = app_client.post(
        "/api/bathrooms/850/reviews",
        json={"rating": 6, "comment": "too high"},
    )
    assert resp.status_code == 400

    resp = app_client.post(
        "/api/bathrooms/850/reviews",
        json={"rating": "bad-number"},
    )
    assert resp.status_code == 400

    doc = test_db["bathrooms"].find_one({"osm_id": 850})
    assert doc["reviews"] == []
    assert doc["rating_count"] == 0


def test_add_bathroom_image_flow(app_client, test_db):
    test_db["bathrooms"].insert_one(
        {
            "osm_id": 860,
            "lat": 0,
            "lon": 0,
            "tags": {},
            "reviews": [],
            "images": [],
            "average_rating": None,
            "rating_count": 0,
        }
    )

    resp = app_client.post(
        "/api/bathrooms/860/images", json={"image": "data:..."}
    )
    assert resp.status_code == 401

    login(app_client, email="img@nyu.edu", name="Img User")
    resp = app_client.post(
        "/api/bathrooms/860/images", json={"image": "data:image/png;base64,abc"}
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert "images" in data
    assert len(data["images"]) == 1
    assert data["images"][0] == "data:image/png;base64,abc"

    doc = test_db["bathrooms"].find_one({"osm_id": 860})
    assert doc["images"] == ["data:image/png;base64,abc"]


def test_favorites_add_and_remove(app_client, test_db):
    test_db["bathrooms"].insert_one(
        {
            "osm_id": 870,
            "lat": 0,
            "lon": 0,
            "tags": {"name": "Fav Bathroom"},
            "reviews": [],
            "average_rating": None,
            "rating_count": 0,
            "favorite_count": 0,
        }
    )
    test_db["users"].insert_one(
        {"email": "fav@nyu.edu", "name": "Fav User", "favorites": []}
    )
    login(app_client, email="fav@nyu.edu", name="Fav User")

    resp = app_client.post("/api/users/favorites/870")
    assert resp.status_code == 200
    resp = app_client.post("/api/users/favorites/870")
    assert resp.status_code == 200

    user_doc = test_db["users"].find_one({"email": "fav@nyu.edu"})
    assert user_doc["favorites"] == [870]
    bathroom_doc = test_db["bathrooms"].find_one({"osm_id": 870})
    assert bathroom_doc.get("favorite_count") == 1

    resp = app_client.get("/api/users/favorites")
    assert resp.status_code == 200
    assert resp.get_json()["favorites"] == [870]

    resp = app_client.delete("/api/users/favorites/870")
    assert resp.status_code == 200
    user_doc = test_db["users"].find_one({"email": "fav@nyu.edu"})
    assert user_doc["favorites"] == []
    bathroom_doc = test_db["bathrooms"].find_one({"osm_id": 870})
    assert bathroom_doc.get("favorite_count") == 0


def test_recommendations_invalid_params(app_client, test_db):
    resp = app_client.get("/api/bathrooms/recommendations?lat=abc&lon=def")
    assert resp.status_code == 400


def test_recommendations_sections_and_order(app_client, test_db):
    test_db["bathrooms"].insert_many(
        [
            {
                "osm_id": 880,
                "lat": 40.0,
                "lon": -73.0,
                "tags": {"name": "Central"},
                "reviews": [],
                "average_rating": 4.5,
                "rating_count": 2,
                "favorite_count": 3,
            },
            {
                "osm_id": 881,
                "lat": 40.1,
                "lon": -73.1,
                "tags": {"name": "North"},
                "reviews": [],
                "average_rating": 5.0,
                "rating_count": 1,
                "favorite_count": 1,
            },
            {
                "osm_id": 882,
                "lat": 42.0,
                "lon": -75.0,
                "tags": {"name": "Far"},
                "reviews": [],
                "average_rating": 2.0,
                "rating_count": 5,
                "favorite_count": 10,
            },
            {
                "osm_id": 883,
                "lat": 41.0,
                "lon": -74.0,
                "tags": {"name": "Unrated"},
                "reviews": [],
                "average_rating": None,
                "rating_count": 0,
                "favorite_count": 4,
            },
        ]
    )

    resp = app_client.get("/api/bathrooms/recommendations?lat=40&lon=-73")
    assert resp.status_code == 200
    data = resp.get_json()

    assert data["top_rated"][0]["osm_id"] == 881
    assert data["most_favorited"][0]["osm_id"] == 882
    nearest_ids = [item["osm_id"] for item in data["nearest"]]
    assert nearest_ids[:2] == [880, 881]
