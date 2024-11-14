import warnings
warnings.filterwarnings("ignore", category=Warning)
import requests
import os
from dotenv import load_dotenv
import sys
import re
import logging

def get_proper_title(colloquial_title, is_tv=False):
    """
    Convert a colloquial title to proper format with year using OMDb API
    Args:
        colloquial_title (str): Informal title
        is_tv (bool): Whether this is a TV show
    Returns:
        str: Formatted title with year or None if not found
    """
    load_dotenv()
    api_key = os.getenv('OMDB_API_KEY')
    
    if not api_key:
        logging.error("OMDB_API_KEY not found in environment variables")
        return None
    
    # Clean up the title
    clean_title = re.sub(r'[._]', ' ', colloquial_title)
    clean_title = re.sub(r'\s+', ' ', clean_title).strip()
    
    # Remove season/episode information for TV shows
    if is_tv:
        clean_title = re.sub(r'[Ss](?:eason)?\s*\d+.*', '', clean_title)
        clean_title = re.sub(r'[Ee](?:pisode)?\s*\d+.*', '', clean_title)
        clean_title = re.sub(r'\d+x\d+.*', '', clean_title)
    
    # Special handling for numeric titles
    if clean_title.isdigit():
        search_title = clean_title
    else:
        # Extract year if present
        year_match = re.search(r'\b(19|20)\d{2}\b', clean_title)
        if year_match:
            year = year_match.group(0)
            clean_title = clean_title[:year_match.start()].strip()
        search_title = clean_title

    logging.info(f"Searching OMDB for title: {search_title}")
    
    # Prepare the API request
    url = f"http://www.omdbapi.com/?t={search_title}&type={'series' if is_tv else 'movie'}&apikey={api_key}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        logging.info(f"OMDB response: {data}")
        
        if data.get('Response') == 'True':
            title = data.get('Title')
            year = data.get('Year', '').split('–')[0]  # Get first year for TV series
            return f"{title} ({year})"
        else:
            logging.error(f"Title not found in OMDB: {search_title}")
            logging.error(f"OMDB error message: {data.get('Error')}")
            return None
            
    except requests.RequestException as e:
        logging.error(f"Error fetching data from OMDb: {e}")
        return None

if __name__ == "__main__":
    # Check if movie title was provided as argument
    if len(sys.argv) < 2:
        print("Usage: python3 title.py \"movie title\"")
        sys.exit(1)
        
    # Get movie title from command line argument
    title = sys.argv[1]
    proper_title = get_proper_title(title)
    if proper_title:
        print(proper_title)
    else:
        print("Movie not found or error occurred")
