import os
import shutil
from pathlib import Path
import scripts.rename as rename
import scripts.audio_test as audio_test

def process_video_files(source_dir, destination_dir):
    # Create destination directory if it doesn't exist
    os.makedirs(destination_dir, exist_ok=True)
    
    # Video file extensions to check
    video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.wmv')
    
    # Iterate through all files in source directory
    for filename in os.listdir(source_dir):
        file_path = os.path.join(source_dir, filename)
        
        # Check if it's a file and has video extension
        if os.path.isfile(file_path) and filename.lower().endswith(video_extensions):
            try:
                # Step 2: Run through rename.py
                renamed_success = rename.process_file(file_path)
                
                if renamed_success:
                    # Step 3: Run through audio_test.py
                    audio_level = audio_test.check_audio_level(file_path)
                    
                    # Step 4: If audio level passes threshold, move file
                    if audio_level < -35:
                        shutil.move(file_path, os.path.join(destination_dir, filename))
                        print(f"Successfully processed and moved: {filename}")
                    else:
                        print(f"Audio level check failed for: {filename}")
                else:
                    print(f"Rename failed for: {filename}")
                    
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")

if __name__ == "__main__":
    # Example usage
    source_directory = "path/to/source/directory"
    destination_directory = "path/to/destination/directory"
    process_video_files(source_directory, destination_directory)
