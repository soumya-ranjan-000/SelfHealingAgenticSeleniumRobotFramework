import os
import sys
import json
import logging
from datetime import datetime
from robot.libraries.BuiltIn import BuiltIn
from robot.api.deco import keyword
from bs4 import BeautifulSoup
import google.generativeai as genai
from dotenv import load_dotenv

# Try absolute import first (if libraries is in path), then relative
try:
    from libraries.LocatorUpdater import update_json_locator
except ImportError:
    try:
        from LocatorUpdater import update_json_locator
    except ImportError:
        # Fallback if neither works (should not happen if path set correctly)
         def update_json_locator(*args):
             logger.error("Could not import LocatorUpdater. Agentic update failed.")
             return False

# Load env vars from .env file if present
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG) # Catch all logs

# Ensure logs go to the console/terminal
# Check if we already have a StreamHandler to sys.__stdout__ to avoid duplicates
has_console_handler = any(
    isinstance(h, logging.StreamHandler) and h.stream == sys.__stdout__ 
    for h in logger.handlers
)

if not has_console_handler:
    console_handler = logging.StreamHandler(sys.__stdout__)
    console_handler.setFormatter(logging.Formatter('[PYTHON] %(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(console_handler)

logger.propagate = False # Prevent double logging if root logger is captured by Robot

class GenAIRescuer:
    """
    A Robot Framework library that uses GenAI (LLM) to heal failed Selenium locators.
    """
    
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found. Level 3 healing will fail.")
        else:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')

    @keyword
    def load_locator(self, page_name, element_name):
        """
        Reads the locator from locators/{page_name}.json
        Returns a dict: {'type': '...', 'value': '...'}
        """
        file_path = os.path.join("locators", f"{page_name}.json")
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            return data.get(element_name)
        except Exception as e:
            logger.error(f"Failed to load locator {element_name} from {page_name}.json: {e}")
            return None

    @keyword
    def get_webelement_with_healing(self, page_name, element_name):
        """
        Attempts to find a WebElement using the provided Page and Element name.
        Looks up the locator from JSON.
        If not found, engages GenAI to find a new locator, prioritizes them, 
        and validates against the live page.
        Returns the WebElement if found, otherwise raises ElementNotFoundException.
        """
        sl = BuiltIn().get_library_instance('SeleniumLibrary')
        driver = sl.driver
        
        # 1. Load Original Locator
        loc_data = self.load_locator(page_name, element_name)
        if not loc_data:
             raise Exception(f"Locator '{element_name}' not found in '{page_name}.json'")
        
        # Construct RF locator
        l_type = loc_data.get('type', 'xpath')
        l_value = loc_data.get('value')
        
        if l_type == 'id': rf_locator = f"id:{l_value}"
        elif l_type == 'name': rf_locator = f"name:{l_value}"
        elif l_type == 'css': rf_locator = f"css:{l_value}"
        elif l_type == 'xpath': rf_locator = f"xpath:{l_value}"
        elif l_type == 'link_text': rf_locator = f"link:{l_value}"
        elif l_type == 'partial_link_text': rf_locator = f"partial link:{l_value}"
        elif l_type == 'class_name': rf_locator = f"class:{l_value}"
        elif l_type == 'tag_name': rf_locator = f"tag:{l_value}"
        else: rf_locator = l_value # Default to original value if type is not strictly recognized by RF prefix

        # ... simple construction
        
        # 1. Try Original Locator
        try:
            locator_map = {
                'id': "id",
                'name': "name",
                'css': "css selector",
                'xpath': "xpath",
                'link_text': "link text",
                'partial_link_text': "partial link text",
                'class_name': "class name",
                'tag_name': "tag name",
            }
            selenium_by = locator_map.get(l_type)

            if selenium_by:
                init_found_el = driver.find_element(selenium_by, l_value)
            elif l_type == 'relative':
                # For 'relative' locators, it's generally better to use SeleniumLibrary's
                # own 'Find Element' keyword as it handles this strategy.
                # However, if direct driver interaction is required, this type
                # is not directly supported by driver.find_element().
                # This implementation assumes 'relative' might be a custom type
                # that needs specific handling or is an error in direct driver usage.
                # For now, we'll raise an error as it's not a standard WebDriver 'by' type.
                raise ValueError(f"Unsupported locator type for direct WebDriver: {l_type}. Consider using SeleniumLibrary's 'Find Element' keyword for 'relative' locators.")
            else:
                raise ValueError(f"Unsupported locator type: {l_type}")

            return init_found_el
        except Exception:
            logger.info(f"GenAIRescuer: Element Not Found Using Existing Locator '{rf_locator}' ({page_name}.{element_name} (Format: PageName.ElementName)). Engaging AI Healing...")

        # 2. Capture & Query
        html_content = self._get_minified_dom(driver.page_source)
        logger.info(f"GenAIRescuer: Captured HTML Content Successfully")
        # We pass the OLD value to the LLM so it knows what we are looking for
        candidates = self._query_llm(rf_locator, html_content)
        logger.info(f"GenAIRescuer: LLM returned Locators Successfully. Locators: {json.dumps(candidates, indent=2)}")
        if not candidates:
            raise Exception(f"GenAIRescuer: Failed to heal/generate new locator for '{rf_locator}'. No suggestions from LLM.")

        # 3. Sort Candidates/Locators
        # Priority: ID > Name > Link Text > Class Name > CSS > XPath
        priority_map = {
            'id': 10,
            'name': 20, 
            'link_text': 30,
            'partial_link_text': 35,
            'class_name': 40,
            'tag_name': 50,
            'css_selector': 60,
            'xpath': 70,
            'relative': 80
        }
        
        # Ensure candidates is a list of dicts
        if isinstance(candidates, str): 
            # Fallback if LLM returns a single string instead of JSON
             try:
                 candidates = json.loads(candidates)
             except:
                 candidates = [{'type': 'xpath', 'value': candidates}]
        if not isinstance(candidates, list):
             candidates = [candidates]

        def get_prio(c):
             t = c.get('type', 'xpath').lower()
             return priority_map.get(t, 100)

        candidates.sort(key=get_prio) # Lower number = Higher priority
        
        logger.info(f"GenAIRescuer: Testing {len(candidates)} candidates in priority order...")

        # 4. Validation Loop
        for cand in candidates:
            new_loc_type = cand.get('type', 'xpath')
            new_loc_val = cand.get('value')
            
            # Construct Robot Framework locator string
            if new_loc_type == 'id': rf_locator = f"id:{new_loc_val}"
            elif new_loc_type == 'name': rf_locator = f"name:{new_loc_val}"
            elif new_loc_type == 'css_selector': rf_locator = f"css:{new_loc_val}"
            elif new_loc_type == 'xpath' and not new_loc_val.startswith('//') and not new_loc_val.startswith('xpath:'): 
                rf_locator = f"xpath:{new_loc_val}"
            elif new_loc_type == 'link_text': rf_locator = f"link:{new_loc_val}"
            elif new_loc_type == 'partial_link_text': rf_locator = f"partial link:{new_loc_val}"
            elif new_loc_type == 'class_name': rf_locator = f"class:{new_loc_val}"
            elif new_loc_type == 'tag_name': rf_locator = f"tag:{new_loc_val}"
            else: rf_locator = new_loc_val
            
            logger.info(f"GenAIRescuer: Finding element with Locator: {rf_locator}")
            
            try:
                # Use SeleniumLibrary to find element (it handles delays/waiting better than raw driver if configured)
                # But here we want immediate check usually, so let's use raw driver for speed
                # or sl.find_element which is robust.
                # Let's use raw driver to catch exception immediately.
                if new_loc_type == 'id': found_el = driver.find_element("id", new_loc_val)
                elif new_loc_type == 'name': found_el = driver.find_element("name", new_loc_val)
                elif new_loc_type == 'link_text': found_el = driver.find_element("link text", new_loc_val)
                elif new_loc_type == 'partial_link_text': found_el = driver.find_element("partial link text", new_loc_val)
                elif new_loc_type == 'class_name': found_el = driver.find_element("class name", new_loc_val)
                elif new_loc_type == 'tag_name': found_el = driver.find_element("tag name", new_loc_val)
                elif new_loc_type == 'css_selector': found_el = driver.find_element("css selector", new_loc_val)
                elif new_loc_type == 'xpath': found_el = driver.find_element("xpath", new_loc_val)
                else: 
                     # Fallback to Robot's find_element for other types mixed in string
                     found_el = sl.find_element(rf_locator)

                # Log success with full metadata
                self._log_healing(page_name, element_name, l_type, l_value, new_loc_type, new_loc_val)
                
                # AGENTIC UPDATE: Check if we should update the Page Object Model JSON file
                auto_update = BuiltIn().get_variable_value('${AUTO_UPDATE_LOCATORS}')
                
                if auto_update == 'True' or auto_update is True:
                    logger.info(f"GenAIRescuer: Agentic Update - Modifying {page_name}.json file...")   
                    if update_json_locator(page_name, element_name, new_loc_type, new_loc_val):
                        logger.info(f"GenAIRescuer: Successfully updated Page Object '{page_name}.{element_name}' with new locator.")
                    else:
                        logger.error(f"GenAIRescuer: Failed to perform Agentic Update for '{page_name}.{element_name}'.")
                else:
                    logger.info(f"GenAIRescuer: Auto-update disabled. Skiping JSON update for '{page_name}.{element_name}'.")

                return found_el

            except Exception as e:
                logger.debug(f"GenAIRescuer: Element Not Found For The Locator: {rf_locator}. Error: {e}")
                continue

        # 5. Fail if all fail
        raise Exception(f"GenAIRescuer: Healing failed. Tried {len(candidates)} Locators but none matched the live page. Need Human Intervention.❤️")


    def _get_minified_dom(self, page_source):
        """
        Parses HTML, removes scripts/styles/comments to reduce context size.
        """
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Compare old vs new: Remove heavy tags
        for tag in soup(["script", "style", "noscript", "svg", "meta", "link"]):
            tag.decompose()
            
        # Get body (or relevant container)
        body = soup.body
        if body:
            return str(body)
        return str(soup)

    def _query_llm(self, old_locator, dom_snippet):
        """
        Sends the prompt to the LLM.
        """
        if not self.api_key:
            return None

        prompt = (
            f"You are an expert Selenium automation engineer. A previous locator failed: '{old_locator}'.\n"
            f"The current HTML structure is:\n"
            f"```html\n{dom_snippet[:15000]}\n```\n\n"
            f"Based on the failed locator and the current HTML, identify the target element. "
            f"Then, generate a list of alternative Selenium locators for that element. "
            f"Prioritize locators by their typical execution speed in Selenium, from fastest to slowest. "
            f"Include the following locator types if applicable, providing a robust value for each:\n"
            f"- 'id' (By.ID)\n"
            f"- 'name' (By.NAME)\n"
            f"- 'link_text' (By.LINK_TEXT)\n"
            f"- 'partial_link_text' (By.PARTIAL_LINK_TEXT)\n"
            f"- 'class_name' (By.CLASS_NAME)\n"
            f"- 'tag_name' (By.TAG_NAME)\n"
            f"- 'css_selector' (By.CSS_SELECTOR)\n"
            f"- 'xpath' (By.XPATH)\n"
            f"For 'relative' locators, describe the relationship (e.g., 'above', 'below', 'to_left_of') and the locator of the reference element.\n\n"
            f"Return a structured JSON array where each item is detailed. Example: [{{'type': 'id', 'value': 'submit-btn'}}, {{'type': 'xpath', 'value': '//button...'}}]. "
            f"Ensure the JSON is well-formed and contains only the array. Do not include any explanations or extra text."
        )

        import json

        import re
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()

            # Attempt to extract JSON array content
            match = re.search(r'```json\s*([\s\S]*?)\s*```', response_text)
            if match:
                json_string = match.group(1).strip()
            else:
                start_index = response_text.find('[')
                end_index = response_text.rfind(']')
                if start_index != -1 and end_index != -1 and end_index > start_index:
                    json_string = response_text[start_index : end_index + 1].strip()
                else:
                    json_string = response_text

            locators_json = json.loads(json_string)
            return locators_json
        except json.JSONDecodeError as e:
            logger.error(f"LLM response was not valid JSON. Attempted to parse: '{json_string}'. Full response: '{response_text}'. Error: {e}")
            return None
        except Exception as e:
            logger.error(f"LLM Query Failed: {e}")
            return None

    def _log_healing(self, page, name, old_type, old_value, new_type, new_value):
        """
        Logs the healing event to a JSON file for the Level 4 Feedback Loop.
        """
        log_file = "healing_log.json"
        timestamp = datetime.now().isoformat()
        
        entry = {
            "page": page,
            "name": name,
            "old_locator": {
                "type": old_type,
                "value": old_value
            },
            "new_locator": {
                "type": new_type,
                "value": new_value
            },
            "source": "GenAI", 
            "timestamp": timestamp
        }
        
        data = []
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r') as f:
                    data = json.load(f)
            except:
                pass
        
        # Filter out any existing entry for this specific element (Upsert strategy)
        data = [item for item in data if not (item.get('page') == page and item.get('name') == name)]
        
        data.append(entry)
        
        with open(log_file, 'w') as f:
            json.dump(data, f, indent=2)

