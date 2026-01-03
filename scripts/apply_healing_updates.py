import os
import sys

# Ensure libraries path is in sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'libraries'))
import LocatorUpdater

def main():
    print("Running Apply Healing Updates...")
    try:
        modified_files = LocatorUpdater.update_locators()
        if modified_files:
            print(f"Successfully modified {len(modified_files)} files.")
        else:
            print("No files were modified (either no healing log or no changes needed).")
    except Exception as e:
        print(f"Error applying updates: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
