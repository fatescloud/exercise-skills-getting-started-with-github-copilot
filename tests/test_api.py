"""Tests for the FastAPI endpoints"""
import pytest


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirects_to_static_index(self, client):
        """Test that root redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_200(self, client):
        """Test that getting activities returns 200 OK"""
        response = client.get("/activities")
        assert response.status_code == 200
    
    def test_get_activities_returns_dict(self, client):
        """Test that activities are returned as a dictionary"""
        response = client.get("/activities")
        data = response.json()
        assert isinstance(data, dict)
    
    def test_get_activities_contains_expected_fields(self, client):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        assert "Chess Club" in activities
        chess_club = activities["Chess Club"]
        
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_for_existing_activity_succeeds(self, client):
        """Test successful signup for an existing activity"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]
    
    def test_signup_adds_participant_to_list(self, client):
        """Test that signup actually adds participant to the activity"""
        email = "newstudent@mergington.edu"
        
        # Sign up
        client.post(f"/activities/Chess%20Club/signup?email={email}")
        
        # Verify participant was added
        response = client.get("/activities")
        activities = response.json()
        assert email in activities["Chess Club"]["participants"]
    
    def test_signup_for_nonexistent_activity_fails(self, client):
        """Test that signup for non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent%20Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"
    
    def test_duplicate_signup_fails(self, client):
        """Test that duplicate signup returns 400 error"""
        email = "duplicate@mergington.edu"
        
        # First signup should succeed
        response1 = client.post(f"/activities/Chess%20Club/signup?email={email}")
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(f"/activities/Chess%20Club/signup?email={email}")
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"].lower()
    
    def test_signup_with_existing_participant_fails(self, client):
        """Test that signing up with an already registered email fails"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_existing_participant_succeeds(self, client):
        """Test successful unregistration of existing participant"""
        response = client.delete(
            "/activities/Chess%20Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "michael@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]
    
    def test_unregister_removes_participant_from_list(self, client):
        """Test that unregister actually removes participant from activity"""
        email = "michael@mergington.edu"
        
        # Verify participant exists before
        response = client.get("/activities")
        activities = response.json()
        assert email in activities["Chess Club"]["participants"]
        
        # Unregister
        client.delete(f"/activities/Chess%20Club/unregister?email={email}")
        
        # Verify participant was removed
        response = client.get("/activities")
        activities = response.json()
        assert email not in activities["Chess Club"]["participants"]
    
    def test_unregister_from_nonexistent_activity_fails(self, client):
        """Test that unregister from non-existent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent%20Club/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"
    
    def test_unregister_non_registered_participant_fails(self, client):
        """Test that unregistering a non-registered participant fails"""
        response = client.delete(
            "/activities/Chess%20Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"].lower()
    
    def test_signup_and_unregister_workflow(self, client):
        """Test complete workflow: signup then unregister"""
        email = "workflow@mergington.edu"
        activity = "Chess Club"
        
        # Sign up
        response = client.post(f"/activities/{activity.replace(' ', '%20')}/signup?email={email}")
        assert response.status_code == 200
        
        # Verify signed up
        response = client.get("/activities")
        activities = response.json()
        assert email in activities[activity]["participants"]
        
        # Unregister
        response = client.delete(f"/activities/{activity.replace(' ', '%20')}/unregister?email={email}")
        assert response.status_code == 200
        
        # Verify unregistered
        response = client.get("/activities")
        activities = response.json()
        assert email not in activities[activity]["participants"]


class TestEdgeCases:
    """Tests for edge cases and special scenarios"""
    
    def test_signup_with_special_characters_in_email(self, client):
        """Test signup with special characters in email"""
        email = "test+special@mergington.edu"
        response = client.post(f"/activities/Chess%20Club/signup?email={email}")
        assert response.status_code == 200
    
    def test_activity_name_with_spaces_works(self, client):
        """Test that activity names with spaces are handled correctly"""
        response = client.post(
            "/activities/Programming%20Class/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
    
    def test_multiple_signups_to_different_activities(self, client):
        """Test that same email can sign up for multiple activities"""
        email = "multitask@mergington.edu"
        
        # Sign up for multiple activities
        response1 = client.post(f"/activities/Chess%20Club/signup?email={email}")
        response2 = client.post(f"/activities/Programming%20Class/signup?email={email}")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify participant is in both
        response = client.get("/activities")
        activities = response.json()
        assert email in activities["Chess Club"]["participants"]
        assert email in activities["Programming Class"]["participants"]
