import os
import sys
import subprocess

def rename_movie_file(file_path):
    """
    Renames a movie file using the proper title format from title.py
    Args:
        file_path (str): Path to the movie file to rename
    Returns:
        bool: True if rename successful, False otherwise
    """
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found")
        return False
        
    # Get the directory and filename
    directory = os.path.dirname(file_path)
    filename = os.path.basename(file_path)
    
    # Get file extension
    file_extension = os.path.splitext(filename)[1]
    
    # Get current name without extension
    current_name = os.path.splitext(filename)[0]
    
    # Call title.py as a subprocess to get proper title
    try:
        result = subprocess.run(['python3', 'title.py', current_name], 
                              capture_output=True, 
                              text=True)
        proper_title = result.stdout.strip()
        
        if proper_title and "not found" not in proper_title:
            # Create new filename with proper title
            new_filename = proper_title + file_extension
            new_path = os.path.join(directory, new_filename)
            
            # Rename the file
            os.rename(file_path, new_path)
            print(f"Successfully renamed:\n{filename} -> {new_filename}")
            return True
        else:
            print(f"Could not get proper title for: {current_name}")
            return False
            
    except subprocess.SubprocessError as e:
        print(f"Error running title.py: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 rename.py <movie_file_path>")
        sys.exit(1)
        
    file_path = sys.argv[1]
    rename_movie_file(file_path)
