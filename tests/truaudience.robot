*** Settings ***
Documentation     A demo suite for Self-Healing (Healenium + GenAI).
Resource          ../resources/common.robot
Suite Setup       Setup Driver
Suite Teardown    Close All Browsers

*** Variables ***
# ${MOCK_APP_PATH}    ${CURDIR}/mock_app.html
# Use file:// protocol for local file
# ${URL}              file:///${MOCK_APP_PATH}
${URL}              https://truaudience.transunion.com/


*** Test Cases ***
Test Self Healing On Button Click
    [Documentation]    Tests that the framework can heal a changed ID.
    Go To    ${URL}
    Maximize Browser Window
    
    # Wait for the JS to change the ID (5 seconds)
    Sleep    6s
    
    # This locator is intentionally broken in locators/SelfHealingDemoPage.json
    # It points to 'submit-btn', but the page has 'submit-v3-btn' (or v2)
    Smart Input Text    truaudience_page    email_input_box    soumya.ranjan@xyz.com
    Smart Element Should Be Visible    truaudience_page    next_button
    Smart Click    truaudience_page    next_button
    Smart Wait Until Element Is Visible    truaudience_page    password_input_box
    Log    Test Passed! Healing successful.
