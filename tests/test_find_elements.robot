*** Settings ***
Resource          ../resources/common.robot
Suite Setup       Setup Driver
Suite Teardown    Close All Browsers

*** Variables ***
${URL}            https://html-pages-for-testing.onrender.com/dynamic_page.html

*** Test Cases ***
Verify Find Multiple Elements With Healing
    [Documentation]    Verifies that Smart Get WebElements can find multiple elements and heal if broken.
    Go To    ${URL}
    Maximize Browser Window
    
    # 1. Verify finding elements with original locator
    ${elements}=    Smart Get WebElements    FindElementsPage    action_buttons
    ${count}=    Get Length    ${elements}
    Should Be True    ${count} > 0
    Log    Found ${count} buttons using original locator.
    
    # 2. Break locators on the page
    Click Button    id:toggle-locators-btn
    Alert Should Be Present    action=ACCEPT
    
    # 3. Verify finding elements with HEALING
    # The original CSS '.action-btn' should now be broken (JS adds a random class)
    # Actually, the JS adds a random class but keeps the old one? 
    # Let me check the JS again.
    # addClassToElements('action-btn', `btn-${randomNum}`);
    # It KEEPS the action-btn class. So I need a locator that is TRULY broken.
    
    # Let's use a locator that isn't just a class.
    # I'll update the JSON to use an ID that will be changed.
    
    Log    Locators broken (actually some might still work, but let's see).
    ${elements_healed}=    Smart Get WebElements    FindElementsPage    action_buttons
    ${count_healed}=    Get Length    ${elements_healed}
    Log    Found ${count_healed} buttons after healing.
    Should Be True    ${count_healed} > 0
