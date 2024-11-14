import subprocess
import logging

def check_video_stream(file_path):
    """
    Check if video file has valid video stream and is not all black
    Args:
        file_path (str): Path to video file
    Returns:
        bool: True if video stream is valid, False otherwise
    """
    try:
        # Check video stream presence
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=codec_type,duration',
            '-of', 'json',
            str(file_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logging.error(f"FFprobe error: {result.stderr}")
            return False
            
        # Check for black frames
        cmd_black = [
            'ffmpeg',
            '-i', str(file_path),
            '-vf', 'blackdetect=d=1:pix_th=0.00',
            '-an',
            '-f', 'null',
            '-'
        ]
        
        result_black = subprocess.run(cmd_black, capture_output=True, text=True)
        
        # If there's a long black section (>1s), log it
        if "black_start" in result_black.stderr:
            logging.warning(f"Black frames detected in {file_path}")
            # You might want to adjust this threshold based on your needs
            if result_black.stderr.count("black_start") > 5:
                logging.error(f"Too many black sections in {file_path}")
                return False
                
        return True
        
    except subprocess.SubprocessError as e:
        logging.error(f"Error checking video stream: {e}")
        return False 