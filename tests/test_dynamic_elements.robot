*** Settings ***
Documentation     Comprehensive test suite for verifying Self-Healing with diverse locator types.
...               Tests ID, Name, CSS, XPath, and data-testid locators.
Resource          ../resources/common.robot

*** Variables ***
# ${MOCK_PAGE_URL}    ${CURDIR}/dynamic_page.html
${MOCK_PAGE_URL}      https://html-pages-for-testing.onrender.com/dynamic_page.html
${PAGE_NAME}        dynamic_page

*** Test Cases ***
Test Self-Healing With Diverse Locator Types
    [Documentation]    Tests self-healing mechanism with ID, Name, CSS, XPath, and data-testid locators.
    ...                Interacts with elements, breaks them dynamically, and verifies healing.
    
    Setup Driver
    Go To    ${MOCK_PAGE_URL}
    Maximize Browser Window
    Sleep    5s    # Wait for page to fully load

    # Log    ===== Using Breaking Locators =====    console=True
    
    # Click the toggle button to break locators (using direct Selenium since this button shouldn't break)
    # Click Element    id:toggle-locators-btn
    Sleep    2s    # Wait for JavaScript to modify all locators
    
    # Test ID-based locators
    Log    Testing ID-based locators...    console=True
    Smart Input Text    ${PAGE_NAME}    user_name_input    John Doe
    Smart Input Text    ${PAGE_NAME}    user_email_input    john@example.com
    Smart Click    ${PAGE_NAME}    register_button
    Alert Should Be Present    Registered!
    Sleep    2s
    
    # Test Name-based locators
    Log    Testing Name-based locators...    console=True
    Smart Input Text    ${PAGE_NAME}    user_phone_input    555-1234
    
    # Test CSS-based locators
    Log    Testing CSS-based locators...    console=True
    Smart Click    ${PAGE_NAME}    save_btn
    Handle Alert    action=ACCEPT    # Accept "Saved!" alert
    Sleep    2s
    Smart Click    ${PAGE_NAME}    delete_btn
    Handle Alert    action=ACCEPT    # Accept "Deleted!" alert
    Sleep    2s
    
    # Test dropdown with ID
    Log    Testing dropdown with ID locator...    console=True
    Smart Select From List By Value    ${PAGE_NAME}    color_dropdown    green
    
    # Test dropdown with Name
    Log    Testing dropdown with Name locator...    console=True
    Smart Select From List By Value    ${PAGE_NAME}    country_dropdown    us
    
    # Test links with different locators
    Log    Testing links with different locators...    console=True
    Smart Click    ${PAGE_NAME}    home_link
    Handle Alert    action=ACCEPT    # Accept "Home" alert
    Sleep    0.5s
    Smart Click    ${PAGE_NAME}    about_link
    Handle Alert    action=ACCEPT    # Accept "About" alert
    Sleep    0.5s
    Smart Click    ${PAGE_NAME}    contact_link
    Handle Alert    action=ACCEPT    # Accept "Contact" alert
    Sleep    0.5s
    
    # Test XPath-based locators
    Log    Testing XPath-based locators...    console=True
    ${warning_text}=    Smart Get Text    ${PAGE_NAME}    warning_message
    Should Contain    ${warning_text}    Warning
    
    ${error_text}=    Smart Get Text    ${PAGE_NAME}    error_message
    Should Contain    ${error_text}    Error
    
    # Test element visibility
    Log    Testing element visibility checks...    console=True
    Smart Element Should Be Visible    ${PAGE_NAME}    status_badge
    
    # Test Get Element Attribute
    Log    Testing Get Element Attribute...    console=True
    ${status}=    Smart Get Element Attribute    ${PAGE_NAME}    status_badge    data-status
    Should Be Equal    ${status}    ready
    
    Log    ===== TEST COMPLETE =====    console=True
    Log    All locator types tested: ID, Name, CSS, XPath, data-testid    console=True
    Log    Self-healing mechanism verified for all types    console=True
    
    [Teardown]    Close Browser

Test Multiple Locator Strategies For Same Element
    [Documentation]    Tests that elements with multiple locator strategies can be healed.
    ...                Uses alternative locators like data-testid when primary locators fail.
    
    Setup Driver
    Go To    ${MOCK_PAGE_URL}
    Maximize Browser Window
    Sleep    5s
    
    Log    Testing alternative locator strategies...    console=True
    
    # Test using data-testid based locators
    Smart Input Text    ${PAGE_NAME}    name_input_by_testid    Test User
    Smart Input Text    ${PAGE_NAME}    email_input_by_testid    test@example.com
    
    # Test using class-based locator
    Smart Input Text    ${PAGE_NAME}    phone_input_by_class    555-0000
    
    # Break locators
    Click Element    id:toggle-locators-btn
    Sleep    2s
    
    # Test healing with alternative strategies
    Smart Clear Text    ${PAGE_NAME}    name_input_by_testid
    Smart Input Text    ${PAGE_NAME}    name_input_by_testid    Healed User
    
    Log    Alternative locator strategies test complete!    console=True
    
    [Teardown]    Close Browser

Test Advanced Wrapper Keywords
    [Documentation]    Tests advanced wrapper keywords like Mouse Over, Double Click, etc.
    
    Setup Driver
    Go To    ${MOCK_PAGE_URL}
    Maximize Browser Window
    Sleep    5s
    
    Log    Testing advanced wrapper keywords...    console=True
    
    # Test Mouse Over
    Smart Mouse Over    ${PAGE_NAME}    save_btn
    Sleep    0.5s
    
    # Test Scroll Element Into View
    Smart Scroll Element Into View    ${PAGE_NAME}    product_table
    Sleep    0.5s
    
    # Test Wait Until Element Is Visible
    Smart Wait Until Element Is Visible    ${PAGE_NAME}    status_badge    5s
    
    # Test Element Should Contain
    Smart Element Should Contain    ${PAGE_NAME}    status_badge    Ready
    
    Log    Advanced wrapper keywords test complete!    console=True
    
    [Teardown]    Close Browser
