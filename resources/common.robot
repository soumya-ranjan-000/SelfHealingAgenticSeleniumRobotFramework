*** Settings ***
Library    SeleniumLibrary
Library    ../libraries/GenAIRescuer.py

*** Variables ***
${HEALENIUM_PROXY_URL}    http://localhost:8085
${BROWSER}                chrome
${USE_HEALENIUM}          False
${AUTO_UPDATE_LOCATORS}   True
${MAX_DYNAMIC_WAIT}       10s
${ENABLE_VISION_HEALING}    True

*** Keywords ***
Setup Driver
    [Documentation]    Opens browser via Healenium Proxy if enabled, otherwise local.
    ...                For Healenium, we use RemoteWebDriver.
    Run Keyword If    '${USE_HEALENIUM}' == 'True'    Open Browser Via Proxy    ELSE    Open Browser    about:blank    ${BROWSER}

Open Browser Via Proxy
    ${options}=    Evaluate    sys.modules['selenium.webdriver'].ChromeOptions()    sys, selenium.webdriver
    Call Method    ${options}    add_argument    --no-sandbox
    Call Method    ${options}    add_argument    --disable-dev-shm-usage
    # Healenium capability to enable/disable healing
    # Call Method    ${options}    set_capability    healenium:options    {'heal-enabled': True}
    
    Open Browser    url=about:blank    browser=${BROWSER}    remote_url=${HEALENIUM_PROXY_URL}    options=${options}

# ============================================================================
# WRAPPER KEYWORDS - All Selenium operations with self-healing capability
# ============================================================================

Smart Click
    [Arguments]    ${page_name}    ${element_name}
    [Documentation]    Clicks an element with self-healing capability.
    ...                Uses GenAI to find alternative locators if the original fails.
    
    ${element}=    Get WebElement With Healing    ${page_name}    ${element_name}
    Click Element    ${element}

Smart Input Text
    [Arguments]    ${page_name}    ${element_name}    ${text}
    [Documentation]    Inputs text into an element with self-healing capability.
    
    ${element}=    Get WebElement With Healing    ${page_name}    ${element_name}
    Input Text    ${element}    ${text}

Smart Clear Text
    [Arguments]    ${page_name}    ${element_name}
    [Documentation]    Clears text from an input field with self-healing capability.
    
    ${element}=    Get WebElement With Healing    ${page_name}    ${element_name}
    Clear Element Text    ${element}

Smart Get Text
    [Arguments]    ${page_name}    ${element_name}
    [Documentation]    Gets text from an element with self-healing capability.
    ...                Returns the text content of the element.
    
    ${element}=    Get WebElement With Healing    ${page_name}    ${element_name}
    ${text}=    Get Text    ${element}
    RETURN    ${text}

Smart Get Value
    [Arguments]    ${page_name}    ${element_name}
    [Documentation]    Gets the value attribute of an element with self-healing capability.
    
    ${element}=    Get WebElement With Healing    ${page_name}    ${element_name}
    ${value}=    Get Value    ${element}
    RETURN    ${value}

Smart Select From List By Label
    [Arguments]    ${page_name}    ${element_name}    ${label}
    [Documentation]    Selects an option from dropdown by label with self-healing capability.
    
    ${element}=    Get WebElement With Healing    ${page_name}    ${element_name}
    Select From List By Label    ${element}    ${label}

Smart Select From List By Value
    [Arguments]    ${page_name}    ${element_name}    ${value}
    [Documentation]    Selects an option from dropdown by value with self-healing capability.
    
    ${element}=    Get WebElement With Healing    ${page_name}    ${element_name}
    Select From List By Value    ${element}    ${value}

Smart Select From List By Index
    [Arguments]    ${page_name}    ${element_name}    ${index}
    [Documentation]    Selects an option from dropdown by index with self-healing capability.
    
    ${element}=    Get WebElement With Healing    ${page_name}    ${element_name}
    Select From List By Index    ${element}    ${index}

Smart Wait Until Element Is Visible
    [Arguments]    ${page_name}    ${element_name}    ${timeout}=10s
    [Documentation]    Waits until element is visible with self-healing capability.
    
    ${element}=    Get WebElement With Healing    ${page_name}    ${element_name}
    Wait Until Element Is Visible    ${element}    ${timeout}

Smart Wait Until Element Is Enabled
    [Arguments]    ${page_name}    ${element_name}    ${timeout}=10s
    [Documentation]    Waits until element is enabled with self-healing capability.
    
    ${element}=    Get WebElement With Healing    ${page_name}    ${element_name}
    Wait Until Element Is Enabled    ${element}    ${timeout}

