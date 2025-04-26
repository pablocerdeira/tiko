#!/usr/bin/env python3
"""
Web content extractor module for Tiko.
Provides functionality to download and cache web content from various sources.
"""
import os
import time
import hashlib
import random
import logging
import requests
import datetime
import uuid
from werkzeug.utils import secure_filename

# Get the logger
logger = logging.getLogger("tiko")

# URL content cache
url_cache = {}
CACHE_EXPIRY = 600  # Cache expiry in seconds (10 minutes)

def get_site_specific_headers(url):
    """Return site-specific headers to bypass blocking."""
    # Base headers for most sites
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Referer": "https://www.google.com/",
        "sec-ch-ua": "\"Not A(Brand\";v=\"99\", \"Google Chrome\";v=\"120\", \"Chromium\";v=\"120\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0"
    }
    
    # Additional site-specific configurations
    if "uol.com.br" in url:
        # UOL seems to check for cookies and referrers
        headers["Referer"] = "https://www.google.com/search?q=noticias+uol"
        headers["Cookie"] = "UOL_SIBrowserId=" + ''.join(random.choices('0123456789abcdef', k=32))
    
    elif "globo.com" in url:
        # G1/Globo may check for specific Referer
        headers["Referer"] = "https://www.google.com/search?q=noticias+g1"
    
    elif "folha.uol.com.br" in url:
        # Folha has additional protection
        headers["Referer"] = "https://www.google.com/search?q=folha+de+sao+paulo"
    
    return headers

def generate_filename_from_url(url):
    """Generate a safe and descriptive filename from a URL."""
    # Try to detect content type from URL
    file_extension = os.path.splitext(url)[1].lower()

    # Get the filename from URL or use a timestamp + UUID
    try:
        url_filename = url.rstrip('/').split('/')[-1]
        # If URL ends with / or has no identifiable filename/extension
        if not url_filename or '.' not in url_filename:
            # Try to create a more descriptive filename by using URL parts
            parts = url.split('/')
            if len(parts) > 3:
                domain = parts[2].split('.')[0] if len(parts) > 2 else 'unknown'
                path_parts = [p for p in parts[3:] if p and p != 'index.html']
                if path_parts:
                    path_slug = '-'.join(path_parts)[:50]  # Limit length
                    url_filename = f"{domain}-{path_slug}.html"
                else:
                    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                    url_filename = f"{domain}_{timestamp}.html"
            else:
                timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                url_filename = f"url_content_{timestamp}_{str(uuid.uuid4())[:8]}.html"  # Default to HTML extension
        
        # If filename has query parameters, clean it up
        if '?' in url_filename:
            clean_name = url_filename.split('?')[0]
            if clean_name and '.' in clean_name:
                url_filename = clean_name
            else:
                # Replace query parameters with safer version
                url_filename = url_filename.replace('?', '-').replace('&', '-').replace('=', '-')[:100] + '.html'
    except:
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        url_filename = f"url_content_{timestamp}_{str(uuid.uuid4())[:8]}.html"  # Default to HTML extension

    return secure_filename(url_filename)

def download_web_content(url, upload_folder):
    """Download content from a URL and save it to a file in the upload folder.
    
    Args:
        url (str): The URL to download content from
        upload_folder (str): The folder path to save the downloaded content
        
    Returns:
        str: The file path where the content is saved, or None if download failed
    """
    if not url or not url.startswith(('http://', 'https://')):
        logger.warning(f"Invalid URL: {url}")
        return None
        
    # Check if URL is in cache and not expired
    url_hash = hashlib.md5(url.encode()).hexdigest()
    current_time = time.time()
    
    if url_hash in url_cache:
        cache_entry = url_cache[url_hash]
        if current_time - cache_entry['timestamp'] < CACHE_EXPIRY:
            # Cache hit, return cached file path if it exists
            if os.path.exists(cache_entry['file_path']):
                logger.info(f"Using cached content for URL: {url}")
                return cache_entry['file_path']
    
    filename = generate_filename_from_url(url)
    file_path = os.path.join(upload_folder, filename)

    # Use site-specific headers for improved anti-blocking
    headers = get_site_specific_headers(url)

    # Try to download content with randomized delays to avoid triggering rate limits
    try:
        # Add small random delay to avoid rate limiting
        time.sleep(0.2 + (0.5 * random.random()))
        
        logger.info(f"Downloading content from URL: {url}")
        session = requests.Session()
        
        # First make a HEAD request to get cookies and check if URL exists
        head_resp = session.head(url, headers=headers, timeout=10, allow_redirects=True)
        
        # Then get the actual content
        r = session.get(url, headers=headers, timeout=30)
        r.raise_for_status()
        
        with open(file_path, 'wb') as f:
            f.write(r.content)
        
        # Add to cache
        url_cache[url_hash] = {
            'timestamp': current_time,
            'file_path': file_path
        }
        
        logger.info(f"URL content saved to: {file_path} (Size: {len(r.content)} bytes)")
        return file_path
    except Exception as e:
        logger.warning(f"Failed to download URL content {url}: {e}")
        return None

def get_input_file(req, upload_folder):
    """Gets the input file from the request. If there is a 'url' field in the form and it's a URL, 
    downloads the content and saves it to a temporary file. Otherwise, uses request.files['file'].
    
    Args:
        req: The Flask request object
        upload_folder (str): The folder path to save the downloaded content or uploaded file
        
    Returns:
        str: The file path of the input file, or None if no file could be obtained
    """
    # First, check if URL is provided in form data
    url = req.form.get('url', '').strip()

    # If not in form, check if it's in query parameters
    if not url:
        url = req.args.get('url', '').strip()

    if url and url.startswith(('http://', 'https://')):
        return download_web_content(url, upload_folder)
    else:
        # Otherwise, expect file upload in form-data
        if 'file' not in req.files:
            logger.warning("No file provided in request")
            return None
        file = req.files['file']
        if file.filename == '':
            logger.warning("Empty filename for uploaded file")
            return None
        filename = secure_filename(file.filename)
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        logger.info(f"File uploaded and saved to: {file_path}")
        return file_path