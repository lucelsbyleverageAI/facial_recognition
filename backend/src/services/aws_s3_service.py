import boto3
import logging
import os
from botocore.exceptions import ClientError, NoCredentialsError
from typing import List, Dict, Any, Optional, Tuple, Union
from src.utils.env_loader import get_required_env_var
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

def get_env_var(var_name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get an environment variable or return a default value if not set.
    
    Args:
        var_name: Name of the environment variable
        default: Default value to return if the environment variable is not set
        
    Returns:
        The value of the environment variable or the default value
    """
    return os.getenv(var_name, default)

class AWSS3Service:
    """
    Service to interact with AWS S3 for consent folder scanning and file operations.
    """
    
    def __init__(
        self, 
        bucket_name: Optional[str] = None, 
        base_prefix: str = "",
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        region_name: Optional[str] = None
    ):
        """
        Initialize the AWS S3 service.
        
        Args:
            bucket_name: Optional name of the S3 bucket. If not provided, uses AWS_BUCKET_NAME from env.
            base_prefix: Optional base prefix (folder) within the bucket to use as root.
            access_key_id: Optional AWS access key ID. If not provided, uses AWS_ACCESS_KEY_ID from env.
            secret_access_key: Optional AWS secret access key. If not provided, uses AWS_SECRET_ACCESS_KEY from env.
            region_name: Optional AWS region name. If not provided, uses AWS_REGION from env.
        """
        # Try to load environment variables from .env file directly
        # Look for .env file in current directory and parent directories
        env_file = '.env'
        env_path = os.path.join(os.getcwd(), env_file)
        if not os.path.exists(env_path):
            # Try parent directory
            env_path = os.path.join(os.path.dirname(os.getcwd()), env_file)
        
        if os.path.exists(env_path):
            print(f"Loading environment variables from {env_path}")
            load_dotenv(env_path)
        
        # Try to get the bucket name from the parameter, then the environment
        self.bucket_name = bucket_name or get_env_var("AWS_BUCKET_NAME", "chwarel-sandbox")
        self.base_prefix = base_prefix.rstrip('/') + '/' if base_prefix else ""
        
        # Get AWS credentials from parameters or environment variables
        self.access_key_id = access_key_id or get_env_var("AWS_ACCESS_KEY_ID")
        self.secret_access_key = secret_access_key or get_env_var("AWS_SECRET_ACCESS_KEY")
        self.region_name = region_name or get_env_var("AWS_REGION", "us-east-1")
        
        # Check if credentials are available
        if not self.access_key_id or not self.secret_access_key:
            logger.warning("AWS credentials not found. S3 operations will likely fail.")
        
        # Initialize the S3 client with explicit credentials
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            region_name=self.region_name
        )
        
        logger.info(f"Initialized AWSS3Service with bucket: {self.bucket_name}, base prefix: {self.base_prefix}")
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to the S3 bucket.
        
        Returns:
            Dict with connection status and additional information
        """
        results = {
            "status": "error",
            "bucket_name": self.bucket_name,
            "operations_tested": [],
            "successful_operations": [],
            "errors": {}
        }
        
        # Test 1: List objects with the base prefix
        try:
            print(f"Testing list_objects_v2 with prefix '{self.base_prefix}'...")
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=self.base_prefix,
                MaxKeys=1
            )
            results["operations_tested"].append("list_objects_v2_with_prefix")
            results["successful_operations"].append("list_objects_v2_with_prefix")
            
            # If we got here, connection is successful
            if results["status"] == "error":
                results["status"] = "success"
            results["message"] = "Successfully connected to S3 bucket"
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            results["operations_tested"].append("list_objects_v2_with_prefix")
            results["errors"]["list_objects_v2_with_prefix"] = f"{error_code}: {error_message}"
            
            logger.error(f"S3 client error on list_objects_v2: {error_code} - {error_message}")
        
        # Test 2: Try head_bucket to check if bucket exists and is accessible
        try:
            print(f"Testing head_bucket operation...")
            response = self.s3_client.head_bucket(Bucket=self.bucket_name)
            results["operations_tested"].append("head_bucket")
            results["successful_operations"].append("head_bucket")
            
            # If we got here, connection is successful
            if results["status"] == "error":
                results["status"] = "success"
            results["message"] = "Successfully connected to S3 bucket"
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            results["operations_tested"].append("head_bucket")
            results["errors"]["head_bucket"] = f"{error_code}: {error_message}"
            
            logger.error(f"S3 client error on head_bucket: {error_code} - {error_message}")
        
        # Test 3: Try to get a non-existent object with the base prefix
        # This is useful because it can fail in a way that confirms credentials are valid
        test_key = f"{self.base_prefix}test-key-that-does-not-exist-{os.urandom(4).hex()}"
        try:
            print(f"Testing get_object with non-existent key '{test_key}'...")
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=test_key
            )
            # We don't expect this to succeed
            results["operations_tested"].append("get_object_non_existent")
            results["successful_operations"].append("get_object_non_existent")
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            results["operations_tested"].append("get_object_non_existent")
            
            # NoSuchKey is the expected error for a non-existent object
            # This indicates our credentials are valid, we just can't find the object
            if error_code == "NoSuchKey":
                results["successful_operations"].append("get_object_non_existent_auth")
                
                # If we got here, connection is successful (auth-wise)
                if results["status"] == "error":
                    results["status"] = "success"
                results["message"] = "Successfully authenticated with S3 (confirmed by NoSuchKey error)"
            else:
                results["errors"]["get_object_non_existent"] = f"{error_code}: {error_message}"
            
            logger.info(f"S3 client error on get_object (expected): {error_code} - {error_message}")
        
        # Handle the case where no authentication worked at all
        if not results["successful_operations"]:
            # No operations succeeded - check for credentials
            if not self.access_key_id or not self.secret_access_key:
                logger.error("No AWS credentials found")
                results["message"] = "No AWS credentials found. Ensure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are set."
            else:
                results["message"] = "Failed to authenticate with AWS S3. Check credentials and permissions."
        
        return results
    
    def list_folders(self, prefix: str = "") -> List[Dict[str, str]]:
        """
        List folders within the specified prefix in the S3 bucket.
        
        Args:
            prefix: The folder prefix to list folders in (relative to base_prefix)
            
        Returns:
            List of dicts with folder information (name, path)
        """
        effective_prefix = f"{self.base_prefix}{prefix}"
        if effective_prefix and not effective_prefix.endswith('/'):
            effective_prefix += '/'
            
        logger.info(f"Listing folders with prefix: {effective_prefix}")
        
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=effective_prefix,
                Delimiter='/'
            )
            
            folders = []
            
            if 'CommonPrefixes' in response:
                for folder in response['CommonPrefixes']:
                    full_prefix = folder['Prefix']  # Including base_prefix
                    
                    # Extract folder name from the full path
                    # If base_prefix is 'consent_data/' and full_prefix is 'consent_data/project1_Name/'
                    # We want to return just 'project1_Name'
                    folder_name = full_prefix
                    if self.base_prefix and full_prefix.startswith(self.base_prefix):
                        folder_name = full_prefix[len(self.base_prefix):]
                    
                    # Remove trailing slash
                    folder_name = folder_name.rstrip('/')
                    
                    folders.append({
                        "name": folder_name,
                        "path": full_prefix
                    })
            
            return folders
            
        except ClientError as e:
            logger.error(f"Error listing folders: {str(e)}")
            raise
    
    def list_files(self, prefix: str = "") -> List[Dict[str, str]]:
        """
        List files within the specified prefix in the S3 bucket.
        
        Args:
            prefix: The folder prefix to list files in (relative to base_prefix)
            
        Returns:
            List of dicts with file information (name, path, size, last_modified)
        """
        effective_prefix = f"{self.base_prefix}{prefix}"
        if effective_prefix and not effective_prefix.endswith('/'):
            effective_prefix += '/'
            
        logger.info(f"Listing files with prefix: {effective_prefix}")
        
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=effective_prefix
            )
            
            files = []
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    key = obj['Key']
                    
                    # Skip "directory" objects (keys ending with '/')
                    if key.endswith('/'):
                        continue
                        
                    # Skip if key is exactly the prefix (not a file in the folder)
                    if key == effective_prefix:
                        continue
                    
                    # Extract file name from the full path
                    # Format like 'consent_data/project1_Name/file.jpg' -> 'file.jpg'
                    file_name = key.split('/')[-1]
                    
                    files.append({
                        "name": file_name,
                        "path": key,
                        "size": obj['Size'],
                        "last_modified": obj['LastModified'].isoformat()
                    })
            
            return files
            
        except ClientError as e:
            logger.error(f"Error listing files: {str(e)}")
            raise
    
    def get_file_content(self, key: str) -> bytes:
        """
        Get the content of a file from S3.
        
        Args:
            key: The key of the file to get (full S3 path or path relative to base_prefix)
            
        Returns:
            File content as bytes
        """
        # Ensure the key has the base_prefix if it's not already included
        if self.base_prefix and not key.startswith(self.base_prefix):
            effective_key = f"{self.base_prefix}{key}"
        else:
            effective_key = key
            
        logger.info(f"Getting file content for key: {effective_key}")
        
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=effective_key
            )
            
            return response['Body'].read()
            
        except ClientError as e:
            logger.error(f"Error getting file content: {str(e)}")
            raise


