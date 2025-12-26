"""
LocatorMapper - Centralized Locator Format Conversion Utility

This module provides a unified interface for converting between different locator formats:
- JSON Page Object format (type, value)
- Selenium WebDriver By strategies
- Robot Framework locator strings
- GenAI response formats

This eliminates duplicate mapping logic across the codebase.
"""

import logging

logger = logging.getLogger(__name__)


class LocatorMapper:
    """
    Centralized utility for converting between different locator format conventions.
    """
    
    # JSON type → Robot Framework prefix mapping
    JSON_TO_RF_PREFIX = {
        'id': 'id',
        'name': 'name',
        'css': 'css',
        'xpath': 'xpath',
        'link_text': 'link',
        'partial_link_text': 'partial link',
        'class_name': 'class',
        'tag_name': 'tag'
    }
    
    # JSON type → Selenium By strategy mapping
    JSON_TO_SELENIUM_BY = {
        'id': 'id',
        'name': 'name',
        'css': 'css selector',
        'xpath': 'xpath',
        'link_text': 'link text',
        'partial_link_text': 'partial link text',
        'class_name': 'class name',
        'tag_name': 'tag name'
    }
    
    # GenAI response type → JSON standard type (normalization)
    # This handles variations in naming conventions from different sources
    GENAI_TO_JSON_TYPE = {
        # Standard types (pass-through)
        'id': 'id',
        'name': 'name',
        'xpath': 'xpath',
        'link_text': 'link_text',
        'partial_link_text': 'partial_link_text',
        'class_name': 'class_name',
        'tag_name': 'tag_name',
        
        # Variations that need normalization
        'css_selector': 'css',
        'css': 'css',
        'class': 'class_name',
        'tag': 'tag_name',
        'link': 'link_text',
        'partial_link': 'partial_link_text',
        
        # Special types
        'relative': 'relative'
    }
    
    # Priority map for sorting locator candidates
    # Lower number = Higher priority (faster/more reliable)
    LOCATOR_PRIORITY = {
        'id': 10,
        'name': 20,
        'link_text': 30,
        'partial_link_text': 35,
        'class_name': 40,
        'tag_name': 50,
        'css': 60,
        'xpath': 70,
        'relative': 80
    }
    
    def normalize_genai_type(self, genai_type):
        """
        Normalize GenAI response locator type to standard JSON format.
        
        Args:
            genai_type (str): Locator type from GenAI response (e.g., 'css_selector', 'class')
            
        Returns:
            str: Normalized type in JSON format (e.g., 'css', 'class_name')
        """
        normalized = self.GENAI_TO_JSON_TYPE.get(genai_type.lower(), genai_type)
        if normalized == genai_type and genai_type not in self.JSON_TO_RF_PREFIX:
            logger.warning(f"Unknown locator type '{genai_type}'. Using as-is.")
        return normalized
    
    def json_to_robot_framework(self, loc_type, loc_value):
        """
        Convert JSON locator format to Robot Framework locator string.
        
        Args:
            loc_type (str): Locator type from JSON (e.g., 'id', 'css', 'xpath')
            loc_value (str): Locator value
            
        Returns:
            str: Robot Framework locator string (e.g., 'id:submit-btn', 'css:.button')
        """
        prefix = self.JSON_TO_RF_PREFIX.get(loc_type)
        
        if prefix:
            return f"{prefix}:{loc_value}"
        else:
            # For unrecognized types, return the value as-is
            logger.warning(f"Unknown locator type '{loc_type}' for RF conversion. Returning value as-is.")
            return loc_value
    
    def wait_for_page_to_load(self, driver, timeout=10):
        """
        Wait for the browser document.readyState to be 'complete'.
        
        Args:
            driver: Selenium WebDriver instance
            timeout (int): Maximum time to wait in seconds
        """
        import time
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                state = driver.execute_script("return document.readyState")
                if state == "complete":
                    return True
            except Exception:
                pass
            time.sleep(0.5)
        logger.warning(f"Page did not reach 'complete' state within {timeout}s. Proceeding anyway.")
        return False

    def wait_for_visibility(self, driver, loc_type, loc_value, timeout=60):
        """
        Wait for an element to be visible on the page.
        
        Args:
            driver: Selenium WebDriver instance
            loc_type (str): Locator type (JSON format)
            loc_value (str): Locator value
            timeout (int): Timeout in seconds
            
        Returns:
            WebElement: The visible element
            
        Raises:
            TimeoutException: If element not visible within timeout
        """
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        selenium_by = self.json_to_selenium_by(loc_type)
        if not selenium_by:
            raise ValueError(f"Unsupported locator type for visibility wait: {loc_type}")
            
        wait = WebDriverWait(driver, timeout)
        return wait.until(EC.visibility_of_element_located((selenium_by, loc_value)))

    def wait_for_all_visible(self, driver, loc_type, loc_value, timeout=60):
        """
        Wait for all elements matching locator to be visible.
        """
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support   import expected_conditions as EC
        
        selenium_by = self.json_to_selenium_by(loc_type)
        if not selenium_by:
            raise ValueError(f"Unsupported locator type for visibility wait: {loc_type}")
            
        wait = WebDriverWait(driver, timeout)
        return wait.until(EC.visibility_of_all_elements_located((selenium_by, loc_value)))

    def scroll_into_view(self, driver, element):
        """
        Scroll the element into the viewport using JavaScript.
        """
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)

    def json_to_selenium_by(self, loc_type):
        """
        Convert JSON locator type to Selenium WebDriver By strategy.
        
        Args:
            loc_type (str): Locator type from JSON (e.g., 'id', 'css', 'xpath')
            
        Returns:
            str: Selenium By strategy (e.g., 'id', 'css selector', 'xpath')
            None: If type is not supported by Selenium WebDriver
        """
        selenium_by = self.JSON_TO_SELENIUM_BY.get(loc_type)
        
        if not selenium_by:
            logger.warning(f"Locator type '{loc_type}' not supported for Selenium WebDriver.")
        
        return selenium_by
    
    def find_element_by_locator(self, driver, loc_type, loc_value):
        """
        Find a WebElement using the provided locator type and value.
        
        Args:
            driver: Selenium WebDriver instance
            loc_type (str): Locator type in JSON format (e.g., 'id', 'css', 'xpath')
            loc_value (str): Locator value
            
        Returns:
            WebElement: The found element
            
        Raises:
            ValueError: If locator type is not supported
            NoSuchElementException: If element is not found
        """
        # Wait for page load before searching
        self.wait_for_page_to_load(driver)
        
        selenium_by = self.json_to_selenium_by(loc_type)
        
        if not selenium_by:
            if loc_type == 'relative':
                raise ValueError(
                    f"Unsupported locator type for direct WebDriver: {loc_type}. "
                    "Consider using SeleniumLibrary's 'Find Element' keyword for 'relative' locators."
                )
            else:
                raise ValueError(f"Unsupported locator type: {loc_type}")
        
        return driver.find_element(selenium_by, loc_value)

    def find_elements_by_locator(self, driver, loc_type, loc_value):
        """
        Find multiple WebElements using the provided locator type and value.
        
        Args:
            driver: Selenium WebDriver instance
            loc_type (str): Locator type in JSON format (e.g., 'id', 'css', 'xpath')
            loc_value (str): Locator value
            
        Returns:
            list[WebElement]: The found elements (empty list if none found)
            
        Raises:
            ValueError: If locator type is not supported
        """
        # Wait for page load before searching
        self.wait_for_page_to_load(driver)
        
        selenium_by = self.json_to_selenium_by(loc_type)
        
        if not selenium_by:
            if loc_type == 'relative':
                raise ValueError(f"Unsupported locator type for direct WebDriver: {loc_type}")
            else:
                raise ValueError(f"Unsupported locator type: {loc_type}")
        
        return driver.find_elements(selenium_by, loc_value)
    
    def get_locator_priority(self, loc_type):
        """
        Get the priority score for a locator type.
        Lower score = Higher priority (faster/more reliable).
        
        Args:
            loc_type (str): Locator type in JSON format
            
        Returns:
            int: Priority score (default 100 for unknown types)
        """
        return self.LOCATOR_PRIORITY.get(loc_type, 100)
    
    def sort_locator_candidates(self, candidates):
        """
        Sort locator candidates by priority (fastest/most reliable first).
        
        Args:
            candidates (list): List of dicts with 'type' and 'value' keys
            
        Returns:
            list: Sorted list of candidates
        """
        def get_priority(candidate):
            loc_type = candidate.get('type', 'xpath').lower()
            normalized_type = self.normalize_genai_type(loc_type)
            return self.get_locator_priority(normalized_type)
        
        return sorted(candidates, key=get_priority)
