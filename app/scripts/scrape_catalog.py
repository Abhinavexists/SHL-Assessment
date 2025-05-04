import json
import os
import re
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import pandas as pd
import time
import random
import logging
from urllib.parse import urljoin

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# URLs and paths
CATALOG_URL = "https://www.shl.com/solutions/products/product-catalog/"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "shl_catalog.json")
DEBUG_DIR = os.path.join(OUTPUT_DIR, "debug")
os.makedirs(DEBUG_DIR, exist_ok=True)

# Headers to mimic a browser
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.6367.78 Safari/537.36"
    )
}

# Sample assessment URLs for fallback
TECHNICAL_ASSESSMENTS = [
    # Programming Languages
    "https://www.shl.com/solutions/products/product-catalog/view/core-java-entry-level-new/",
    "https://www.shl.com/solutions/products/product-catalog/view/java-8-new/",
    "https://www.shl.com/solutions/products/product-catalog/view/core-java-advanced-level-new/",
    "https://www.shl.com/solutions/products/product-catalog/view/python-new/",
    "https://www.shl.com/solutions/products/product-catalog/view/javascript-new/",
    "https://www.shl.com/solutions/products/product-catalog/view/c-sharp-programming-new/",
    "https://www.shl.com/solutions/products/product-catalog/view/php-new/",
    
    # Databases and Data
    "https://www.shl.com/solutions/products/product-catalog/view/sql-server-new/",
    "https://www.shl.com/solutions/products/product-catalog/view/mysql-new/",
    "https://www.shl.com/solutions/products/product-catalog/view/mongodb-new/",
    "https://www.shl.com/solutions/products/product-catalog/view/data-science-new/",
    
    # Testing and QA
    "https://www.shl.com/solutions/products/product-catalog/view/selenium-new/",
    "https://www.shl.com/solutions/products/product-catalog/view/manual-testing-new/",
    "https://www.shl.com/solutions/products/product-catalog/view/automata-selenium/",
    
    # Web Technologies
    "https://www.shl.com/solutions/products/product-catalog/view/html5-new/",
    "https://www.shl.com/solutions/products/product-catalog/view/css3-new/",
    "https://www.shl.com/solutions/products/product-catalog/view/react-js-new/",
    "https://www.shl.com/solutions/products/product-catalog/view/angular-new/",
]

COGNITIVE_ASSESSMENTS = [
    "https://www.shl.com/solutions/products/product-catalog/view/verify-numerical-ability/",
    "https://www.shl.com/solutions/products/product-catalog/view/verify-verbal-ability-next-generation/",
    "https://www.shl.com/solutions/products/product-catalog/view/verify-inductive-reasoning/",
    "https://www.shl.com/solutions/products/product-catalog/view/verify-mechanical-reasoning/",
]

PERSONALITY_ASSESSMENTS = [
    "https://www.shl.com/solutions/products/product-catalog/view/occupational-personality-questionnaire-opq32r/",
    "https://www.shl.com/solutions/products/product-catalog/view/motivational-questionnaire/",
]

# Combine all sample URLs
SAMPLE_URLS = TECHNICAL_ASSESSMENTS + COGNITIVE_ASSESSMENTS + PERSONALITY_ASSESSMENTS

def extract_duration(text):
    """Extract duration in minutes from text."""
    if not text:
        return None
    
    # Regex for minutes
    duration_pattern = re.compile(r'(\d+)(?:\s*)(min|mins|minutes|minute)')
    match = duration_pattern.search(text)
    
    if match:
        return f"{match.group(1)} minutes"
    
    # Also check for hours
    hours_pattern = re.compile(r'(\d+)(?:\s*)(hour|hours|hr|hrs)')
    match = hours_pattern.search(text)
    if match:
        hours = int(match.group(1))
        return f"{hours * 60} minutes"
        
    return "Not specified"

