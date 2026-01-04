import os
import sys
import json
import logging
from datetime import datetime
from robot.libraries.BuiltIn import BuiltIn
from robot.api.deco import keyword
from bs4 import BeautifulSoup, Comment
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image, ImageDraw
import io
import base64

# Try absolute import first (if libraries is in path), then relative
try:
    from libraries.LocatorUpdater import update_json_locator
    from libraries.LocatorMapper import LocatorMapper
except ImportError:
    try:
        from LocatorUpdater import update_json_locator
        from LocatorMapper import LocatorMapper
    except ImportError:
        # Fallback if neither works (should not happen if path set correctly)
         def update_json_locator(*args):
             logger.error("Could not import LocatorUpdater. Agentic update failed.")
             return False
         class LocatorMapper:
             def __init__(self):
                 logger.error("Could not import LocatorMapper. Using fallback.")

# Import ContextTracker
# We rely on PYTHONPATH including the project root so 'libraries' is a package
try:
    from libraries.ContextTracker import context_tracker
except ImportError:
    # Fallback only if strictly necessary, but warn about singleton risk
    try:
        from ContextTracker import context_tracker
        logger.warning("Imported ContextTracker as top-level module. Singleton mismatch possible if Listener uses 'libraries.ContextTracker'.")
    except ImportError:
        class ContextTrackerStub:
            def get_context(self):
                return {}
        context_tracker = ContextTrackerStub()
        logger.warning("Could not import ContextTracker. Context awareness disabled.")

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
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Initialize centralized locator mapper
        self.mapper = LocatorMapper()

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
        elements = self.get_webelements_with_healing(page_name, element_name)
        if elements:
            return elements[0]
        
        # This part should technically be handled by get_webelements_with_healing raising an exception,
        # but for safety and clarity:
        raise Exception(f"GenAIRescuer: No element found for '{page_name}.{element_name}' after healing.")

    @keyword
    def get_webelements_with_healing(self, page_name, element_name):
        """
        Attempts to find multiple WebElements using the provided Page and Element name.
        Looks up the locator from JSON.
        If no elements found or not visible, engages GenAI to find a new locator, 
        prioritizes them, and validates against the live page.
        Returns a list of WebElements if found, otherwise raises an exception.
        """
        sl = BuiltIn().get_library_instance('SeleniumLibrary')
        driver = sl.driver
        
        # Fetch dynamic wait timeout from Robot Framework
        max_wait_str = BuiltIn().get_variable_value('${MAX_DYNAMIC_WAIT}', '60s')
        # Convert RF time string (e.g., '60s', '1 min') to seconds
        try:
            from robot.utils import timestr_to_secs
            max_wait = timestr_to_secs(max_wait_str)
        except:
            max_wait = 60
            
        # 1. Load Original Locator
        loc_data = self.load_locator(page_name, element_name)
        if not loc_data:
             raise Exception(f"Locator '{element_name}' not found in '{page_name}.json'")
        
        l_type = loc_data.get('type', 'xpath')
        l_value = loc_data.get('value')
        
        # Use centralized mapper to construct RF locator
        rf_locator = self.mapper.json_to_robot_framework(l_type, l_value)
        
        # 1. Try Original Locator with Visibility Wait
        try:
            logger.info(f"GenAIRescuer: Waiting up to {max_wait}s for '{rf_locator}' to be visible...")
            init_found_els = self.mapper.wait_for_all_visible(driver, l_type, l_value, timeout=max_wait)
            if init_found_els:
                # Scroll the first found element into view
                self.mapper.scroll_into_view(driver, init_found_els[0])
                
                # --- NEW: Save snapshot for Differential Healing ---
                # OPTIMIZATION: Only save if we don't have a snapshot yet.
                if not self._snapshot_exists(page_name, element_name):
                    self._save_dom_snapshot(page_name, element_name, init_found_els[0])
                
                return init_found_els
            logger.info(f"GenAIRescuer: No visible elements found using existing locator '{rf_locator}' ({page_name}.{element_name}). Engaging AI Healing...")
        except Exception as e:
            logger.info(f"GenAIRescuer: Visibility wait failed or error using existing locator '{rf_locator}': {e}. Engaging AI Healing...")

        # 2. Capture & Query
        html_content = self._get_minified_dom(driver.page_source)
        
        # --- NEW: Load snapshot for Differential Healing ---
        last_known_html = self._load_dom_snapshot(page_name, element_name)
        
        # --- NEW: Vision / Screenshot Logic ---
        last_known_image = None
        current_image = None
        
        enable_vision = BuiltIn().get_variable_value('${ENABLE_VISION_HEALING}', 'False')
        if str(enable_vision).lower() == 'true':
            try:
                # 1. Capture Current Broken State
                png_data = driver.get_screenshot_as_png()
                current_image = Image.open(io.BytesIO(png_data))
                
                # 2. Load Last Known Good State (if available)
                snapshot_dir = os.path.join("locators", "dom_snapshots", page_name)
                success_img_path = os.path.join(snapshot_dir, f"{element_name}_success.png")
                
                if os.path.exists(success_img_path):
                    try:
                        last_known_image = Image.open(success_img_path)
                        logger.info(f"GenAIRescuer: Loaded reference screenshot from {success_img_path}")
                    except Exception as img_err:
                         logger.warning(f"GenAIRescuer: Failed to load reference screenshot: {img_err}")
                
                logger.info("GenAIRescuer: Prepared images for Multi-Modal analysis.")
            except Exception as e:
                logger.warning(f"GenAIRescuer: Vision capture failed: {e}")

        logger.info(f"GenAIRescuer: Captured HTML Content Successfully")
        candidates = self._query_llm(rf_locator, html_content, last_known_html, last_known_image, current_image)
        logger.info(f"GenAIRescuer: LLM returned Locators Successfully. Locators: {json.dumps(candidates, indent=2)}")
        if not candidates:
            raise Exception(f"GenAIRescuer: Failed to heal/generate new locator for '{rf_locator}'. No suggestions from LLM.")

        # 3. Sort Candidates/Locators
        if isinstance(candidates, str): 
             try:
                 candidates = json.loads(candidates)
             except:
                 candidates = [{'type': 'xpath', 'value': candidates}]
        if not isinstance(candidates, list):
             candidates = [candidates]

        candidates = self.mapper.sort_locator_candidates(candidates)
        
        logger.info(f"GenAIRescuer: Testing {len(candidates)} candidates in priority order...")

        # 4. Validation Loop
        for cand in candidates:
            new_loc_type = cand.get('type', 'xpath')
            new_loc_val = cand.get('value')
            
            normalized_type = self.mapper.normalize_genai_type(new_loc_type)
            rf_locator = self.mapper.json_to_robot_framework(normalized_type, new_loc_val)
            
            logger.info(f"GenAIRescuer: Finding/Waiting for visible elements with Locator: {rf_locator}")
            
            try:
                # For healing candidates, we use a smaller wait per candidate to avoid hanging too long
                # but long enough to see if it's there. Let's use 5s or a fraction of max_wait.
                heal_wait = min(5, 10)
                found_els = self.mapper.wait_for_all_visible(driver, normalized_type, new_loc_val, timeout=heal_wait)
                if not found_els:
                    continue

                # Scroll into view
                self.mapper.scroll_into_view(driver, found_els[0])

                # Log success
                self._log_healing(page_name, element_name, l_type, l_value, normalized_type, new_loc_val)

                # --- NEW: Save snapshot for Differential Healing ---
                self._save_dom_snapshot(page_name, element_name, found_els[0])
                
                # AGENTIC UPDATE
                auto_update = BuiltIn().get_variable_value('${AUTO_UPDATE_LOCATORS}')
                if auto_update == 'True' or auto_update is True:
                    logger.info(f"GenAIRescuer: Agentic Update - Modifying {page_name}.json file...")   
                    if update_json_locator(page_name, element_name, normalized_type, new_loc_val):
                        logger.info(f"GenAIRescuer: Successfully updated Page Object '{page_name}.{element_name}' with new locator.")
                    else:
                        logger.error(f"GenAIRescuer: Failed to perform Agentic Update for '{page_name}.{element_name}'.")

                return found_els

            except Exception as e:
                logger.debug(f"GenAIRescuer: Error finding/waiting for elements for locator {rf_locator}: {e}")
                continue

        # 5. Fail if all fail
        raise Exception(f"GenAIRescuer: Healing failed. Tried {len(candidates)} Locators but none matched or became visible on the live page. Need Human Intervention.❤️")


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

    def _query_llm(self, old_locator, dom_snippet, last_known_good=None, last_known_image=None, current_image=None):
        """
        Sends the prompt to the LLM (Text + Optional Images).
        """
        if not self.api_key:
            return None

        snapshot_context = ""
        if last_known_good:
            snapshot_context = f"\nIn the previous version, the element looked like this:\n```html\n{last_known_good}\n```\nAnalyze the 'Last Known Good' HTML to understand the element's role, behavior, and visual appearance.\n"

        image_context = ""
        if last_known_image and current_image:
            image_context = (
                "\nI have provided two images:\n"
                "1. **Reference Image**: Shows the valid element from a previous successful run. The target element is **highlighted with a RED or BLACK outline**.\n"
                "2. **Current Image**: Shows the current page state where the locator failed (no highlight).\n"
                "Compare these images to understand how the page visual structure has changed.\n"
            )
        elif current_image:
             image_context = "\nI have provided a screenshot of the current page state where the locator failed.\n"

        # --- Execution Context ---
        try:
             ctx = context_tracker.get_context()
             test_name = ctx.get('test_name', 'Unknown')
             last_kws = ", ".join(ctx.get('last_keywords', []))
             last_steps = ", ".join(ctx.get('last_steps', []))
             
             exec_context = (
                 f"\n**Execution Context**:\n"
                 f"- Test Name: '{test_name}'\n"
                 f"- Last Executed Keywords: [{last_kws}]\n"
                 f"- Last Executed Steps: [{last_steps}]\n"
                 f"Use this context to infer the user's intent and current state in the flow.\n"
             )
        except Exception as e:
             logger.warning(f"GenAIRescuer: Failed to get execution context: {e}")
             exec_context = "" 


        prompt = (
            f"You are an expert Selenium automation engineer and Visual QA analyst. A previous locator failed: '{old_locator}'.\n"
            f"Your task is to identify the CORRECT element in the new DOM by cross-referencing structural hierarchy and visual position.\n"
            f"{snapshot_context}"
            f"{image_context}"
            f"{exec_context}"
            f"The current HTML structure (Current Broken DOM) is:\n"
            f"```html\n{dom_snippet[:15000]}\n```\n\n"
            f"**CRITICAL INSTRUCTIONS FOR LOCATING THE ELEMENT:**\n"
            f"1. **STRICT PARENT CHECK**: The 'Last Known Good' HTML provided (if any) contains the target element AND its direct parents (ancestors). "
            f"Any candidate element you find in the 'Current Broken DOM' MUST be nested inside a similar parent hierarchy. "
            f"Do NOT select an element if it has the same attributes but resides in a different container (e.g., a similar button in a different modal or footer). "
            f"Use the parent structure to disambiguate.\n"
            f"2. **VISUAL VERIFICATION**: Analyze the 'Reference Image' (if provided). The target element is HIGHLIGHTED with a box. "
            f"Look at the 'Current Image' (if provided). Does the candidate element you found in the HTML appear in the SAME relative visual location as the highlighted box? "
            f"If the structural match implies an element in the top-right, but the highlight was in the bottom-left, DISCARD that candidate. "
            f"Only return locators for the element that matches BOTH the structural parent hierarchy AND the visual screen position.\n\n"
            f"Generate a list of alternative Selenium locators for the verified element. "
            f"Prioritize locators by their typical execution speed in Selenium, from fastest to slowest. "
            f"Include the following locator types if applicable, providing a robust value for each:\n"
            f"- 'id' (By.ID)\n"
            f"- 'link_text' (By.LINK_TEXT)\n"
            f"- 'partial_link_text' (By.PARTIAL_LINK_TEXT)\n"
            f"- 'class_name' (By.CLASS_NAME)\n"
            f"- 'tag_name' (By.TAG_NAME)\n"
            f"- 'css_selector' (By.CSS_SELECTOR)\n"
            f"- 'xpath' (By.XPATH)\n"
            f"- 'name' (By.NAME)\n"
            f"For 'relative' locators, describe the relationship (e.g., 'above', 'below', 'to_left_of') and the locator of the reference element.\n\n"
            f"Return a structured JSON array where each item is detailed. Example: [{{'type': 'id', 'value': 'submit-btn'}}, {{'type': 'xpath', 'value': '//button...'}}]. "
            f"Ensure the JSON is well-formed and contains only the array."
        )
        logger.info(f"Gemini prompt: {prompt}")
        
        import re
        try:
            inputs = [prompt]
            if last_known_image:
                 inputs.append(last_known_image)
            if current_image:
                 inputs.append(current_image)
            logger.info(f"Calling gemini now....")    
            response = self.model.generate_content(inputs)
            response_text = response.text.strip()
            logger.info(f"Gemini response: {response_text}")

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

    def _save_dom_snapshot(self, page_name, element_name, element):
        """
        Saves a minified DOM snippet including 3 levels of ancestry context 
        to locators/snapshots/{page_name}/{element_name}.html
        """
        try:
            # JavaScript to create a 'Vertical Slice' of the DOM (Target + 3 Parents)
            # This isolates the structural path without including thousands of sibling nodes.
            js_script = """
                var el = arguments[0];
                var depth = 3;
                var current = el.cloneNode(true); // Deep clone the target to keep its inner text/structure
                
                var ptr = el.parentElement;
                for (var i = 0; i < depth && ptr; i++) {
                    var wrapper = ptr.cloneNode(false); // Shallow clone parent (attributes only, no siblings)
                    wrapper.appendChild(current);
                    current = wrapper;
                    ptr = ptr.parentElement;
                }
                return current.outerHTML;
            """
            
            # reliable way to get driver from the element itself
            driver = element.parent 
            context_html = driver.execute_script(js_script, element)
            
            minified_html = self._minify_html_snippet(context_html)
            
            snapshot_dir = os.path.join("locators", "dom_snapshots", page_name)
            os.makedirs(snapshot_dir, exist_ok=True)
            
            file_path = os.path.join(snapshot_dir, f"{element_name}.html")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(minified_html)
            
            # --- Visual Snapshot with Highlight ---
            try:
                # 1. Highlight Element
                original_border = driver.execute_script("return arguments[0].style.border", element)
                driver.execute_script("arguments[0].style.border='5px solid red'", element)
                
                # 2. Capture Screenshot
                screenshot_path = os.path.join(snapshot_dir, f"{element_name}_success.png")
                driver.save_screenshot(screenshot_path)
                
                # 3. Remove Highlight
                driver.execute_script(f"arguments[0].style.border='{original_border}'", element)
                
                logger.debug(f"GenAIRescuer: Saved highlighted success screenshot to {screenshot_path}")
            except Exception as viz_err:
                 logger.warning(f"GenAIRescuer: Failed to save visual snapshot: {viz_err}")

            logger.debug(f"GenAIRescuer: Saved DOM snapshot (w/ 3 parents) and metadata for {page_name}.{element_name}")
        except Exception as e:
            logger.warning(f"GenAIRescuer: Failed to save DOM snapshot for {page_name}.{element_name}: {e}")

    def _load_dom_snapshot(self, page_name, element_name):
        """
        Loads the minified DOM snapshot for an element if it exists.
        Returns: html_content
        """
        dir_path = os.path.join("locators", "dom_snapshots", page_name)
        html_path = os.path.join(dir_path, f"{element_name}.html")
        
        html_content = None

        if os.path.exists(html_path):
            try:
                with open(html_path, "r", encoding="utf-8") as f:
                    html_content = f.read()
            except Exception as e:
                logger.warning(f"GenAIRescuer: Failed to load DOM snapshot for {page_name}.{element_name}: {e}")
        
        return html_content

    def _minify_html_snippet(self, html):
        """
        Minifies a small HTML snippet by removing comments and extra whitespace.
        """
        if not html:
            return ""
        soup = BeautifulSoup(html, 'html.parser')
        # Remove comments
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
        # Get string and minify
        minified = str(soup).replace('\n', ' ').replace('\r', ' ')
        import re
        minified = re.sub(r'\s+', ' ', minified).strip()
        return minified

    def _snapshot_exists(self, page_name, element_name):
        """
        Checks if a DOM snapshot already exists for the given element.
        """
        dir_path = os.path.join("locators", "dom_snapshots", page_name)
        # We check for the HTML file as the primary indicator
        html_path = os.path.join(dir_path, f"{element_name}.html")
        return os.path.exists(html_path)

