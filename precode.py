import os
import mimetypes
import subprocess

def is_video_file(filename):
    # Get the MIME type of the file
    mime_type, _ = mimetypes.guess_type(filename)
    # Check if it's a video file
    return mime_type and mime_type.startswith('video/')

def process_directory(directory_path):
    # Iterate through all files in the directory
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        
        # Skip if it's a directory
        if os.path.isdir(file_path):
            continue
            
        # Check if it's a video file
        if is_video_file(file_path):
            # Run the rename script on video files
            try:
                subprocess.run(['python3', 'scripts/rename.py', file_path], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error processing video file {filename}: {e}")
        else:
            # Delete non-video files
            try:
                os.remove(file_path)
                print(f"Deleted non-video file: {filename}")
            except OSError as e:
                print(f"Error deleting file {filename}: {e}")

if __name__ == "__main__":
    # Get the current directory
    current_dir = os.getcwd()
    process_directory(current_dir)
