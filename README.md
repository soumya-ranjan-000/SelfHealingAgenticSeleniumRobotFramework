# Self-Healing Selenium Robot Framework

This project implements a next-gen automated testing framework with a "Zero-Maintenance" goal using a Dual-Layer AI approach.

## Features
- **Level 3 Healing**: Uses GenAI (LLM) as a fallback rescuer to find semantic matches by analyzing raw HTML.
- **Level 4 Maintenance**: Automated feedback loop. Logs all healing events to `healing_log.json`.
- **Level 5 Agentic Live-Update**: The system is **Self-Correcting**. When GenAI finds a fix, it **automatically updates the JSON Page Object file** in real-time.

## Architecture
This project uses a **JSON-based Page Object Model (POM)**.
- Locators are stored in `locators/[PageName].json`.
- Tests reference them by Page Name and Element Name.

## Setup
1. **Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configuration**:
   - Create a `.env` file with `GEMINI_API_KEY=your_key_here`.

## Execution
Run the demo suite:
```bash
robot -d results tests/self_healing_demo.robot
```

## How It Works (Agentic Flow)
1. **Fail**: Test fails to find an element (e.g., ID changed).
2. **Heal**: GenAI analyzes the page and finds the new locator.
3. **Update**: The agent **automatically updates** the `locators/*.json` file.
4. **Pass**: The test continues successfully. The code is fixed permanently.




https://github.com/user-attachments/assets/8c830b6b-9108-4d18-9315-23f9e6203aa3

