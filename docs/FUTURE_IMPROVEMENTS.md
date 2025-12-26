# Future Roadmap: Advanced AI Healing Strategies

This document outlines planned improvements to the Gemini-based self-healing mechanism to reach near 100% accuracy and robustness.

---

## 1. Differential Healing (DOM Snapshots)
**Concept:** Provide Gemini with both the "Last Known Good" DOM and the "Current Broken" DOM.

*   **Logic:** Gemini performs a structural "diff" to identify how an element has evolved.
*   **Implementation Requirement:** 
    *   A mechanism to save a minified DOM snippet to the `locators/` directory whenever a locator is used successfully.
    *   Updating the prompt to include: *"In the previous version, the element look like X. In the current version, identify its equivalent."*

## 2. Multi-Modal Vision (Visual Reasoning)
**Concept:** Use Gemini 2.0's vision capabilities by providing screenshots of the failure state.

*   **Logic:** Sometimes structural data (HTML) is insufficient (e.g., elements hidden by overlays or canvas-based components).
*   **Implementation Requirement:**
    *   Capture a base64 encoded screenshot of the browser viewport upon locator failure.
    *   Send the image alongside the HTML to Gemini.
    *   Prompt: *"Look at this screenshot. Find the button labeled 'Submit' and provide its structural locator from the attached HTML."*

## 3. Hierarchical Ancestry (Landmarking)
**Concept:** Provide the "Path of Parents" rather than just the target element.

*   **Logic:** An element might change its ID, but its parent container (like `div#login-form`) is often more stable.
*   **Implementation Requirement:**
    *   When saving "Last Known Good" state, save the tag/attributes of the 3 immediate parent levels.
    *   This provides Gemini with "landmarks" to narrow down the search area in a large DOM.

## 4. Workflow & Intent Context
**Concept:** Inform Gemini of the test's high-level goal and recent actions.

*   **Logic:** Knowing that the test just filled a password helps Gemini distinguish between multiple "Submit" buttons on a page.
*   **Implementation Requirement:**
    *   Extract the Robot Framework `${TEST_NAME}` and the names of the last 3 keywords executed.
    *   Include in prompt: *"Context: The user is currently in the 'Checkout' flow and just entered 'Credit Card' details. Find the final confirmation button."*

## 5. Negative Constraints (Anti-Brittle Logic)
**Concept:** Teach Gemini which attributes to ignore.

*   **Logic:** Modern frameworks (Angular, React, Vue) generate temporary, dynamic IDs (e.g., `_ngcontent-c12`).
*   **Implementation Requirement:**
    *   Define a list of "Unstable Patterns" (regex).
    *   Prompt instruction: *"Ignore attributes matching 'id=^css-' or 'class=.*active.*' as these are dynamic and will break on the next run."*

---

## Technical Feasibility Summary
| Strategy | Complexity | Impact | Priority |
| :--- | :--- | :--- | :--- |
| **Differential Healing** | Medium | High | P1 |
| **Workflow Context** | Low | Medium | P2 |
| **Vision/Screenshots** | High | Very High | P2 |
| **Negative Constraints** | Low | High | P1 |

### Summary of an "Ultimate" AI Prompt:
If we were to upgrade your [GenAIRescuer.py](cci:7://file:///d:/SeleniumRobotFramework/libraries/GenAIRescuer.py:0:0-0:0), the "Perfect Prompt" would look like this:

> "I was performing a **Login Test**. My last action was **'Type Password'**. 
> I am now looking for an element I call **'SubmitButton'**. 
> In the **Last Working Version**, it looked like this: `{old_html_snippet}`. 
> In the **Current Broken Version**, the page looks like this: `{new_dom_snippet}`. 
> Here is a **screenshot** of the current state. 
> **Please find the equivalent element.**"