"""
Tests for the Mergington High School API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test"""
    activities["Chess Club"]["participants"] = ["michael@mergington.edu", "daniel@mergington.edu"]
    activities["Programming Class"]["participants"] = ["emma@mergington.edu", "sophia@mergington.edu"]
    activities["Gym Class"]["participants"] = ["john@mergington.edu", "olivia@mergington.edu"]
    activities["Basketball Team"]["participants"] = ["james@mergington.edu", "alex@mergington.edu"]
    activities["Swimming Club"]["participants"] = ["sarah@mergington.edu", "noah@mergington.edu"]
    activities["Art Studio"]["participants"] = ["lucy@mergington.edu", "mia@mergington.edu"]
    activities["Drama Club"]["participants"] = ["ethan@mergington.edu", "ava@mergington.edu"]
    activities["Debate Team"]["participants"] = ["william@mergington.edu", "isabella@mergington.edu"]
    activities["Robotics Club"]["participants"] = ["liam@mergington.edu", "charlotte@mergington.edu"]
    yield


class TestRootEndpoint:
    """Test the root endpoint"""

    def test_root_redirects_to_static(self, client):
        """Test that root redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Test the GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """Test that all activities are returned"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 9
        assert "Chess Club" in data
        assert "Programming Class" in data

    def test_activities_have_correct_structure(self, client):
        """Test that activities have the expected structure"""
        response = client.get("/activities")
        data = response.json()
        chess_club = data["Chess Club"]
        
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)


class TestSignupForActivity:
    """Test the POST /activities/{activity_name}/signup endpoint"""

    def test_signup_for_existing_activity(self, client):
        """Test signing up for an existing activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up test@mergington.edu for Chess Club" in data["message"]

    def test_signup_adds_participant_to_list(self, client):
        """Test that signup actually adds participant to the activity"""
        client.post("/activities/Chess Club/signup?email=newstudent@mergington.edu")
        
        response = client.get("/activities")
        data = response.json()
        assert "newstudent@mergington.edu" in data["Chess Club"]["participants"]

    def test_signup_for_nonexistent_activity(self, client):
        """Test signing up for a non-existent activity returns 404"""
        response = client.post(
            "/activities/Fake Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_duplicate_signup_prevented(self, client):
        """Test that duplicate signups are prevented"""
        email = "duplicate@mergington.edu"
        
        # First signup should succeed
        response1 = client.post(f"/activities/Chess Club/signup?email={email}")
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(f"/activities/Chess Club/signup?email={email}")
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]

    def test_signup_with_existing_participant(self, client):
        """Test signing up with email that's already registered"""
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]


class TestUnregisterParticipant:
    """Test the DELETE /activities/{activity_name}/participants/{email} endpoint"""

    def test_unregister_existing_participant(self, client):
        """Test unregistering an existing participant"""
        response = client.delete(
            "/activities/Chess Club/participants/michael@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered michael@mergington.edu from Chess Club" in data["message"]

    def test_unregister_removes_participant_from_list(self, client):
        """Test that unregister actually removes participant from the activity"""
        client.delete("/activities/Chess Club/participants/michael@mergington.edu")
        
        response = client.get("/activities")
        data = response.json()
        assert "michael@mergington.edu" not in data["Chess Club"]["participants"]

    def test_unregister_from_nonexistent_activity(self, client):
        """Test unregistering from a non-existent activity returns 404"""
        response = client.delete(
            "/activities/Fake Club/participants/test@mergington.edu"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_nonexistent_participant(self, client):
        """Test unregistering a participant that isn't signed up returns 404"""
        response = client.delete(
            "/activities/Chess Club/participants/notregistered@mergington.edu"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Participant not found"

    def test_unregister_then_signup_again(self, client):
        """Test that a participant can signup again after being unregistered"""
        email = "michael@mergington.edu"
        
        # Unregister
        response1 = client.delete(f"/activities/Chess Club/participants/{email}")
        assert response1.status_code == 200
        
        # Signup again
        response2 = client.post(f"/activities/Chess Club/signup?email={email}")
        assert response2.status_code == 200
        
        # Verify participant is in the list
        response3 = client.get("/activities")
        data = response3.json()
        assert email in data["Chess Club"]["participants"]
