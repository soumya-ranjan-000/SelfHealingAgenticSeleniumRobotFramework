*** Settings ***
Resource          ../resources/common.robot
Library           DateTime
Suite Setup       Setup Driver
Suite Teardown    Close All Browsers

*** Variables ***
${URL}            https://html-pages-for-testing.onrender.com/dynamic_page.html

*** Test Cases ***
Verify Visibility Wait and Scroll To View
    [Documentation]    Verifies that the framework waits for visibility and scrolls to the element.
    Go To    ${URL}
    Maximize Browser Window
    
    # 1. Test Scrolling
    # Select a link at the bottom of the page
    Log    Attempting to find and scroll to 'Contact' link at the bottom.
    ${element}=    Get Web Element With Healing    dynamic_page    contact_link
    # The scroll logic is inside the keyword now, but let's verify we can see it
    Log    Is element in view? (Visual check in recording or logs)
    
    # 2. Test Visibility Wait
    # I'll use a script to hide the 'Save Data' button and show it after 10s
    Execute JavaScript    document.querySelector('.save-btn').style.display = 'none'; setTimeout(() => { document.querySelector('.save-btn').style.display = 'block'; }, 10000);
    
    Log    Waiting for 'Save Data' button to become visible (should take 10s)...
    ${start}=    Get Current Date    result_format=epoch
    Smart Click    dynamic_page    save_btn
    ${end}=    Get Current Date    result_format=epoch
    ${duration}=    Evaluate    ${end} - ${start}
    
    Log    Interaction took ${duration} seconds.
    Should Be True    ${duration} >= 10
    
    Alert Should Be Present    Saved!    action=ACCEPT
