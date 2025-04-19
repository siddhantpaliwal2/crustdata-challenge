#!/usr/bin/env python
"""
Example script demonstrating the use of InteractAPI to log into a website.
This example shows how to handle form filling and authentication.
"""

import os
import sys
import time
from dotenv import load_dotenv

# add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_ai import InteractAPI

# load environment variables
load_dotenv()

def main():
    """
    demonstrate browser-ai by logging into a website
    """
    # check for openai api key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found in environment variables or .env file.")
        print("Please set your OpenAI API key before running this example.")
        return
    
    # get credentials from environment or user input
    username = os.getenv("DEMO_USERNAME")
    password = os.getenv("DEMO_PASSWORD")
    
    if not username:
        username = input("Enter your username for the demo: ")
    if not password:
        password = input("Enter your password for the demo: ")
    
    # create the interact api instance
    interact = InteractAPI(headless=False)
    
    try:
        # start a browser session
        print("Starting browser session...")
        if not interact.start_session():
            print("Failed to start browser session.")
            return
        
        # for this example, we'll use GitHub's login page
        # you could replace this with any login page
        print("\nNavigating to GitHub login page...")
        result = interact.execute("Navigate to github.com/login")
        
        if not result.get("success", False):
            print(f"Failed to navigate to login page: {result.get('error')}")
            return
            
        # fill in the username
        print("\nFilling in the username...")
        result = interact.execute(f"Enter '{username}' in the username field")
        
        if not result.get("success", False):
            print(f"Failed to enter username: {result.get('error')}")
            return
            
        # fill in the password
        print("\nFilling in the password...")
        result = interact.execute(f"Enter '{password}' in the password field")
        
        if not result.get("success", False):
            print(f"Failed to enter password: {result.get('error')}")
            return
            
        # click the sign in button
        print("\nClicking the sign in button...")
        result = interact.execute("Click the sign in button")
        
        if not result.get("success", False):
            print(f"Failed to click sign in button: {result.get('error')}")
            return
            
        # wait for login to complete and check if successful
        print("\nChecking if login was successful...")
        time.sleep(3)  # give it a moment to process
        
        result = interact.execute("Check if we are now logged in")
        
        # get current page information
        page_info = interact.get_page_state()
        print(f"Current URL: {page_info.get('url', 'Unknown')}")
        print(f"Page title: {page_info.get('title', 'Unknown')}")
        
        # take a screenshot
        print("\nTaking a screenshot...")
        interact.execute("Take a screenshot and save it as 'login_result.png'")
        
        # save the action history
        print("\nSaving action history...")
        interact.save_history("login_history.json")
            
    finally:
        # ensure we always close the browser when done
        print("\nEnding browser session...")
        interact.end_session()
        
if __name__ == "__main__":
    main() 