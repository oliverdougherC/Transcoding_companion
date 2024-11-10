import warnings
warnings.filterwarnings("ignore", category=Warning)
import requests
import os
from dotenv import load_dotenv
import sys
import re

def get_proper_title(colloquial_title):
    """
    Convert a colloquial movie title to proper format with year using OMDb API
    Args:
        colloquial_title (str): Informal movie title
    Returns:
        str: Formatted title as "Movie Title (Year)" or None if not found
    """
    load_dotenv()
    api_key = os.getenv('OMDB_API_KEY')
    
    if not api_key:
        raise ValueError("OMDB_API_KEY not found in environment variables")
    
    # Clean up the title before querying
    clean_title = colloquial_title.replace('.', ' ').replace('(', '').replace(')', '')
    
    # Find all years in the string
    year_matches = list(re.finditer(r'\b(19|20)\d{2}\b', clean_title))
    
    if year_matches:
        # Take the last year found as the release year
        release_year = year_matches[-1].group(0)
        # Keep everything before any additional content after the release year
        clean_title = clean_title[:year_matches[-1].start()].strip()
        
        # If there are other years in the title, preserve them
        for match in year_matches[:-1]:
            year_in_title = match.group(0)
            if year_in_title in clean_title:
                clean_title = clean_title  # Keep the year if it's part of the title
    
    # Prepare the API request
    url = f"http://www.omdbapi.com/?t={clean_title}&apikey={api_key}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if data.get('Response') == 'True':
            # Clean the title by removing any trailing year in parentheses
            title = data.get('Title')
            if '(' in title:
                title = title.split('(')[0].strip()
            year = data.get('Year')
            return f"{title} ({year})"
        else:
            return None
            
    except requests.RequestException as e:
        print(f"Error fetching data from OMDb: {e}")
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
