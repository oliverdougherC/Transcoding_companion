import os
import shutil
import logging
from pathlib import Path
import json
import re
import concurrent.futures
import pickle
from datetime import datetime
import scripts.rename as rename
import scripts.audio_test as audio_test
import scripts.video_test as video_test
import scripts.handbrake as handbrake

def setup_logging():
    """Configure logging to both file and console with timestamp"""
    # Create logs directory if it doesn't exist
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)
    
    # Create log file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f'media_processor_{timestamp}.log'
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logging.info("=== Starting New Processing Session ===")
    logging.info(f"Log file: {log_file}")

def load_progress():
    """Load progress from checkpoint file"""
    try:
        with open('.progress.pkl', 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        return set()

def save_progress(processed_files):
    """Save progress to checkpoint file"""
    with open('.progress.pkl', 'wb') as f:
        pickle.dump(processed_files, f)

def parse_tv_show(file_path):
    """
    Parse TV show information from file path
    Returns: (show_title, season_num, episode_num) or None if not a TV show
    """
    path = Path(file_path)
    
    # First, try to get show name from directory structure
    show_name = None
    season_num = None
    
    # Look for show name (parent of "Season X" directory)
    for parent in path.parents:
        if parent.name.lower().startswith('season '):
            show_name = parent.parent.name
            season_match = re.search(r'season\s*(\d+)', parent.name, re.IGNORECASE)
            if season_match:
                season_num = int(season_match.group(1))
            break
    
    if not show_name or not season_num:
        return None
        
    # Find episode number in filename
    episode_patterns = [
        r'[Ee](\d{1,2})',                # Matches "E1"
        r'[Ss]\d{1,2}[Ee](\d{1,2})',     # Matches "S4E1"
        r'episode\s*(\d{1,2})',          # Matches "episode 1"
    ]
    
    episode_num = None
    for pattern in episode_patterns:
        match = re.search(pattern, path.name, re.IGNORECASE)
        if match:
            episode_num = int(match.group(1))
            break
    
    if not episode_num:
        return None
        
    return (show_name, season_num, episode_num)

def create_tv_structure(base_path, show_title, season_num):
    """Create TV show directory structure"""
    show_path = Path(base_path) / show_title
    season_path = show_path / f"Season {season_num}"
    os.makedirs(season_path, exist_ok=True)
    return season_path

def cleanup_failed_file(file_path):
    """Remove failed transcoded file and log it"""
    try:
        Path(file_path).unlink(missing_ok=True)
        logging.info(f"Cleaned up failed file: {file_path}")
    except Exception as e:
        logging.error(f"Error cleaning up {file_path}: {e}")

def cleanup_source_file(file_path):
    """Remove original source file after successful processing"""
    try:
        Path(file_path).unlink(missing_ok=True)
        logging.info(f"Cleaned up source file: {file_path}")
    except Exception as e:
        logging.error(f"Error cleaning up source {file_path}: {e}")

def move_to_final_destination(source_path, config):
    """Move processed file to its final destination"""
    try:
        source_path = Path(source_path)
        tv_info = parse_tv_show(source_path)
        
        if tv_info:
            # For TV shows
            show_title, season_num, episode_num = tv_info
            dest_dir = create_tv_structure(config['tv_directory'], show_title, season_num)
            
            # Create simplified episode filename: SXXEXX.ext
            episode_filename = f"S{season_num:02d}E{episode_num:02d}{source_path.suffix}"
            dest_path = dest_dir / episode_filename
            
            logging.info(f"TV Show detected: {show_title} - Season {season_num} Episode {episode_num}")
        else:
            # For movies
            dest_dir = Path(config['movies_directory'])
            dest_path = dest_dir / source_path.name
            
        # Create destination directory if it doesn't exist
        os.makedirs(dest_dir, exist_ok=True)
        
        # Move the file
        shutil.move(str(source_path), str(dest_path))
        logging.info(f"Moved {source_path.name} to {dest_path}")
        return True
        
    except Exception as e:
        logging.error(f"Error moving file {source_path}: {e}")
        return False

def test_transcoded_file(file_path):
    """Run comprehensive quality tests on transcoded file"""
    try:
        # Check file exists and has size
        if not file_path.exists() or file_path.stat().st_size == 0:
            logging.error(f"File missing or empty: {file_path}")
            return False
            
        # Check video stream
        if not video_test.check_video_stream(str(file_path)):
            logging.error(f"Video stream test failed: {file_path}")
            return False
            
        # Check audio levels
        volume = audio_test.get_average_volume(str(file_path))
        if volume is None or volume < -70:  # -70 dB threshold for silence
            logging.error(f"Audio test failed: {file_path}")
            return False
            
        logging.info(f"All quality tests passed: {file_path}")
        return True
        
    except Exception as e:
        logging.error(f"Error during quality testing: {e}")
        return False

def process_all_files(config):
    """Process all media files in stages"""
    source_dir = Path(config['source_directory'])
    processed_files = load_progress()
    
    # Get list of video files
    video_files = [
        f for f in source_dir.glob('**/*')
        if f.suffix.lower() in ('.mp4', '.mkv', '.avi', '.mov')
        and str(f) not in processed_files
    ]
    
    if not video_files:
        logging.info("No new files to process")
        return

    # Stage 1: Rename all files (keeping original structure)
    logging.info("=== Stage 1: Renaming Files ===")
    renamed_files = []
    for file_path in video_files:
        logging.info(f"Processing: {file_path}")
        tv_info = parse_tv_show(file_path)
        
        if tv_info:
            show_title, season_num, episode_num = tv_info
            new_filename = f"S{season_num:02d}E{episode_num:02d}{file_path.suffix}"
            new_path = file_path.parent / new_filename
            os.rename(file_path, new_path)
            renamed_files.append(new_path)
            logging.info(f"Renamed to: {new_path}")
        else:
            renamed_files.append(file_path)

    # Stage 2: Transcode files
    logging.info("\n=== Stage 2: Transcoding Files ===")
    transcoded_files = []
    for source_path in renamed_files:
        tv_info = parse_tv_show(source_path)
        
        if tv_info:
            show_title, season_num, _ = tv_info
            transcode_path = create_tv_structure(
                config['transcode_directory'],
                show_title,
                season_num
            ) / source_path.name.replace(source_path.suffix, '.mkv')
        else:
            transcode_path = Path(config['transcode_directory']) / source_path.name.replace(source_path.suffix, '.mkv')
        
        logging.info(f"Transcoding: {source_path} -> {transcode_path}")
        if handbrake.transcode_video(str(source_path), str(transcode_path)):
            transcoded_files.append(transcode_path)
        else:
            logging.error(f"Failed to transcode: {source_path}")

    # Stage 3: Test all transcoded files
    logging.info("\n=== Stage 3: Testing Files ===")
    passed_files = []
    for transcode_path in transcoded_files:
        logging.info(f"Testing: {transcode_path}")
        if test_transcoded_file(transcode_path):
            passed_files.append(transcode_path)
        else:
            logging.error(f"Failed quality tests: {transcode_path}")
            cleanup_failed_file(transcode_path)

    if not passed_files:
        logging.error("No files passed quality tests. Stopping process.")
        return

    # Stage 4: Move files to final destination
    logging.info("\n=== Stage 4: Moving Files to Final Destination ===")
    for transcode_path in passed_files:
        if move_to_final_destination(transcode_path, config):
            # Find the original source file
            source_path = next((p for p in renamed_files if p.stem == transcode_path.stem), None)
            if source_path:
                cleanup_source_file(source_path)
                processed_files.add(str(source_path))
                save_progress(processed_files)
        else:
            logging.error(f"Failed to move file to destination: {transcode_path}")

    logging.info("\n=== Processing Complete ===")

if __name__ == "__main__":
    try:
        # Create logs directory and setup logging
        setup_logging()
        
        # Read configuration
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
            
        # Create required directories
        required_dirs = [
            'source_directory', 
            'transcode_directory', 
            'movies_directory', 
            'tv_directory'
        ]
        
        for dir_key in required_dirs:
            os.makedirs(config[dir_key], exist_ok=True)
            logging.info(f"Created/verified directory: {config[dir_key]}")
            
        # Process files
        process_all_files(config)
        
    except Exception as e:
        logging.error(f"Fatal error: {e}")
