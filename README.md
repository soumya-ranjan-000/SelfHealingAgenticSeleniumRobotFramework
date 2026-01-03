# 🤖 Self-Healing Selenium Robot Framework (Agentic)

> **"Zero-Maintenance" Automation that Fixes Itself.**

## 1. What is this Project?

This is a **Next-Generation Automated Testing Framework** that solves the biggest pain point in Selenium automation: **Brittle Locators**.

Traditional automation scripts fail whenever the UI changes (ID changes, Class renaming, structural shifts). This framework uses **Generative AI (Gemini 2.0)** to "heal" itself at runtime. When a locator fails, the AI Agent steps in, analyzes the page (DOM + Vision), finds the new element, and seamlessly continues the test.

### **Who is it for?**
- **QA Engineers** tired of fixing broken scripts after every deployment.
- **SDETs** building robust, low-maintenance frameworks.
- **Teams** practicing CI/CD where flaky tests block deployments.

### **how & When to use?**
- Use this framework for **E2E UI Testing** of dynamic web applications.
- Run it in your CI/CD pipeline or locally.
- It shines when testing applications with frequent UI updates or AB testing.

---

## 2. Capabilities

This framework implements a **Multi-Level Healing Strategy**:

### 🧠 Level 3: Semantic Healing (GenAI)
Instead of relying on rigid XPaths, the framework captures the **Live DOM** and sends it to a Large Language Model (LLM). The LLM understands the *semantic purpose* of the element (e.g., "The Login Button") and returns a robust new locator.

### 👁️ Multi-Modal Vision Healing (Gemini 2.0)
The framework captures **snapshots** of elements when they are healthy. If they break later, it sends both the **Live Screenshot** and the **Reference Image** to the AI. The AI uses **Visual Reasoning** to find the element even if the underlying code has completely changed (e.g., from `<button>` to `<div>`).

### 🧬 Differential Healing (Snapshots)
It saves a "Minified DOM Snapshot" of every element during successful runs. When a failure occurs, it compares the **Last Known Good State** vs. **Current Broken State** to understand exactly how the element evolved.

### ⚡ Level 5: Agentic Live-Correction
This is the "Zero-Maintenance" magic.
1.  **Detect**: Test fails.
2.  **Heal**: AI finds the new locator.
3.  **Update**: The Agent **automatically rewrites your source code** (JSON Page Objects) with the new locator.
4.  **Commit**: (Optional) It can even create a Git branch and push the fix!

---

## 3. Unique Value Proposition

| Feature | Traditional Framework | This Agentic Framework |
| :--- | :--- | :--- |
| **Maintenance** | Manual. QA spends hours fixing locators. | **Zero**. The AI fixes code for you. |
| **Flakiness** | High. Tests fail on minor UI changes. | **Low**. Tests adapt to UI changes. |
| **Technologies** | XPath, CSS Selectors. | **GenAI, Computer Vision, DOM Diffing**. |
| **Recovery** | None. Test fails immediately. | **Real-time Healing**. Test recovers and passes. |

**Real-World Fit**:
In Agile/DevOps, UI changes daily. Traditional scripts require a 1:1 ratio of development to maintenance time. This framework decouples test logic from locator fragility, allowing QAs to focus on **expanding coverage** rather than **maintaining existence**.

---

## 4. Execution Workflow (Start to End)

1.  **Test Start**: Robot Framework triggers a test case.
2.  **Interaction**: The test calls a wrapper keyword (e.g., `Smart Click`).
3.  **Lookup**: It loads the locator from `locators/[Page].json`.
4.  **Action**:
    *   **Success**: It clicks the element. (Snapshot updated).
    *   **Failure**: `ElementNotFoundException` is caught.
5.  **Healing Trigger (GenAIRescuer)**:
    *   Captures current Page Source (DOM).
    *   Captures Screenshot.
    *   Loads "Last Known" data.
    *   Queries **Gemini LLM**: "Here is the broken page. Find the 'Submit Button' that used to look like X."
6.  **Recovery**: LLM returns 5 candidate locators. The framework tries them in order of priority (ID > Name > CSS > XPath).
7.  **Auto-Fix**: Once a working locator is found:
    *   The test performs the click.
    *   The framework **overwrites** the JSON file with the new locator.
8.  **Result**: Test PASSES. Code is UPDATED.

---

## 5. Directory Structure

```text
SeleniumRobotFramework/
├── README.md               # You are here
├── requirements.txt        # Python dependencies
├── .env                    # API Keys (GEMINI_API_KEY)
├── healing_log.json        # Audit trail of all AI fixes
│
├── libraries/              # Custom Python Agents
│   ├── GenAIRescuer.py     # Main AI Logic (Healing, Vision, LLM Query)
│   ├── LocatorMapper.py    # Utility for locator translation
│   └── LocatorUpdater.py   # Agent that modifies JSON files
│
├── locators/               # PAGE OBJECT MODEL (JSON)
│   ├── login_page.json     # { "button": { "type": "id", "value": "..." } }
│   ├── dom_snapshots/      # Stored historical state of elements
│   └── ...
│
├── resources/              # Robot Framework Resources
│   └── common.robot        # "Smart" keywords (Smart Click, Setup Driver)
│
├── tests/                  # Test Suites
│   └── self_healing_demo.robot
│
└── results/                # Test Execution Reports (Log/Report/XML)
```

---

## 6. Commands & Setup

### Prerequisites
1.  Python 3.10+
2.  Google Gemini API Key (Free tier available)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Configure Environment
Create a `.env` file in the root:
```ini
GEMINI_API_KEY=your_actual_api_key_here
```

### Step 3: Run Tests
Run the demo suite (verify everything works):
```bash
robot -d results tests/self_healing_demo.robot
```

## How It Works (Agentic Flow)
1. **Fail**: Test fails to find an element (e.g., ID changed).
2. **Heal**: GenAI analyzes the page and finds the new locator.
3. **Update**: The agent **automatically updates** the `locators/*.json` file.
4. **Pass**: The test continues successfully. The code is fixed permanently.




https://github.com/user-attachments/assets/8c830b6b-9108-4d18-9315-23f9e6203aa3

