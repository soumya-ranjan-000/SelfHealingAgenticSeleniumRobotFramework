import json
import os
from datetime import datetime
try:
    from git import Repo
except ImportError:
    Repo = None

HEALING_LOG = "healing_log.json"
LOCATORS_DIR = "locators"

def update_json_locator(page_name, element_name, new_locator_type, new_locator_value):
    """
    Updates a single locator in the JSON file. 
    Can be called by GenAIRescuer for live updates.
    """
    json_file_path = os.path.join(LOCATORS_DIR, f"{page_name}.json")
    
    if not os.path.exists(json_file_path):
        print(f"Locator file {json_file_path} not found. Skipping.")
        return False
        
    try:
        # Read existing
        with open(json_file_path, 'r') as f:
            data = json.load(f)
        
        # Update
        if element_name in data:
            print(f"Updating {page_name}.{element_name} -> {new_locator_type}: {new_locator_value}")
            data[element_name]['type'] = new_locator_type # Ensure we update the 'type' field
            data[element_name]['value'] = new_locator_value # Ensure we update the 'value' field
            
            # Write back
            with open(json_file_path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        else:
                print(f"Element {element_name} not found in {json_file_path}. Skipping.")
                return False

    except Exception as e:
        print(f"Error updating file {json_file_path}: {e}")
        return False

def update_locators():
    if not os.path.exists(HEALING_LOG):
        print(f"No healing log found at {HEALING_LOG}. Nothing to update.")
        return

    try:
        with open(HEALING_LOG, 'r') as f:
            changes = json.load(f)
    except Exception as e:
        print(f"Error reading healing log: {e}")
        return

    if not changes:
        print("Healing log is empty.")
        return

    print(f"Found {len(changes)} locators to update.")

    modified_files = []

    for change in changes:
        page_name = change.get('page')
        element_name = change.get('name')
        new_loc = change.get('new_locator')['value'] # Extract value from object
        
        if not page_name or not element_name or not new_loc:
            print(f"Skipping invalid entry: {change}")
            continue
        
        if update_json_locator(page_name, element_name, new_loc):
             json_file_path = os.path.join(LOCATORS_DIR, f"{page_name}.json")
             if json_file_path not in modified_files:
                modified_files.append(json_file_path)

    # if modified_files:
    #     create_pr(modified_files)
    
    print("Locator update complete.")

def create_pr(files):
    if Repo is None:
        print("GitPython not installed. Skipping Git operations.")
        return

    try:
        repo = Repo(".")
        # if repo.is_dirty(untracked_files=True):
        #      print("Repo has uncommitted changes. Proceeding carefully...")
        
        branch_name = f"healing/update-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        current_branch = repo.active_branch
        
        print(f"Creating new branch: {branch_name}")
        new_branch = repo.create_head(branch_name)
        new_branch.checkout()
        
        repo.index.add(files)
        repo.index.commit("chore(healing): Auto-update POM locators via GenAI")
        
        print("Pushing to remote...")
        try:
            repo.remotes.origin.push(refspec=f'{branch_name}:{branch_name}')
            print(f"Changes pushed to {branch_name}")
            print(f"Please open a PR for branch '{branch_name}' manually.")
        except Exception as e:
             print(f"Failed to push: {e}")

        # Switch back
        current_branch.checkout()

    except Exception as e:
        print(f"Git operation failed: {e}")

if __name__ == "__main__":
    update_locators()
