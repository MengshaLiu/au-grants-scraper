import requests
from bs4 import BeautifulSoup
import time
import random
import logging
import json

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Scraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        self.session = requests.Session()
        
    def get_soup(self, url, params=None):
        """Make a request to the specified URL and return the BeautifulSoup object."""
        try:
            response = self.session.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    def get_total_grant_list_pages(self,url):
        """Extract the total number of pages from the pagination."""
        logger.info(f"Scraping grant list page: {url}")
        soup = self.get_soup(url)
        pagination = soup.find('ul', class_='pagination')
        if not pagination:
            return 1
        # Find all page number links
        page_links = pagination.find_all('a')
        
        # Extract numbers from the links
        page_numbers = []
        for link in page_links:
            text = link.get_text(strip=True)
            if text.isdigit():
                page_numbers.append(int(text))
        
        # Return the highest page number found
        return max(page_numbers) if page_numbers else 1
    
    def extract_grant_link_from_page(self, url, params):
        """Extract grant hyperlink from a page."""
        soup = self.get_soup(url, params=params)
        if not soup:
            logger.error("Failed to fetch the grant links")
            return None
        
        href_list = []
        try:
            # Find the dive containing grant list
            grant_item_div = soup.find_all('div', class_='boxEQH')
            for div in grant_item_div:
                # Extract specific grant go_id from each grant div
                href_div = div.find('div', class_= 'list-desc-inner')
                href=href_div.find('a', class_='u')['href'] 
                href_list.append(href)
                    
        except Exception as e:
            logger.error(f"Error extracting grants links: {e}")
            
        return href_list
    
    def extract_grant_info_from_grant_page(self, href_list):
        """Extract grant info from each grant page"""
        grants=[]
        try: 
            # Extract grant info for grants listed in the page
            for href in href_list:
                grant={}
                logger.info(f"Scraping page: https://www.grants.gov.au{href}")
                soup=self.get_soup(f"https://www.grants.gov.au{href}")
                if not soup:
                    logger.error(f"Failed to fetch the grant page for: https://www.grants.gov.au{href}")
                    return None
        
                div = soup.find_all('div', class_='list-desc')
                for title in div:
                    title_name = title.find('span').get_text(strip=True).replace(':','')
                    title_value = title.find('div', class_='list-desc-inner').get_text(strip=True)
                    grant[title_name] = title_value

                grants.append(grant)

        except Exception as e:
            logger.error(f"Error extracting grants info from page: {e}")
        return grants

    def scrape_all_pages(self,base_url):
        total_grants=[]
        #Extract grant info for the first page
        href_list = self.extract_grant_link_from_page(base_url,params=None)
        if not href_list:
                logger.error(f"Failed to fetch page list for the page: 1")
            
        grants_in_page = self.extract_grant_info_from_grant_page(href_list)
        total_grants.extend(grants_in_page)
        # Get total number of pages
        total_pages = self.get_total_grant_list_pages(base_url)
        logger.info(f"Total pages detected: {total_pages}")

        # Exract grant info for remaining pages
        for page in range(2, total_pages+1):
            logger.info(f"Scraping page {page}")
            
        # Add a delay to be respectful to the server
            time.sleep(random.uniform(1, 3))
            
            params = {'page': page}
            href_list = self.extract_grant_link_from_page(base_url,params=params)
    
            if not href_list:
                logger.error(f"Failed to fetch page list for {page}")
                continue
            
            grants_in_page = self.extract_grant_info_from_grant_page(href_list)
            logger.info(f"Successfully Extracted {len(grants_in_page)} grants from page: {page}")
            total_grants.extend(grants_in_page)

        grants_length = len(total_grants) 
        logger.info(f"Successfully Extracted {grants_length} grants from {total_pages} pages")
        return  total_grants           

    def write_to_json(self,data,file_name):
        "Save grants data to .json file"
        #Cehck if the grants data is empty
        if not data:
            logger.warning("No grants to save")
            return False
        
        try: 
            with open(file_name, "w") as final:
                json.dump(data, final)
                logger.info("Successfully saved data to JSON")
            return True
        except Exception as e:
            logger.error (f"Error saving grants data to JSON: {e}")
            return False
        
if __name__ == "__main__":
    grants_scraper = Scraper()
    grant_list_url = "https://www.grants.gov.au/Go/List"
    total_grants = grants_scraper.scrape_all_pages(grant_list_url)
    grants_scraper.write_to_json(total_grants, "grants_info.json")
   