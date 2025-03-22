import os
import sys

def check_file_exists(file_path):
    exists = os.path.exists(file_path)
    print(f"File {file_path}: {'EXISTS' if exists else 'DOES NOT EXIST'}")
    return exists

def check_directory_exists(dir_path):
    exists = os.path.exists(dir_path) and os.path.isdir(dir_path)
    print(f"Directory {dir_path}: {'EXISTS' if exists else 'DOES NOT EXIST'}")
    if exists:
        print(f"Contents of {dir_path}: {os.listdir(dir_path)}")
    return exists

def main():
    print("Checking RebelSCRIBE project structure...")
    
    # Check directories
    check_directory_exists("src")
    check_directory_exists("src/backend")
    check_directory_exists("src/backend/models")
    check_directory_exists("src/backend/services")
    check_directory_exists("src/utils")
    
    # Check files
    check_file_exists("src/backend/models/documentation.py")
    check_file_exists("src/backend/services/documentation_manager.py")
    check_file_exists("src/utils/logging_utils.py")
    check_file_exists("src/utils/file_utils.py")
    check_file_exists("src/utils/config_manager.py")
    check_file_exists("src/utils/document_cache.py")
    
    print("\nChecking Python imports...")
    try:
        import src.backend.models.documentation
        print("Import src.backend.models.documentation: SUCCESS")
    except ImportError as e:
        print(f"Import src.backend.models.documentation: FAILED - {e}")
    
    try:
        import src.backend.services.documentation_manager
        print("Import src.backend.services.documentation_manager: SUCCESS")
    except ImportError as e:
        print(f"Import src.backend.services.documentation_manager: FAILED - {e}")
    
    try:
        import src.utils.logging_utils
        print("Import src.utils.logging_utils: SUCCESS")
    except ImportError as e:
        print(f"Import src.utils.logging_utils: FAILED - {e}")

if __name__ == "__main__":
    main()
