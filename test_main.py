from fastapi.testclient import TestClient
import pytest
from main import app
from pydantic import BaseModel

def test_get_tracks():
    with TestClient(app) as client:
        response = client.get("/tracks", params = {'page': 2, 'per_page': 1})
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert response.json()[0]['TrackId'] == 3
        assert response.json()[0]['Name'] == 'Fast As a Shark'

def test_get_tracks_by_composer():
    with TestClient(app) as client:
        response = client.get("/tracks/composers", params = {"composer_name": "Toby Smith"})
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert response.json()[0] == 'Deeper Underground'
        assert response.json()[-1] == 'The Kids'

def test_get_tracks_by_composer_empty_composer():
    with TestClient(app) as client:
        response = client.get("/tracks/composers", params = {"composer_name": ""})
        assert response.status_code == 404
        assert response.json() == {"detail":{"error":"No tracks by this composer."}}

class Album(BaseModel):
    title : str
    artist_id: int

def test_post_album():
    with TestClient(app) as client:
        response = client.post("/albums", json = {'title':'Test', 'artist_id':271})
        assert response.status_code == 201
        assert response.json()["Title"] == "Test"
        assert response.json()["ArtistId"] == 271

def test_post_album_wrong_id():
    with TestClient(app) as client:
        response = client.post("/albums", json = {'title': 'Test', 'artist_id': -1})
        assert response.status_code == 404
        assert response.json() == {"detail":{"error":"Unknown artist."}}

def test_get_album():
    with TestClient(app) as client:
        response = client.get(f"/albums/{351}")
        assert response.status_code == 200
        assert response.json()["Title"] == "Test"
        assert response.json()["ArtistId"] == 271

def test_sales():
    with TestClient(app) as client:
        response = client.get("/sales", params = {"category": "customers"})
        assert response.status_code == 200
        assert response.json()[0]["CustomerId"] == 6
        assert response.json()[0]["Sum"] == 49.62
        assert response.json()[1]["CustomerId"] == 26
        assert response.json()[1]["Sum"] == 47.62

        response = client.get("/sales", params = {"category": "genres"})
        assert response.status_code == 200
        assert response.json()[0]["Name"] == "Rock"
        assert response.json()[0]["Sum"] == 835
        assert response.json()[1]["Name"] == "Latin"
        assert response.json()[1]["Sum"] == 386

        response = client.get("/sales", params = {"category": "aaaa"})
        assert response.status_code == 404
        assert response.json() == {"detail": {"error": "Wrong category name."}}

def test_put_customer():
    with TestClient(app) as client:
        response = client.put(f"/customers/{1}", json = {"company": "TEST"})
        assert response.status_code == 200
        assert response.json()["CustomerId"] == 1
        assert response.json()["Company"] == "TEST"

