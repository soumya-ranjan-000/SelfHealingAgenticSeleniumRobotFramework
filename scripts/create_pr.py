import os
import sys
import time
import argparse
import subprocess
from datetime import datetime
from git import Repo, exc

# Ensure libraries path is in sys.path to import LocatorUpdater
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'libraries'))
import LocatorUpdater

REPO_PATH = "."

def is_gh_cli_installed():
    """Check if the GitHub CLI (gh) is installed."""
    try:
        subprocess.run(["gh", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def run_git_workflow(suite_name="CustomSuite"):
    print("Starting Automated PR Workflow...")
    
    # 1. Apply Updates
    modified_files = LocatorUpdater.update_locators()
    
    if not modified_files:
        print("No locators were updated. Exiting git workflow.")
        return

    # 2. Git Operations
    try:
        repo = Repo(REPO_PATH)
    except exc.InvalidGitRepositoryError:
        print(f"Error: {os.path.abspath(REPO_PATH)} is not a valid git repository.")
        print("Please initialize git: git init")
        return

    if not repo.is_dirty(untracked_files=True):
        print("No git changes detected (unexpected, since files were modified). Exiting.")
        return

    # Sanitize suite name for branch name
    sanitized_suite_name = "".join(c for c in suite_name if c.isalnum() or c in ('-', '_'))
    if not sanitized_suite_name:
        sanitized_suite_name = "GenericSuite"
        
    branch_name = f"{sanitized_suite_name}-healing-{int(time.time())}"
    print(f"Creating branch: {branch_name}")
    
    try:
        current = repo.active_branch
        new_branch = repo.create_head(branch_name)
        new_branch.checkout()
        
        print(f"Staging {len(modified_files)} files...")
        repo.index.add(modified_files)
        
        commit_message = f"fix(healing): Auto-heal locators for {suite_name}"
        repo.index.commit(commit_message)
        
        print(f"Committed changes to {branch_name} with message: '{commit_message}'")
        
        # 3. Push and PR
        print("\n--- Push & PR ---")
        
        remote_name = "origin"
        if remote_name in repo.remotes:
            print(f"Pushing to {remote_name}...")
            try:
                repo.remote(remote_name).push(branch_name)
                print("Push successful.")
                
                if is_gh_cli_installed():
                    print("Attempting to create PR via GitHub CLI...")
                    pr_title = f"Auto-fix Locators for {suite_name}"
                    pr_body = "This PR was automatically created by the self-healing agent.\nIt contains updated locators found during test execution."
                    subprocess.run([
                        "gh", "pr", "create", 
                        "--title", pr_title, 
                        "--body", pr_body, 
                        "--head", branch_name
                    ], check=True)
                    print("PR Created successfully.")
                else:
                    print("GitHub CLI (gh) not found. Please create a PR manually.")
                    # Construct a generic PR URL check (assuming GitHub)
                    # We'd need the remote URL to be accurate, but just a reminder is good enough.
                    print(f"Create PR for branch '{branch_name}'.")
            except Exception as e:
                print(f"Failed to push to remote: {e}")
        else:
            print(f"Remote '{remote_name}' not found. Skipping push.")
            
    except Exception as e:
        print(f"An error occurred during git operations: {e}")
    finally:
        # Return to original branch
        print(f"Switching back to {current.name}...")
        current.checkout()
        print("Workflow finished.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auto PR Creation Script")
    parser.add_argument("--suite", type=str, default="UnknownSuite", help="Name of the Test Suite")
    args = parser.parse_args()
    
    run_git_workflow(suite_name=args.suite)
