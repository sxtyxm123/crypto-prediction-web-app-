"""
Authentication Manager for CryptoPredict AI
Handles user registration, login, profile management, and password security
"""

import json
import os
import uuid
import re
from datetime import datetime
from typing import Dict, Optional, List
import bcrypt


class AuthManager:
    """Manages user authentication and profile data"""
    
    def __init__(self, users_file: str = "users.json"):
        """
        Initialize AuthManager
        
        Args:
            users_file: Path to JSON file storing user data
        """
        self.users_file = users_file
        self._ensure_users_file()
    
    def _ensure_users_file(self):
        """Create users.json if it doesn't exist"""
        if not os.path.exists(self.users_file):
            initial_data = {"users": []}
            with open(self.users_file, 'w') as f:
                json.dump(initial_data, f, indent=2)
    
    def _load_users(self) -> Dict:
        """Load users from JSON file"""
        try:
            with open(self.users_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading users: {e}")
            return {"users": []}
    
    def _save_users(self, data: Dict):
        """Save users to JSON file"""
        try:
            with open(self.users_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving users: {e}")
    
    def validate_email(self, email: str) -> bool:
        """
        Validate email format
        
        Args:
            email: Email address to validate
            
        Returns:
            True if valid, False otherwise
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def validate_password(self, password: str) -> Dict[str, any]:
        """
        Validate password strength
        
        Args:
            password: Password to validate
            
        Returns:
            Dict with 'valid' boolean and 'errors' list
        """
        errors = []
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'strength': self._calculate_password_strength(password)
        }
    
    def _calculate_password_strength(self, password: str) -> str:
        """
        Calculate password strength
        
        Returns:
            'weak', 'medium', or 'strong'
        """
        score = 0
        
        if len(password) >= 8:
            score += 1
        if len(password) >= 12:
            score += 1
        if re.search(r'[A-Z]', password):
            score += 1
        if re.search(r'[a-z]', password):
            score += 1
        if re.search(r'\d', password):
            score += 1
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 1
        
        if score <= 2:
            return 'weak'
        elif score <= 4:
            return 'medium'
        else:
            return 'strong'
    
    def validate_phone(self, phone: str) -> bool:
        """
        Validate phone number format
        
        Args:
            phone: Phone number to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Allow international format: +1234567890 or 1234567890
        pattern = r'^\+?\d{10,15}$'
        return bool(re.match(pattern, phone))
    
    def hash_password(self, password: str) -> str:
        """
        Hash password using bcrypt
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """
        Verify password against hash
        
        Args:
            password: Plain text password
            hashed: Hashed password
            
        Returns:
            True if password matches, False otherwise
        """
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def email_exists(self, email: str) -> bool:
        """
        Check if email already exists
        
        Args:
            email: Email to check
            
        Returns:
            True if exists, False otherwise
        """
        data = self._load_users()
        return any(user['email'].lower() == email.lower() for user in data['users'])
    
    def register_user(
        self,
        name: str,
        email: str,
        password: str,
        phone: Optional[str] = None,
        birth_date: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Register a new user
        
        Args:
            name: User's full name
            email: User's email address
            password: User's password (plain text)
            phone: User's phone number (optional)
            birth_date: User's birth date in YYYY-MM-DD format (optional)
            
        Returns:
            Dict with 'success' boolean, 'user' dict if successful, 'error' if failed
        """
        # Validate email
        if not self.validate_email(email):
            return {'success': False, 'error': 'Invalid email format'}
        
        # Check if email exists
        if self.email_exists(email):
            return {'success': False, 'error': 'Email already registered'}
        
        # Validate password
        password_validation = self.validate_password(password)
        if not password_validation['valid']:
            return {
                'success': False,
                'error': 'Password does not meet requirements',
                'details': password_validation['errors']
            }
        
        # Validate phone if provided
        if phone and not self.validate_phone(phone):
            return {'success': False, 'error': 'Invalid phone number format'}
        
        # Validate name
        if not name or len(name.strip()) < 2:
            return {'success': False, 'error': 'Name must be at least 2 characters'}
        
        # Create user
        user_id = str(uuid.uuid4())
        hashed_password = self.hash_password(password)
        
        user = {
            'id': user_id,
            'name': name.strip(),
            'email': email.lower().strip(),
            'password_hash': hashed_password,
            'phone': phone.strip() if phone else None,
            'birth_date': birth_date,
            'created_at': datetime.now().isoformat(),
            'last_login': None,
            'preferences': {
                'theme': 'dark',
                'favorite_cryptos': []
            },
            'stats': {
                'total_predictions': 0,
                'last_prediction': None
            }
        }
        
        # Save user
        data = self._load_users()
        data['users'].append(user)
        self._save_users(data)
        
        # Return user without password hash
        user_safe = {k: v for k, v in user.items() if k != 'password_hash'}
        
        return {
            'success': True,
            'user': user_safe,
            'message': 'Registration successful'
        }
    
    def authenticate_user(self, email: str, password: str) -> Dict[str, any]:
        """
        Authenticate user with email and password
        
        Args:
            email: User's email
            password: User's password (plain text)
            
        Returns:
            Dict with 'success' boolean, 'user' dict if successful, 'error' if failed
        """
        data = self._load_users()
        
        # Find user by email
        user = None
        for u in data['users']:
            if u['email'].lower() == email.lower().strip():
                user = u
                break
        
        if not user:
            return {'success': False, 'error': 'Invalid email or password'}
        
        # Verify password
        if not self.verify_password(password, user['password_hash']):
            return {'success': False, 'error': 'Invalid email or password'}
        
        # Update last login
        user['last_login'] = datetime.now().isoformat()
        self._save_users(data)
        
        # Return user without password hash
        user_safe = {k: v for k, v in user.items() if k != 'password_hash'}
        
        return {
            'success': True,
            'user': user_safe,
            'message': 'Login successful'
        }
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """
        Get user by ID
        
        Args:
            user_id: User's unique ID
            
        Returns:
            User dict without password hash, or None if not found
        """
        data = self._load_users()
        
        for user in data['users']:
            if user['id'] == user_id:
                user_safe = {k: v for k, v in user.items() if k != 'password_hash'}
                return user_safe
        
        return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """
        Get user by email
        
        Args:
            email: User's email
            
        Returns:
            User dict without password hash, or None if not found
        """
        data = self._load_users()
        
        for user in data['users']:
            if user['email'].lower() == email.lower().strip():
                user_safe = {k: v for k, v in user.items() if k != 'password_hash'}
                return user_safe
        
        return None
    
    def update_profile(
        self,
        user_id: str,
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        birth_date: Optional[str] = None,
        preferences: Optional[Dict] = None
    ) -> Dict[str, any]:
        """
        Update user profile
        
        Args:
            user_id: User's unique ID
            name: New name (optional)
            email: New email (optional)
            phone: New phone (optional)
            birth_date: New birth date (optional)
            preferences: New preferences dict (optional)
            
        Returns:
            Dict with 'success' boolean, 'user' dict if successful, 'error' if failed
        """
        data = self._load_users()
        
        # Find user
        user_index = None
        for i, user in enumerate(data['users']):
            if user['id'] == user_id:
                user_index = i
                break
        
        if user_index is None:
            return {'success': False, 'error': 'User not found'}
        
        user = data['users'][user_index]
        
        # Update fields
        if name is not None:
            if len(name.strip()) < 2:
                return {'success': False, 'error': 'Name must be at least 2 characters'}
            user['name'] = name.strip()
        
        if email is not None:
            if not self.validate_email(email):
                return {'success': False, 'error': 'Invalid email format'}
            # Check if new email already exists (for different user)
            if email.lower() != user['email'].lower() and self.email_exists(email):
                return {'success': False, 'error': 'Email already in use'}
            user['email'] = email.lower().strip()
        
        if phone is not None:
            if phone and not self.validate_phone(phone):
                return {'success': False, 'error': 'Invalid phone number format'}
            user['phone'] = phone.strip() if phone else None
        
        if birth_date is not None:
            user['birth_date'] = birth_date
        
        if preferences is not None:
            user['preferences'].update(preferences)
        
        # Save changes
        data['users'][user_index] = user
        self._save_users(data)
        
        # Return updated user without password hash
        user_safe = {k: v for k, v in user.items() if k != 'password_hash'}
        
        return {
            'success': True,
            'user': user_safe,
            'message': 'Profile updated successfully'
        }
    
    def change_password(
        self,
        user_id: str,
        old_password: str,
        new_password: str
    ) -> Dict[str, any]:
        """
        Change user password
        
        Args:
            user_id: User's unique ID
            old_password: Current password
            new_password: New password
            
        Returns:
            Dict with 'success' boolean, 'error' if failed
        """
        data = self._load_users()
        
        # Find user
        user_index = None
        for i, user in enumerate(data['users']):
            if user['id'] == user_id:
                user_index = i
                break
        
        if user_index is None:
            return {'success': False, 'error': 'User not found'}
        
        user = data['users'][user_index]
        
        # Verify old password
        if not self.verify_password(old_password, user['password_hash']):
            return {'success': False, 'error': 'Current password is incorrect'}
        
        # Validate new password
        password_validation = self.validate_password(new_password)
        if not password_validation['valid']:
            return {
                'success': False,
                'error': 'New password does not meet requirements',
                'details': password_validation['errors']
            }
        
        # Update password
        user['password_hash'] = self.hash_password(new_password)
        data['users'][user_index] = user
        self._save_users(data)
        
        return {
            'success': True,
            'message': 'Password changed successfully'
        }
    
    def increment_prediction_count(self, user_id: str):
        """
        Increment user's prediction count
        
        Args:
            user_id: User's unique ID
        """
        data = self._load_users()
        
        for i, user in enumerate(data['users']):
            if user['id'] == user_id:
                user['stats']['total_predictions'] += 1
                user['stats']['last_prediction'] = datetime.now().isoformat()
                data['users'][i] = user
                self._save_users(data)
                break
    
    def get_all_users_count(self) -> int:
        """
        Get total number of registered users
        
        Returns:
            Number of users
        """
        data = self._load_users()
        return len(data['users'])
    
    def delete_user(self, user_id: str) -> Dict[str, any]:
        """
        Delete user account
        
        Args:
            user_id: User's unique ID
            
        Returns:
            Dict with 'success' boolean
        """
        data = self._load_users()
        
        # Find and remove user
        original_count = len(data['users'])
        data['users'] = [u for u in data['users'] if u['id'] != user_id]
        
        if len(data['users']) == original_count:
            return {'success': False, 'error': 'User not found'}
        
        self._save_users(data)
        
        return {
            'success': True,
            'message': 'Account deleted successfully'
        }


# Example usage
if __name__ == "__main__":
    auth = AuthManager()
    
    # Test registration
    result = auth.register_user(
        name="John Doe",
        email="john@example.com",
        password="SecurePass123!",
        phone="+1234567890",
        birth_date="1990-01-01"
    )
    print("Registration:", result)
    
    # Test login
    result = auth.authenticate_user("john@example.com", "SecurePass123!")
    print("Login:", result)