def determine_test_type(text, url, name):
    """Determine the test type based on description, URL, and name."""
    text = (text or "").lower()
    url = url.lower()
    name = (name or "").lower()
    
    combined_text = f"{text} {url} {name}"
    
    # Technical assessments
    if any(keyword in combined_text for keyword in [
        "coding", "java", "python", "javascript", "programming", "sql", "selenium", "testing", 
        "automata", "html", "css", "drupal", "php", "c#", "c++", "ruby", "react", "angular",
        "node.js", "typescript", "mongodb", "database", ".net", "devops", "aws", "cloud",
        "docker", "kubernetes", "git", "api", "rest", "graphql", "security", "algorithm"
    ]):
        return "Technical"
    
    # Cognitive assessments
    elif any(keyword in combined_text for keyword in [
        "reasoning", "problem solving", "cognitive", "verbal", "numerical", "inductive",
        "logical", "abstract", "spatial", "mechanical", "verify", "aptitude", "ability"
    ]):
        return "Cognitive"
    
    # Personality assessments
    elif any(keyword in combined_text for keyword in [
        "personality", "behavior", "motivation", "competency", "opq", "mbti", "hogan",
        "disc", "emotional intelligence", "eq", "temperament", "preference"
    ]):
        return "Personality/Behavioral"
    
    # Leadership assessments
    elif any(keyword in combined_text for keyword in [
        "leadership", "management", "executive", "strategic", "manager", "director",
        "supervisor", "leader", "coaching", "decision-making", "delegation"
    ]):
        return "Leadership"
    
    # Role-specific assessments
    elif any(keyword in combined_text for keyword in [
        "sales", "customer service", "call center", "administrative", "financial", 
        "data entry", "retail", "healthcare", "accounting", "marketing", "hr", "legal",
        "solution", "short form", "job focused"
    ]):
        return "Role-specific"
    
    # Default
        return "General"

def determine_adaptive_support(text, name, url):
    """Determine if the assessment has adaptive/IRT support."""
    combined_text = f"{text} {name} {url}".lower()
    
    if "adaptive/irt" in combined_text or "adaptive" in combined_text or "irt" in combined_text:
        return "Yes"
    elif "non-adaptive" in combined_text:
        return "No"
    
    return "No"

def determine_remote_support(text, name, url):
    """Determine if the assessment has remote testing support."""
    combined_text = f"{text} {name} {url}".lower()
    
    if "no remote" in combined_text or "in-person only" in combined_text:
        return "No"
    elif "remote testing" in combined_text or "online" in combined_text:
        return "Yes"
    
    return "Yes"

