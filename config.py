"""
ACDON Configuration Manager
Handles environment variables, Firebase initialization, and system-wide constants
"""
import os
from dataclasses import dataclass
from typing import Optional
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
import structlog

# Initialize logging
logger = structlog.get_logger()

# Load environment variables
load_dotenv()

@dataclass
class FirebaseConfig:
    """Firebase configuration with validation"""
    project_id: str
    private_key_id: str
    private_key: str
    client_email: str
    client_id: str
    auth_uri: str = "https://accounts.google.com/o/oauth2/auth"
    token_uri: str = "https://oauth2.googleapis.com/token"
    auth_provider_x509_cert_url: str = "https://www.googleapis.com/oauth2/v1/certs"
    client_x509_cert_url: str = ""
    
    def __post_init__(self):
        """Validate Firebase configuration"""
        if not all([self.project_id, self.private_key, self.client_email]):
            raise ValueError("Missing required Firebase credentials")
        # Format private key properly
        self.private_key = self.private_key.replace('\\n', '\n')

class ACDONConfig:
    """Main configuration class for ACDON"""
    
    def __init__(self):
        self._firebase_app = None
        self._firestore_client = None
        self.logger = logger.bind(module="config")
        
    def initialize_firebase(self) -> bool:
        """
        Initialize Firebase Admin SDK with error handling
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            # Check if already initialized
            if firebase_admin._apps:
                self.logger.info("Firebase already initialized")
                self._firestore_client = firestore.client()
                return True
            
            # Get credentials from environment
            cred_dict = {
                "type": "service_account",
                "project_id": os.getenv("FIREBASE_PROJECT_ID"),
                "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
                "private_key": os.getenv("FIREBASE_PRIVATE_KEY", ""),
                "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
                "client_id": os.getenv("FIREBASE_CLIENT_ID"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL", "")
            }
            
            # Validate credentials
            firebase_config = FirebaseConfig(**cred_dict)
            
            # Initialize Firebase
            cred = credentials.Certificate(cred_dict)
            self._firebase_app = firebase_admin.initialize_app(cred)
            self._firestore_client = firestore.client(self._firebase_app)
            
            self.logger.info("Firebase initialized successfully", 
                           project_id=firebase_config.project_id)
            return True
            
        except ValueError as ve:
            self.logger.error("Firebase configuration error", error=str(ve))
            return False
        except Exception as e:
            self.logger.error("Firebase initialization failed", error=str(e))
            return False
    
    @property
    def firestore_client(self) -> Optional[firestore.Client]:
        """Get Firestore client with lazy initialization"""
        if not self._firestore_client:
            self.initialize_firebase()
        return self._firestore_client
    
    @property
    def optimization_thresholds(self) -> dict:
        """Get optimization thresholds from environment"""
        return {
            "performance_threshold": float(os.getenv("PERF_THRESHOLD", "0.7")),
            "resource_threshold": float(os.getenv("RESOURCE_THRESHOLD", "0.8")),
            "latency_threshold": float(os.getenv("LATENCY_THRESHOLD", "100")),  # ms
            "retry_attempts": int(os.getenv("RETRY_ATTEMPTS", "3"))
        }

# Global configuration instance
config = ACDONConfig()