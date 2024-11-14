import os
import sys
import subprocess
import re
import logging
from pathlib import Path

def extract_tv_info(file_path):
    """
    Extract TV show information from complex directory structures and filenames
    Args:
        file_path (str): Full path to the file
    Returns:
        tuple: (show_name, season_num, episode_num) or (None, None, None)
    """
    path = Path(file_path)
    full_path = str(path)
    
    # Try to get show name from parent directories first
    show_name = None
    for parent in path.parents:
        if any(str(season_dir.name).lower().startswith('season') for season_dir in parent.glob('Season *')):
            show_name = parent.name
            break
    
    if not show_name:
        # Try to extract from filename
        filename_match = re.match(r'(.+?)(?:\s+[Ss]eason|\s+[Ss]\d)', path.stem, re.IGNORECASE)
        if filename_match:
            show_name = filename_match.group(1)
    
    # Clean up show name
    if show_name:
        show_name = re.sub(r'[._]', ' ', show_name).strip()
    
    # Find season number
    season_patterns = [
        r'Season\s*(\d{1,2})',           # Matches "Season 4" in directory
        r'[Ss](\d{1,2})[Ee]\d{1,2}',     # Matches "S4E1"
        r'season\s*(\d{1,2})\s*episode',  # Matches "season 1 episode"
    ]
    
    season_num = None
    # First check directory name
    for parent in path.parents:
        for pattern in season_patterns:
            match = re.search(pattern, str(parent.name), re.IGNORECASE)
            if match:
                season_num = match.group(1).zfill(2)
                break
        if season_num:
            break
    
    # If not found in directory, check filename
    if not season_num:
        for pattern in season_patterns:
            match = re.search(pattern, path.name, re.IGNORECASE)
            if match:
                season_num = match.group(1).zfill(2)
                break
    
    # Find episode number
    episode_patterns = [
        r'[Ee](\d{1,2})',                # Matches "E1"
        r'[Ss]\d{1,2}[Ee](\d{1,2})',     # Matches "S4E1"
        r'episode\s*(\d{1,2})',          # Matches "episode 1"
    ]
    
    episode_num = None
    for pattern in episode_patterns:
        match = re.search(pattern, path.name, re.IGNORECASE)
        if match:
            episode_num = match.group(1).zfill(2)
            break
    
    logging.info(f"Extracted TV info - Show: {show_name}, Season: {season_num}, Episode: {episode_num}")
    
    if show_name and season_num and episode_num:
        return show_name, season_num, episode_num
    return None, None, None

def create_tv_structure(base_path, show_title, season_num):
    """Create TV show directory structure"""
    show_path = Path(base_path) / show_title
    season_path = show_path / f"Season {int(season_num)}"  # Remove leading zero for folder name
    os.makedirs(season_path, exist_ok=True)
    return season_path

def rename_media_file(file_path):
    """Renames a media file using the proper title format"""
    if not os.path.exists(file_path):
        logging.error(f"Error: File {file_path} not found")
        return None
        
    directory = os.path.dirname(file_path)
    filename = os.path.basename(file_path)
    file_extension = os.path.splitext(filename)[1]
    
    # Try to extract TV show information
    show_name, season_num, episode_num = extract_tv_info(file_path)
    is_tv = bool(show_name and season_num and episode_num)
    
    try:
        if is_tv:
            # Use the extracted show name for OMDB lookup
            search_name = show_name
            logging.info(f"Searching for TV show: {search_name}")
        else:
            search_name = os.path.splitext(filename)[0]
            logging.info(f"Searching for movie: {search_name}")
        
        result = subprocess.run(
            ['python3', 'scripts/title.py', search_name, '--tv' if is_tv else '--movie'],
            capture_output=True,
            text=True
        )
        proper_title = result.stdout.strip()
        
        if proper_title and "not found" not in proper_title.lower():
            if is_tv:
                # Extract base title and year
                base_title = proper_title.split('(')[0].strip()
                year = re.search(r'\((\d{4})\)', proper_title)
                year = year.group(1) if year else ''
                
                # Create show title with year
                show_title = f"{base_title} ({year})"
                
                # Create episode filename (just SXXEXX)
                new_filename = f"S{season_num}E{episode_num}{file_extension}"
                
                # Maintain directory structure
                relative_path = Path(file_path).relative_to(Path(directory).parent)
                new_dir = Path(directory) / relative_path.parent
                new_path = new_dir / new_filename
            else:
                new_path = Path(directory) / (proper_title + file_extension)
            
            # Create directory if it doesn't exist
            os.makedirs(new_path.parent, exist_ok=True)
            
            # Rename and move the file
            os.rename(file_path, new_path)
            logging.info(f"Successfully renamed and moved:\n{filename} -> {new_path}")
            return str(new_path)
        else:
            logging.error(f"Could not get proper title for: {search_name}")
            return None
            
    except subprocess.SubprocessError as e:
        logging.error(f"Error running title.py: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 rename.py <movie_file_path>")
        sys.exit(1)
        
    file_path = sys.argv[1]
    rename_media_file(file_path)
