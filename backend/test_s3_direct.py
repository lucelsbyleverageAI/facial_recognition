import boto3
import traceback
from botocore.exceptions import ClientError

def test_s3_connection():
    """
    Test direct S3 connection using the provided credentials and approach.
    This follows exactly the example provided by your colleague.
    """
    print("Testing S3 connection with provided credentials...")
    print("==================================================")
    
    # Their exact approach with session
    try:
        session = boto3.Session(
            aws_access_key_id='AKIAXWAUPJ5HMXPHSVCL',
            aws_secret_access_key='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',
            region_name='us-east-1'
        )
        s3_client = session.client('s3')
        bucket_name = 'chwarel-sandbox'
        print("Session and client created successfully.")
    except Exception as e:
        print(f"Error creating session: {str(e)}")
        return
    
    # Test 1: List top-level folders
    print("\nTest 1: Listing top-level folders using list_objects_v2 with Delimiter='/'...")
    print("--------------------------------------------------------------------------")
    try:
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Delimiter='/'
        )
        
        if 'CommonPrefixes' in response:
            print("Success! Folders in bucket:")
            for folder in response['CommonPrefixes']:
                print(f"  - {folder['Prefix']}")
        else:
            print("No folders found in the bucket.")
            
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"ClientError in Test 1: {error_code} - {error_message}")
    except Exception as e:
        print(f"Error in Test 1: {str(e)}")
        
    # Test 2: List specific folders with a prefix
    print("\nTest 2: Listing folders with specific prefixes...")
    print("------------------------------------------------")
    test_prefixes = ["consent_data/", "projects/", "data/"]
    for prefix in test_prefixes:
        print(f"\n  2.{test_prefixes.index(prefix)+1}: Testing prefix='{prefix}'...")
        try:
            response = s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=prefix,
                Delimiter='/'
            )
            
            if 'CommonPrefixes' in response:
                print(f"  Success! Folders under '{prefix}':")
                for folder in response['CommonPrefixes']:
                    print(f"    - {folder['Prefix']}")
            else:
                print(f"  No folders found under '{prefix}'.")
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            print(f"  ClientError: {error_code} - {error_message}")
        except Exception as e:
            print(f"  Error: {str(e)}")
    
    # Test 3: Try to get a specific object (will fail with NoSuchKey if the object doesn't exist)
    print("\nTest 3: Attempting to get a non-existent object...")
    print("------------------------------------------------")
    non_existent_key = 'test-file-that-does-not-exist.txt'
    
    try:
        response = s3_client.get_object(
            Bucket=bucket_name,
            Key=non_existent_key
        )
        print("Unexpectedly succeeded in getting a non-existent object!")
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        
        if error_code == 'NoSuchKey':
            print("Success! Got expected NoSuchKey error for non-existent object.")
        else:
            print(f"ClientError: {error_code} - {error_message}")
    except Exception as e:
        print(f"Error: {str(e)}")
    
    # Test 4: Try to list all objects to see if any are accessible
    print("\nTest 4: Listing all objects in the bucket...")
    print("-------------------------------------------")
    try:
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            MaxKeys=10
        )
        
        if 'Contents' in response:
            print(f"Success! Found {len(response['Contents'])} objects:")
            for obj in response['Contents'][:5]:  # Show first 5
                print(f"  - {obj['Key']} (size: {obj['Size']} bytes)")
            if len(response['Contents']) > 5:
                print(f"  ... and {len(response['Contents']) - 5} more objects")
        else:
            print("No objects found in the bucket.")
            
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"ClientError: {error_code} - {error_message}")
    except Exception as e:
        print(f"Error: {str(e)}")

    print("\nTest 5: Try head_bucket to check if the bucket exists...")
    print("-----------------------------------------------------")
    try:
        response = s3_client.head_bucket(Bucket=bucket_name)
        print("Success! Bucket exists and is accessible.")
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"ClientError: {error_code} - {error_message}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    try:
        test_s3_connection()
        print("\nTest script completed!")
    except Exception as e:
        print(f"Unexpected error in script: {str(e)}")
        traceback.print_exc() 