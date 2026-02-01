import unittest
import requests
from unittest.mock import patch

class TestUserAPI(unittest.TestCase):
    
    def setUp(self):
        self.base_url = "https://api.example.com"
    
    def test_get_user_success(self):
        """Test successful user retrieval"""
        response = requests.get(f"{self.base_url}/users/123")
        self.assertEqual(response.status_code, 200)
        self.assertIn('id', response.json())
    
    def test_get_user_not_found(self):
        """Test user not found scenario"""
        response = requests.get(f"{self.base_url}/users/999")
        assert response.status_code == 404
    
    def test_create_user_success(self):
        """Test successful user creation"""
        user_data = {"name": "John Doe", "email": "john@example.com"}
        response = requests.post(f"{self.base_url}/users", json=user_data)
        self.assertEqual(response.status_code, 201)
    
    def test_create_user_invalid_data(self):
        """Test user creation with invalid data"""
        invalid_data = {"name": ""}
        response = requests.post(f"{self.base_url}/users", json=invalid_data)
        self.assertEqual(response.status_code, 400)
    
    def test_create_user_conflict(self):
        """Test user creation when user already exists"""
        user_data = {"name": "Jane Doe", "email": "jane@example.com"}
        # Create user first
        requests.post(f"{self.base_url}/users", json=user_data)
        # Try to create again
        response = requests.post(f"{self.base_url}/users", json=user_data)
        self.assertEqual(response.status_code, 409)
    
    def test_update_user_success(self):
        """Test successful user update"""
        update_data = {"name": "Updated Name"}
        response = requests.put(f"{self.base_url}/users/123", json=update_data)
        assert response.status_code == 200
    
    def test_update_user_not_found(self):
        """Test update non-existent user"""
        update_data = {"name": "Updated Name"}
        response = requests.put(f"{self.base_url}/users/999", json=update_data)
        self.assertEqual(response.status_code, 404)
    
    def test_update_user_forbidden(self):
        """Test update user without permission"""
        update_data = {"name": "Updated Name"}
        response = requests.put(f"{self.base_url}/users/456", json=update_data)
        self.assertEqual(response.status_code, 403)
    
    def test_unauthorized_access(self):
        """Test access without authentication"""
        response = requests.get(f"{self.base_url}/users/123")
        # Should return 401 if not authenticated
        self.assertEqual(response.status_code, 401)

if __name__ == '__main__':
    unittest.main()