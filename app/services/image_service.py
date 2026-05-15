import requests
import logging
import os
import uuid
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

LOGO_DEV_PUBLIC_KEY = os.getenv('LOGO_DEV_PUBLIC_KEY')
PEXELS_API_KEY = os.getenv('PEXELS_API_KEY')

def get_company_logo_path(domain: str):
    """
    Fetches the logo image for a given domain and saves it to a temporary file.
    Returns the path to the downloaded image.
    """
    if not domain or not LOGO_DEV_PUBLIC_KEY:
        return None
        
    # Clean domain name
    domain = domain.lower().strip().replace("http://", "").replace("https://", "").split("/")[0]
        
    url = f"https://img.logo.dev/{domain}?token={LOGO_DEV_PUBLIC_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Ensure temp directory exists
        temp_dir = Path("temp_images")
        temp_dir.mkdir(exist_ok=True)
        
        file_path = temp_dir / f"{uuid.uuid4()}.png"
        
        with open(file_path, "wb") as f:
            f.write(response.content)
            
        return str(file_path)
    except Exception as e:
        logging.error(f"Error fetching logo for {domain}: {e}")
        return None

def get_topic_image_path(query: str):
    """
    Searches Pexels for a query and downloads the first high-quality image found.
    Returns the path to the downloaded image.
    """
    if not query or not PEXELS_API_KEY:
        return None

    headers = {
        "Authorization": PEXELS_API_KEY
    }
    
    url = f"https://api.pexels.com/v1/search?query={query}&per_page=1"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data.get("photos"):
            logging.warning(f"No photos found on Pexels for query: {query}")
            return None
            
        # Get the large resolution image URL
        image_url = data["photos"][0]["src"]["large"]
        
        # Download the actual image
        img_response = requests.get(image_url, timeout=10)
        img_response.raise_for_status()
        
        # Ensure temp directory exists
        temp_dir = Path("temp_images")
        temp_dir.mkdir(exist_ok=True)
        
        # Extract extension from URL or default to jpg
        ext = image_url.split('.')[-1].split('?')[0]
        if len(ext) > 4: ext = "jpg"
        
        file_path = temp_dir / f"{uuid.uuid4()}.{ext}"
        
        with open(file_path, "wb") as f:
            f.write(img_response.content)
            
        return str(file_path)
    except Exception as e:
        logging.error(f"Error fetching Pexels image for {query}: {e}")
        return None

def cleanup_temp_images():
    """
    Deletes all temporary images in the temp_images directory.
    """
    temp_dir = Path("temp_images")
    if temp_dir.exists():
        for file in temp_dir.iterdir():
            try:
                if file.is_file():
                    os.remove(file)
            except Exception as e:
                logging.error(f"Error cleaning up temp image {file}: {e}")
