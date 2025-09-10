from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

def scrape_data(url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    try:
        service = Service(ChromeDriverManager().install())
        with webdriver.Chrome(service=service, options=options) as driver:
            driver.get(url)
            # Wait for body to be present
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            content = []
            
            # Get meta description
            meta_desc = driver.find_elements(By.XPATH, "//meta[@name='description']")
            if meta_desc:
                content.append(f"META_DESCRIPTION: {meta_desc[0].get_attribute('content')}")
            
            # Get title
            title = driver.title
            if title:
                content.append(f"TITLE: {title}")
            
            # Get main content elements
            main_content_selectors = [
                "main", "article", "#content", ".content",
                "[role='main']", "#main-content"
            ]
            
            main_content = None
            for selector in main_content_selectors:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    main_content = elements[0]
                    break
            
            # If no main content container found, use body
            if not main_content:
                main_content = driver.find_element(By.TAG_NAME, "body")
            
            # Get text from important elements within main content
            important_elements = main_content.find_elements(
                By.CSS_SELECTOR,
                'h1, h2, h3, h4, p, li, table, dl, blockquote'
            )
            
            for element in important_elements:
                text = element.text.strip()
                if text:
                    tag_name = element.tag_name.upper()
                    content.append(f"{tag_name}: {text}")
            
            return "\n".join(content) if content else "No content could be extracted"
            
    except TimeoutException:
        return "Timeout while loading the page"
    except Exception as e:
        return f"Error scraping the page: {str(e)}"
