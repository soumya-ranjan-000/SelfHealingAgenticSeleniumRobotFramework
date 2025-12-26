# Execution Guide: Self-Healing Robot Framework

This guide will walk you through running the project, triggering self-healing, and creating a pull request.

## Prerequisites
1.  **Docker Desktop** (Installed and Running) - *Optional, only for Level 2*
2.  **Python 3.8+**
3.  **Gemini API Key** (Set as `GEMINI_API_KEY` env variable)
4.  **Git** (Configured for Level 4)

## Step 1: Install Dependencies
Open a terminal in the project root:
```bash
pip install -r requirements.txt
```

## Step 2: Start Infrastructure (Level 2)
This starts the Healenium Proxy and Backend.
*Note: If you skip this, ensure `USE_HEALENIUM` is `False` in `resources/common.robot`.*
```bash
cd docker
docker-compose up -d
```
> Wait about 30 seconds for the containers to fully start. You can check status with `docker ps`.

## Step 3: Run the Test (Break it!)
We have a test `tests/self_healing_demo.robot` that opens `mock_app.html`.
It references a Page Object `SelfHealingDemoPage.json` where the locator `submit_btn` points to the **old** ID (`submit-btn`).
The mock app changes that ID to `submit-v3-btn` after 5 seconds.

Run it:
```bash
# Ensure you are in the project root
# Windows (PowerShell)
$env:GEMINI_API_KEY="your-api-key"
robot -d results tests/self_healing_demo.robot
```

**What to Expect (Agentic Healing):**
1.  Browser opens.
2.  Test fails on `submit_btn` (Initial attempt).
3.  **GenAI Rescues**: Finds the new `submit-v3-btn`.
4.  **Live Update**: The system **automatically updates** `locators/SelfHealingDemoPage.json` with the new value.
5.  Test **PASSES**.

## Step 4: Verify the Fix
Open `locators/SelfHealingDemoPage.json`. You will see it has been updated to:
```json
"submit_btn": {
  "type": "id", 
  "value": "submit-v3-btn"
}
```
Run the test again. It will pass immediately without needing to heal, because the code itself was fixed.

---

# Challenge Mode: Advanced Self-Healing Testing

## Overview

The `mock_app.html` has been enhanced with **Challenge Mode** to rigorously test GenAI's self-healing capabilities. This mode removes most IDs and uses diverse, complex locator strategies with random number-based breaking.

## Running Challenge Mode Tests

```bash
# Run the comprehensive challenge mode tests
robot --outputdir results tests/test_dynamic_elements.robot

# Run specific test
robot -t "Test Self-Healing With Diverse Locator Types" tests/test_dynamic_elements.robot
```

## What Makes It Challenging?

### 1. Minimal IDs (90% Removed)
Only 2 elements retain IDs:
- `toggle-locators-btn` (control button)
- `submit-registration-btn` (submit button)

All other elements use:
- **Name attributes**: `userName`, `colorSelect`, `about-link`
- **CSS classes**: `.phone-field`, `.country-selector`, `.export-btn`
- **Data attributes**: `data-testid`, `data-action`, `data-page`
- **Aria labels**: `aria-label="Full Name Input"`
- **XPath**: `//p[@data-type='warning']`

### 2. Random Number Breaking (1000-9999)

Instead of fixed patterns, locators break with random 4-digit numbers:

```javascript
// Examples of random breaking:
userName → userName_4523
colorSelect → colorSelect_7891
data-testid="email-input" → data-testid="email-input_2156"
class="form-input" → class="form-input input-3489"
aria-label="Full Name Input" → aria-label="Full Name Input 6234"
```

### 3. Context-Dependent Elements

Some elements have NO unique identifiers:

| Element | Challenge |
|---------|-----------|
| Phone Input | Only `class="phone-field"` - no ID, no name, no data-testid |
| Country Dropdown | Only `class="country-selector"` and `aria-label` |
| Export Button | Only `class="export-btn"` - no data-action |

GenAI must use:
- Surrounding context (labels, siblings)
- Element position in DOM
- Text content
- Placeholder text
- Aria labels

## Challenge Mode Locator Examples

### Example 1: Name Input
```html
<!-- Original -->
<input name="userName" class="form-input name-field" 
       data-testid="name-input" aria-label="Full Name Input">

<!-- After Toggle (Random: 4523) -->
<input name="userName_4523" class="form-input name-field input-4523" 
       data-testid="name-input_4523" aria-label="Full Name Input 4523">
```

**Locator Options**:
- `name="userName"` ❌ Broken
- `[data-testid="name-input"]` ❌ Broken
- `[aria-label="Full Name Input"]` ❌ Broken
- `.name-field` ✅ Still works (but not unique)
- `//input[@placeholder='Enter your full name']` ✅ Works
- `//label[text()='Full Name:']/following-sibling::input` ✅ Works

### Example 2: Phone Input (Hardest)
```html
<!-- Original -->
<input class="phone-field" placeholder="Enter phone number" 
       aria-label="Phone Number">

<!-- After Toggle (Random: 7891) -->
<input class="phone-field input-7891" placeholder="Enter phone number" 
       aria-label="Phone Number 7891">
```

**Locator Options**:
- `.phone-field` ✅ Still works (but has added class)
- `[aria-label="Phone Number"]` ❌ Broken
- `//input[@placeholder='Enter phone number']` ✅ Works
- `//label[text()='Phone:']/following-sibling::input` ✅ Works
- `.user-form input:nth-of-type(3)` ✅ Works (position-based)

### Example 3: Country Dropdown
```html
<!-- Original -->
<select class="country-selector" aria-label="Country Selection">

<!-- After Toggle (Random: 2156) -->
<select class="country-selector select-2156" aria-label="Country Selection 2156">
```

**Locator Options**:
- `.country-selector` ✅ Still works
- `[aria-label="Country Selection"]` ❌ Broken
- `//label[text()='Country:']/following-sibling::select` ✅ Works
- `select.dropdown-control:nth-of-type(2)` ✅ Works

## Expected GenAI Behavior

When locators break, GenAI should:

1. **Analyze Context**: Look at labels, placeholders, surrounding elements
2. **Suggest Multiple Alternatives**: Provide fallback locators
3. **Prioritize Stability**: Prefer text-based or position-based locators
4. **Update JSON**: Automatically update `mock_page.json` with healed locator

## Verification

After running tests:

1. **Check Healing Log**:
```bash
cat healing_log.json
```

2. **Check Updated Locators**:
```bash
cat locators/mock_page.json
```

3. **Review Test Report**:
```bash
# Open in browser
results/report.html
```

## Difficulty Levels

| Level | IDs | Breaking Pattern | Complexity |
|-------|-----|------------------|------------|
| Easy | All elements | Fixed suffix `-v2` | 🟢 Low |
| Medium | 50% elements | Cycling patterns | 🟡 Medium |
| **Challenge** | **10% elements** | **Random 1000-9999** | 🔴 **High** |

## Tips for Success

1. **Use Wrapper Keywords**: Always use `Smart Click`, `Smart Input Text`, etc.
2. **Enable Auto-Update**: Set `${AUTO_UPDATE_LOCATORS} = True` in `common.robot`
3. **Monitor Logs**: Watch console output for healing events
4. **Review Suggestions**: Check what alternative locators GenAI suggests

## Summary

Challenge Mode tests the **true power** of GenAI self-healing by:
- ✅ Removing easy ID-based locators
- ✅ Using diverse identifier types
- ✅ Implementing unpredictable random breaking
- ✅ Forcing context-aware element discovery

This creates a realistic environment that mirrors real-world web applications where IDs are often missing or unstable!