def test_aws_s3_service():
    """
    Test function to verify AWS S3 connectivity and basic operations.
    Prints results to console for manual verification.
    """
    try:
        # Print environment variables (with partial masking for security)
        print("Environment variables:")
        for var_name in ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION", "AWS_BUCKET_NAME"]:
            value = os.getenv(var_name, "")
            if var_name in ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"] and value:
                # Show just first 5 and last 4 characters
                masked_value = value[:5] + "..." + value[-4:] if len(value) > 9 else "***masked***"
                print(f"  {var_name}={masked_value}")
            else:
                print(f"  {var_name}={value}")
        
        print("\nInitializing AWS S3 Service...")
        s3_service = AWSS3Service()
        
        print("\nTesting connection...")
        connection_result = s3_service.test_connection()
        print(f"Connection test result: {connection_result}")
        
        # If standard connection tests fail, try direct object access instead
        # This works better when the IAM policy only allows specific object operations
        
        print("\nAttempting direct object access tests...")
        
        # Try accessing objects with common patterns for consent folders
        test_paths = [
            # Common project folder paths
            "projects/",
            "consent/",
            "consent_data/",
            "data/",
            
            # More specific paths
            "projects/project1_TestProject/",
            "consent_data/project1_TestProject/",
            "data/project1_TestProject/"
        ]
        
        success = False
        
        for path in test_paths:
            print(f"\nTesting access to path: '{path}'")
            try:
                # Try to list objects with this prefix
                response = s3_service.s3_client.list_objects_v2(
                    Bucket=s3_service.bucket_name,
                    Prefix=path,
                    MaxKeys=10
                )
                
                # If we get here, we have access
                print(f"Success! We have access to list objects with prefix '{path}'")
                
                # Check if there are any objects
                if 'Contents' in response:
                    print(f"Found {len(response['Contents'])} objects:")
                    for obj in response['Contents'][:5]:  # Limit to first 5
                        print(f"  - {obj['Key']} (size: {obj['Size']} bytes)")
                    if len(response['Contents']) > 5:
                        print(f"  ... and {len(response['Contents']) - 5} more")
                else:
                    print("No objects found with this prefix")
                
                success = True
                
            except Exception as e:
                print(f"Error accessing path '{path}': {str(e)}")
        
        if not success:
            print("\nAll direct access tests failed. There might be an issue with the credentials or permissions.")
            print("Please verify the following:")
            print("1. The AWS credentials are correct")
            print("2. The user has permissions to access the bucket or specific paths")
            print("3. The bucket name 'chwarel-sandbox' is correct")
            print("4. The bucket exists in the specified region ('us-east-1' by default)")
        
        # Try with specific prefixes that might exist even if direct access failed
        print("\nTrying additional folder listing approaches...")
        try:
            # Try without a prefix first
            print("\nListing top-level folders (no prefix)...")
            folders = s3_service.list_folders()
            print(f"Found {len(folders)} folders:")
            for folder in folders:
                print(f"  - {folder['name']} (path: {folder['path']})")
        except Exception as e:
            print(f"Error listing top-level folders: {str(e)}")
        
        # Try with specific prefixes
        test_prefixes = ["consent_data/", "projects/", "data/"]
        for prefix in test_prefixes:
            print(f"\nTrying to list folders with prefix '{prefix}'...")
            try:
                folders = s3_service.list_folders(prefix)
                print(f"Found {len(folders)} folders:")
                for folder in folders:
                    print(f"  - {folder['name']} (path: {folder['path']}")
                    
                    # If we found folders, try to list files in the first one
                    if len(folders) > 0:
                        first_folder = folders[0]
                        print(f"\n  Files in folder {first_folder['name']}:")
                        try:
                            files = s3_service.list_files(first_folder['name'])
                            if files:
                                for file in files[:5]:  # Limit to first 5 files for brevity
                                    print(f"    - {file['name']} (size: {file['size']} bytes)")
                                if len(files) > 5:
                                    print(f"    ... and {len(files) - 5} more files")
                            else:
                                print("    No files found")
                        except Exception as e:
                            print(f"    Error listing files: {str(e)}")
            except Exception as e:
                print(f"Error listing folders with prefix '{prefix}': {str(e)}")
        
        print("\nTest completed!")
        
    except Exception as e:
        print(f"Error during test: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # This allows running this module directly to test AWS S3 connectivity
    test_aws_s3_service() 