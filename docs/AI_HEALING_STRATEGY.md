# Gemini AI Self-Healing Strategy

This document explains the technical strategy and logic behind how the Gemini AI predicts and heals locators in this framework, even when the provided input is irrelevant or broken.

---

## 1. Contextual Intelligence (Mind-Reading)
When a locator fails, the system doesn't just send the broken string to Gemini. It provides a rich context package that allows the AI to "understand" the intent:

*   **The Intent (Element Name):** The AI is given the semantic name of the element (e.g., `SubmitButton`, `LoginField`). This name often carries more weight than a technical XPath.
*   **The Reality (Minified DOM):** The system captures the current HTML of the page. To save tokens and improve focus, it "minifies" the DOM by stripping out:
    *   `<script>` and `<style>` blocks
    *   `<svg>` and `<link>` tags
    *   Comments and metadata
*   **The History (Failed Locator):** Even if irrelevant, the old locator provides a "starting point" for what the element *used* to be.

## 2. The Generative Reasoning Process
Gemini acts as an **Agentic Developer**. The logic follows these steps:

1.  **Semantic Mapping:** It maps the "Element Name" to the HTML structure. If you're looking for `UserIcon`, it looks for `<img>`, `<i>`, or `<span>` tags near text labels like "Profile" or "Account".
2.  **Structural Analysis:** It analyzes the attributes (`id`, `class`, `name`, `data-testid`) of the elements it finds in the DOM snippet.
3.  **Multi-Candidate Generation:** Instead of one guess, it generates a ranked list of multiple locator types:
    *   `id` (Highest Priority)
    *   `name`
    *   `css_selector`
    *   `xpath` (Fallback)

## 3. The "Trust but Verify" Loop
The system never blindly accepts an AI prediction. It uses a validation loop to ensure correctness:

*   **Priority Sorting:** The `LocatorMapper` library sorts the AI's suggestions. Hardware-efficient locators (like `id`) are tried before expensive ones (like `xpath`).
*   **Live Validation:** The system attempts to find the element on the **active browser window** using each suggested locator.
*   **Visibility Check:** Only elements that are **actually visible** on the screen are considered successful matches. If a locator finds a hidden element, the loop continues to the next suggestion.
*   **Winner-Takes-All:** The first locator that produces a visible element on the live page is crowned the "winner."

## 4. Continuity & Learning (The Feedback Loop)
Once a locator is healed, the system ensures it doesn't have to "think" as hard next time:

*   **Healing Logs:** Every successful repair is recorded in `healing_log.json` with the timestamp and the old vs. new values.
*   **Agentic Updates:** If `AUTO_UPDATE_LOCATORS` is set to `True`, the system automatically overwrites the original JSON file in the `locators/` directory with the new, working locator. 
*   **Zero-Latency Future Rounds:** Subsequent test runs will use the updated locator immediately, bypassing the AI healing process entirely until the next UI change.

---

## Why it works even with "Irrelevant" inputs:
Because the AI prioritizes **Element Name + Current DOM Structure** over the **Failed Locator String**. As long as the AI can see the current page and knows what "Role" the element plays, it can find it regardless of how broken the previous locator was.