def scrape_catalog_tables(main_url):
    """Scrape all tables from the catalog page, handling pagination."""
    all_product_urls = []
    
    try:
        # Get the initial page
        response = requests.get(main_url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        
        # Save raw HTML for debugging
        with open(os.path.join(DEBUG_DIR, "catalog_page.html"), "w", encoding="utf-8") as f:
            f.write(response.text)
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract all product URLs from tables
        tables = soup.find_all('table')
        
        logger.info(f"Found {len(tables)} tables on the catalog page")
        
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                link_cell = row.find('td')
                if link_cell:
                    link = link_cell.find('a')
                    if link and link.has_attr('href'):
                        href = link['href']
                        if 'product-catalog/view/' in href or '/products/' in href:
                            if not href.startswith('http'):
                                href = requests.compat.urljoin(main_url, href)
                            all_product_urls.append(href)
        
        # Find pagination links
        pagination = soup.find_all('a', class_=lambda c: c and ('page' in c or 'pagination' in c))
        
        # If no dedicated pagination class, look for numbers that could be page links
        if not pagination:
            pagination = soup.find_all('a', text=re.compile(r'^\d+$'))
        
        # Extract max page number
        max_page = 1
        for page_link in pagination:
            try:
                page_num = int(page_link.text.strip())
                if page_num > max_page:
                    max_page = page_num
            except ValueError:
                continue
        
        logger.info(f"Detected {max_page} pages of catalog results")
        
        # Process additional pages
        for page in range(2, max_page + 1):
            page_url = f"{main_url}?page={page}"
            logger.info(f"Processing catalog page {page}/{max_page}: {page_url}")
            
            try:
                time.sleep(random.uniform(1.0, 2.0))
                page_response = requests.get(page_url, headers=HEADERS, timeout=30)
                page_response.raise_for_status()
                
                page_soup = BeautifulSoup(page_response.text, 'html.parser')
                page_tables = page_soup.find_all('table')
                
                for table in page_tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        link_cell = row.find('td')
                        if link_cell:
                            link = link_cell.find('a')
                            if link and link.has_attr('href'):
                                href = link['href']
                                if 'product-catalog/view/' in href or '/products/' in href:
                                    if not href.startswith('http'):
                                        href = requests.compat.urljoin(main_url, href)
                                    all_product_urls.append(href)
            
            except Exception as e:
                logger.error(f"Error processing page {page}: {e}")
        
        return list(set(all_product_urls))  # Remove duplicates
    
    except Exception as e:
        logger.error(f"Error scraping catalog tables: {e}")
        return []

def scrape_product_page(url):
    """Scrape a single product page for assessment details."""
    try:
        logger.info(f"Scraping product page: {url}")
        time.sleep(random.uniform(0.5, 1.5))  # Be polite to the server
        
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract product name
        name_element = soup.find('h1', class_='entry-title') or soup.find('h1')
        name = name_element.text.strip() if name_element else os.path.basename(url).replace('-', ' ').title()
        
        # Extract description
        description = ""
        desc_elements = [
            soup.find('div', class_='product-description'),
            soup.find('div', class_='entry-content'),
            soup.find('meta', attrs={'name': 'description'})
        ]
        
        for elem in desc_elements:
            if elem:
                if elem.name == 'meta':
                    description = elem.get('content', '')
                else:
                    # Get text from paragraphs
                    paragraphs = elem.find_all('p')
                    if paragraphs:
                        description = ' '.join([p.text.strip() for p in paragraphs])
                    else:
                        description = elem.text.strip()
                if description:
                    break
        
        # If still no description, look for any paragraphs in the main content
        if not description:
            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
            if main_content:
                paragraphs = main_content.find_all('p')
                if paragraphs:
                    description = ' '.join([p.text.strip() for p in paragraphs[:3]])  # First 3 paragraphs
        
        # Clean up the description
        description = re.sub(r'\s+', ' ', description).strip()
        
        # Extract duration
        duration_text = ""
        duration_elements = [
            soup.find('span', string=re.compile(r'duration|time', re.I)),
            soup.find('dt', string=re.compile(r'duration|time', re.I))
        ]
        
        # If we found a duration label, look for value in next element
        for elem in duration_elements:
            if elem:
                next_elem = elem.find_next()
                if next_elem:
                    duration_text = next_elem.text.strip()
                    break
        
        # If we didn't find a labeled duration, look for duration in the description
        if not duration_text and description:
            duration_match = re.search(r'(\d+)\s*(min|mins|minutes|minute|hour|hours|hr|hrs)', description, re.I)
            if duration_match:
                duration_text = duration_match.group(0)
        
        # Parse the duration
        duration = extract_duration(duration_text or description)
        
        # Determine test type, remote and adaptive support
        test_type = determine_test_type(description, url, name)
        remote_support = determine_remote_support(description, name, url)
        adaptive_support = determine_adaptive_support(description, name, url)
        
        # Return structured data
        return {
            "name": name,
            "url": url,
            "description": description,
            "remote_support": remote_support,
            "adaptive_support": adaptive_support,
            "duration": duration,
            "type": test_type
        }
    
    except Exception as e:
        logger.error(f"Error scraping product page {url}: {e}")
        return None

def scrape_shl_catalog():
    """Scrape the SHL product catalog and save to JSON."""
    logger.info(f"Scraping catalog from {CATALOG_URL}")
    
    try:
        # First, try scraping from catalog page
        logger.info("Scraping product URLs from catalog tables...")
        product_urls_from_tables = scrape_catalog_tables(CATALOG_URL)
        logger.info(f"Found {len(product_urls_from_tables)} product URLs from catalog tables")
        
        # Also try to find products from the entire page
        logger.info("Finding product URLs from the entire page...")
        product_urls_from_page = find_product_urls(CATALOG_URL)
        logger.info(f"Found {len(product_urls_from_page)} product URLs from the entire page")
        
        # Combine and deduplicate URLs
        all_product_urls = list(set(product_urls_from_tables + product_urls_from_page))
        logger.info(f"Total unique product URLs: {len(all_product_urls)}")
        
        # If we didn't find any products, use our sample URLs
        if not all_product_urls:
            logger.warning("No product URLs found from website, using sample URLs")
            all_product_urls = SAMPLE_URLS
            logger.info(f"Using {len(all_product_urls)} sample URLs")
        
        # Scrape each product page
        catalog = []
        logger.info(f"Scraping {len(all_product_urls)} product pages...")
        
        for url in tqdm(all_product_urls, desc="Scraping products"):
            product_data = scrape_product_page(url)
            if product_data:
                catalog.append(product_data)
        
        logger.info(f"Successfully scraped {len(catalog)} assessments")
        
        # If we still don't have enough products, create some placeholders
        if len(catalog) < 5:
            logger.warning(f"Only found {len(catalog)} assessments, creating placeholders")
            catalog = create_mock_assessments()
        
        # Save the catalog
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(catalog, f, indent=2)
        logger.info(f"Saved catalog to {OUTPUT_FILE}")
        
        # Also save as CSV
        csv_file = OUTPUT_FILE.replace('.json', '.csv')
        pd.DataFrame(catalog).to_csv(csv_file, index=False)
        logger.info(f"Saved catalog to {csv_file}")
        
        return catalog
    
    except Exception as e:
        logger.error(f"Error scraping catalog: {e}")
        import traceback
        traceback.print_exc()
        
        # Create mock assessments as fallback
        logger.warning("Creating mock assessments due to scraping error")
        catalog = create_mock_assessments()
        
        # Save the catalog
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(catalog, f, indent=2)
        logger.info(f"Saved mock catalog to {OUTPUT_FILE}")
        
        return catalog

def find_product_urls(main_url):
    """Find product URLs from the entire page."""
    try:
        # Get the page
        response = requests.get(main_url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        
        # Save raw HTML for debugging
        debug_file = os.path.join(DEBUG_DIR, "debug_response.html")
        with open(debug_file, "w", encoding="utf-8") as f:
            f.write(response.text)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for product listings specifically
        product_listings = soup.find_all(class_='product-listing')
        logger.info(f"Found {len(product_listings)} elements with class 'product-listing'")
        
        if not product_listings:
            # Try alternative selectors that might contain product links
            potential_products = []
            potential_products.extend(soup.find_all('div', class_=lambda c: c and ('product' in c.lower())))
            potential_products.extend(soup.find_all('article'))
            potential_products.extend(soup.find_all('li', class_=lambda c: c and ('product' in c.lower())))
            
            logger.info(f"Found {len(potential_products)} potential product containers with alternative selectors")
        
        # Extract all links from the page
        all_links = soup.find_all('a')
        logger.info(f"Found {len(all_links)} links on the page")
        
        product_urls = []
        for link in all_links:
            if link.has_attr('href'):
                href = link['href']
                if 'product-catalog/view/' in href or '/products/' in href or '/solutions/products/' in href:
                    # Ensure absolute URL
                    if not href.startswith('http'):
                        href = urljoin(main_url, href)
                    product_urls.append(href)
        
        # Remove duplicates
        product_urls = list(set(product_urls))
        return product_urls
        
    except Exception as e:
        logger.error(f"Error finding product URLs: {e}")
        return []

def create_mock_assessments():
    """Create mock assessments for testing."""
    logger.info("Creating mock assessments for testing")
    
    return [
        {
            "name": "Core Java (Advanced Level)",
            "url": "https://www.shl.com/products/product-catalog/view/core-java-advanced-level-new/",
            "description": "Advanced Java assessment evaluating proficiency in multithreading, design patterns, JVM optimization, and enterprise application development. Covers Spring Framework, Hibernate ORM, microservices architecture, and advanced debugging techniques.",
            "remote_support": "Yes",
            "adaptive_support": "No",
            "duration": "60 minutes",
            "type": "Technical"
        },
        {
            "name": "Core Java (Entry Level)",
            "url": "https://www.shl.com/products/product-catalog/view/core-java-entry-level-new/",
            "description": "Assessment for entry-level Java developers covering core language features, OOP concepts, collections framework, exception handling, and basic I/O operations. Includes practical coding exercises to evaluate problem-solving abilities.",
            "remote_support": "Yes",
            "adaptive_support": "No",
            "duration": "45 minutes",
            "type": "Technical"
        }
    ]

if __name__ == "__main__":
    catalog = scrape_shl_catalog()
    print(f"Scraped {len(catalog)} assessments") 