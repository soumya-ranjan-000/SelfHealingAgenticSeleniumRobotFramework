import os
import sys
import subprocess
import xml.etree.ElementTree as ET

# Configuration
TEST_COMMAND = ["robot", "--outputdir", "results", "tests"]
OUTPUT_XML = os.path.join("results", "output.xml")
HEALING_LOG = "healing_log.json"
CREATE_PR_SCRIPT = os.path.join(os.path.dirname(__file__), "create_pr.py")

def run_tests():
    print(f"Running tests with command: {' '.join(TEST_COMMAND)}")
    # Run tests; don't check return code as tests might fail (which is fine)
    subprocess.run(TEST_COMMAND)

def get_suite_name_from_xml(xml_path):
    try:
        if not os.path.exists(xml_path):
            return "UnknownSuite"
        
        tree = ET.parse(xml_path)
        root = tree.getroot()
        # The top-level suite name is usually in the first <suite> element
        suite = root.find("suite")
        if suite is not None:
             return suite.get("name") or "UnknownSuite"
        return "UnknownSuite"
    except Exception as e:
        print(f"Error parsing {xml_path}: {e}")
        return "UnknownSuite"

def main():
    # 1. Run Tests
    run_tests()
    
    # 2. Check for Healing Log
    if not os.path.exists(HEALING_LOG):
        print("No healing log found. No self-healing actions to process.")
        return

    # Check if log is empty or just "[]"
    with open(HEALING_LOG, 'r') as f:
        content = f.read().strip()
        if not content or content == "[]":
            print("Healing log is empty. No changes to PR.")
            return

    # 3. Get Suite Name
    suite_name = get_suite_name_from_xml(OUTPUT_XML)
    print(f"Detected Test Suite Name: {suite_name}")

    # 4. Trigger PR Creation
    print("Triggering Auto PR Workflow...")
    subprocess.run([sys.executable, CREATE_PR_SCRIPT, "--suite", suite_name])

if __name__ == "__main__":
    main()
