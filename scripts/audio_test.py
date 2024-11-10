import subprocess
import json
import sys

def get_average_volume(file_path):
    """
    Calculate the average volume level in decibels for a video file using ffmpeg
    Args:
        file_path (str): Path to the video file
    Returns:
        float: Average volume in dB, or None if analysis fails
    """
    try:
        # Run ffmpeg with volume detection filter
        cmd = [
            'ffmpeg',
            '-i', file_path,
            '-af', 'volumedetect',
            '-vn',  # Skip video
            '-sn',  # Skip subtitles
            '-dn',  # Skip data
            '-f', 'null',
            '-'
        ]

        # Run command and capture stderr where ffmpeg writes the volume stats
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Parse mean volume from ffmpeg output
        for line in result.stderr.split('\n'):
            if 'mean_volume' in line:
                # Extract the dB value
                mean_db = float(line.split(':')[1].strip().replace(' dB', ''))
                return mean_db
                
        print(f"Could not find volume information in {file_path}")
        return None
        
    except subprocess.SubprocessError as e:
        print(f"Error running ffmpeg: {e}")
        return None
    except ValueError as e:
        print(f"Error parsing ffmpeg output: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 audio_level_test.py <video_file_path>")
        sys.exit(1)
        
    file_path = sys.argv[1]
    avg_volume = get_average_volume(file_path)
    
    if avg_volume is not None:
        print(f"Average volume: {avg_volume:.1f} dB")
    else:
        print("Could not determine average volume")