Smart Element Should Be Visible
    [Arguments]    ${page_name}    ${element_name}
    [Documentation]    Verifies that element is visible with self-healing capability.
    
    ${element}=    Get WebElement With Healing    ${page_name}    ${element_name}
    Element Should Be Visible    ${element}

Smart Element Should Contain
    [Arguments]    ${page_name}    ${element_name}    ${expected_text}
    [Documentation]    Verifies that element contains expected text with self-healing capability.
    
    ${element}=    Get WebElement With Healing    ${page_name}    ${element_name}
    Element Should Contain    ${element}    ${expected_text}

Smart Element Should Be Enabled
    [Arguments]    ${page_name}    ${element_name}
    [Documentation]    Verifies that element is enabled with self-healing capability.
    
    ${element}=    Get WebElement With Healing    ${page_name}    ${element_name}
    Element Should Be Enabled    ${element}

Smart Element Should Be Disabled
    [Arguments]    ${page_name}    ${element_name}
    [Documentation]    Verifies that element is disabled with self-healing capability.
    
    ${element}=    Get WebElement With Healing    ${page_name}    ${element_name}
    Element Should Be Disabled    ${element}

Smart Get Element Attribute
    [Arguments]    ${page_name}    ${element_name}    ${attribute}
    [Documentation]    Gets an attribute value from element with self-healing capability.
    
    ${element}=    Get WebElement With Healing    ${page_name}    ${element_name}
    ${attr_value}=    Get Element Attribute    ${element}    ${attribute}
    RETURN    ${attr_value}

Smart Double Click Element
    [Arguments]    ${page_name}    ${element_name}
    [Documentation]    Double clicks an element with self-healing capability.
    
    ${element}=    Get WebElement With Healing    ${page_name}    ${element_name}
    Double Click Element    ${element}

Smart Mouse Over
    [Arguments]    ${page_name}    ${element_name}
    [Documentation]    Hovers mouse over an element with self-healing capability.
    
    ${element}=    Get WebElement With Healing    ${page_name}    ${element_name}
    Mouse Over    ${element}

Smart Scroll Element Into View
    [Arguments]    ${page_name}    ${element_name}
    [Documentation]    Scrolls element into view with self-healing capability.
    
    ${element}=    Get WebElement With Healing    ${page_name}    ${element_name}
    Scroll Element Into View    ${element}

Smart Checkbox Should Be Selected
    [Arguments]    ${page_name}    ${element_name}
    [Documentation]    Verifies checkbox is selected with self-healing capability.
    
    ${element}=    Get WebElement With Healing    ${page_name}    ${element_name}
    Checkbox Should Be Selected    ${element}

Smart Select Checkbox
    [Arguments]    ${page_name}    ${element_name}
    [Documentation]    Selects a checkbox with self-healing capability.
    
    ${element}=    Get WebElement With Healing    ${page_name}    ${element_name}
    Select Checkbox    ${element}

Smart Unselect Checkbox
    [Arguments]    ${page_name}    ${element_name}
    [Documentation]    Unselects a checkbox with self-healing capability.
    
    ${element}=    Get WebElement With Healing    ${page_name}    ${element_name}
    Unselect Checkbox    ${element}

Smart Press Keys
    [Arguments]    ${page_name}    ${element_name}    @{keys}
    [Documentation]    Presses keys on an element with self-healing capability.
    
    ${element}=    Get WebElement With Healing    ${page_name}    ${element_name}
    Press Keys    ${element}    @{keys}

Smart Get Element Count
    [Arguments]    ${page_name}    ${element_name}
    [Documentation]    Gets count of matching elements with self-healing capability.
    ...                Note: This returns count of elements matching the healed locator.
    
    ${element}=    Get WebElement With Healing    ${page_name}    ${element_name}
    # For count, we need to use the locator, not the element
    # This is a special case - we'll get the locator from the element
    ${count}=    Get Element Count    ${element}
    RETURN    ${count}

Smart Get WebElements
    [Arguments]    ${page_name}    ${element_name}
    [Documentation]    Gets multiple WebElements with self-healing capability.
    
    ${elements}=    Get WebElements With Healing    ${page_name}    ${element_name}
    RETURN    ${elements}

Smart Submit Form
    [Arguments]    ${page_name}    ${element_name}
    [Documentation]    Submits a form with self-healing capability.
    
    ${element}=    Get WebElement With Healing    ${page_name}    ${element_name}
    Submit Form    ${element}
