"""
External database connectors - PostgreSQL, MySQL, MongoDB
"""

import os
import logging
from typing import List, Dict, Any, Optional
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class DatabaseConnector:
    """Connect and push data to external databases"""
    
    def __init__(self):
        """Initialize connector with encryption"""
        encryption_key = os.getenv('ENCRYPTION_KEY')
        if encryption_key:
            self.cipher = Fernet(encryption_key.encode())
        else:
            self.cipher = None
            logger.warning("No encryption key found - credentials will not be encrypted")
    
    def encrypt_credentials(self, credentials: str) -> str:
        """Encrypt database credentials"""
        if self.cipher:
            return self.cipher.encrypt(credentials.encode()).decode()
        return credentials
    
    def decrypt_credentials(self, encrypted: str) -> str:
        """Decrypt database credentials"""
        if self.cipher:
            return self.cipher.decrypt(encrypted.encode()).decode()
        return encrypted
    
    def connect_postgresql(self, connection_string: str, encrypted: bool = False) -> Any:
        """
        Connect to PostgreSQL database
        
        Args:
            connection_string: Connection URL
            encrypted: Whether connection string is encrypted
            
        Returns:
            Database connection
        """
        try:
            import psycopg2
            
            if encrypted:
                connection_string = self.decrypt_credentials(connection_string)
            
            conn = psycopg2.connect(connection_string)
            logger.info("PostgreSQL connection established")
            return conn
            
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}")
            raise
    
    def connect_mysql(self, connection_string: str, encrypted: bool = False) -> Any:
        """
        Connect to MySQL database
        
        Args:
            connection_string: Connection URL
            encrypted: Whether connection string is encrypted
            
        Returns:
            Database connection
        """
        try:
            import mysql.connector
            from urllib.parse import urlparse
            
            if encrypted:
                connection_string = self.decrypt_credentials(connection_string)
            
            # Parse connection string
            parsed = urlparse(connection_string)
            
            conn = mysql.connector.connect(
                host=parsed.hostname,
                port=parsed.port or 3306,
                user=parsed.username,
                password=parsed.password,
                database=parsed.path.lstrip('/')
            )
            
            logger.info("MySQL connection established")
            return conn
            
        except Exception as e:
            logger.error(f"MySQL connection failed: {e}")
            raise
    
    def connect_mongodb(self, connection_string: str, encrypted: bool = False) -> Any:
        """
        Connect to MongoDB
        
        Args:
            connection_string: MongoDB URI
            encrypted: Whether URI is encrypted
            
        Returns:
            MongoDB client
        """
        try:
            import pymongo
            
            if encrypted:
                connection_string = self.decrypt_credentials(connection_string)
            
            client = pymongo.MongoClient(connection_string)
            # Test connection
            client.server_info()
            
            logger.info("MongoDB connection established")
            return client
            
        except Exception as e:
            logger.error(f"MongoDB connection failed: {e}")
            raise
    
    def push_to_postgresql(self, jobs: List[Dict[str, Any]], connection_string: str, 
                          table_name: str = 'jobs', encrypted: bool = False) -> int:
        """
        Push jobs to PostgreSQL database
        
        Args:
            jobs: List of job dictionaries
            connection_string: Connection URL
            table_name: Target table name
            encrypted: Whether connection string is encrypted
            
        Returns:
            Number of jobs inserted
        """
        conn = None
        try:
            conn = self.connect_postgresql(connection_string, encrypted)
            cursor = conn.cursor()
            
            inserted = 0
            for job in jobs:
                # Build INSERT query
                columns = ', '.join(job.keys())
                placeholders = ', '.join(['%s'] * len(job))
                query = f"""
                    INSERT INTO {table_name} ({columns}) 
                    VALUES ({placeholders})
                    ON CONFLICT (source_url) DO NOTHING
                """
                
                cursor.execute(query, list(job.values()))
                inserted += cursor.rowcount
            
            conn.commit()
            logger.info(f"Pushed {inserted} jobs to PostgreSQL")
            return inserted
            
        except Exception as e:
            logger.error(f"Failed to push to PostgreSQL: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def push_to_mysql(self, jobs: List[Dict[str, Any]], connection_string: str,
                     table_name: str = 'jobs', encrypted: bool = False) -> int:
        """Push jobs to MySQL database"""
        conn = None
        try:
            conn = self.connect_mysql(connection_string, encrypted)
            cursor = conn.cursor()
            
            inserted = 0
            for job in jobs:
                columns = ', '.join(job.keys())
                placeholders = ', '.join(['%s'] * len(job))
                query = f"""
                    INSERT IGNORE INTO {table_name} ({columns}) 
                    VALUES ({placeholders})
                """
                
                cursor.execute(query, list(job.values()))
                inserted += cursor.rowcount
            
            conn.commit()
            logger.info(f"Pushed {inserted} jobs to MySQL")
            return inserted
            
        except Exception as e:
            logger.error(f"Failed to push to MySQL: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def push_to_mongodb(self, jobs: List[Dict[str, Any]], connection_string: str,
                       database_name: str = 'pakjobs', collection_name: str = 'jobs',
                       encrypted: bool = False) -> int:
        """Push jobs to MongoDB"""
        client = None
        try:
            client = self.connect_mongodb(connection_string, encrypted)
            db = client[database_name]
            collection = db[collection_name]
            
            # Use source_url as unique identifier
            inserted = 0
            for job in jobs:
                result = collection.update_one(
                    {'source_url': job['source_url']},
                    {'$set': job},
                    upsert=True
                )
                if result.upserted_id:
                    inserted += 1
            
            logger.info(f"Pushed {inserted} jobs to MongoDB")
            return inserted
            
        except Exception as e:
            logger.error(f"Failed to push to MongoDB: {e}")
            raise
        finally:
            if client:
                client.close()
    
    def test_connection(self, db_type: str, connection_string: str, encrypted: bool = False) -> bool:
        """
        Test database connection
        
        Args:
            db_type: 'postgresql', 'mysql', or 'mongodb'
            connection_string: Connection URL
            encrypted: Whether connection string is encrypted
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if db_type == 'postgresql':
                conn = self.connect_postgresql(connection_string, encrypted)
                conn.close()
            elif db_type == 'mysql':
                conn = self.connect_mysql(connection_string, encrypted)
                conn.close()
            elif db_type == 'mongodb':
                client = self.connect_mongodb(connection_string, encrypted)
                client.close()
            else:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
