#!/usr/bin/env python
"""
Example script demonstrating the use of InteractAPI to perform a search
and navigate through search results.
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
    demonstrate browser-ai by performing a search and exploring results
    """
    # check for openai api key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found in environment variables or .env file.")
        print("Please set your OpenAI API key before running this example.")
        return
    
    # get search query from command line or use default
    search_query = "Python programming language"
    if len(sys.argv) > 1:
        search_query = " ".join(sys.argv[1:])
    
    print(f"Will search for: {search_query}")
    
    # create the interact api instance
    interact = InteractAPI(headless=False)
    
    try:
        # start a browser session
        print("Starting browser session...")
        if not interact.start_session():
            print("Failed to start browser session.")
            return
        
        # navigate to a search engine
        print("\nNavigating to search engine...")
        result = interact.execute("Navigate to google.com")
        
        if not result.get("success", False):
            print(f"Failed to navigate to search engine: {result.get('error')}")
            return
            
        # perform the search
        print(f"\nSearching for '{search_query}'...")
        result = interact.execute(f"Search for {search_query}")
        
        if not result.get("success", False):
            print(f"Failed to perform search: {result.get('error')}")
            return
            
        # wait for search results to load
        time.sleep(2)
        
        # get information about the current page
        page_info = interact.get_page_state()
        print(f"Current URL: {page_info.get('url', 'Unknown')}")
        print(f"Page title: {page_info.get('title', 'Unknown')}")
        
        # examine the search results
        print("\nExamining search results...")
        result = interact.execute("Count how many search results are visible on the page")
        
        # click on the first result
        print("\nClicking on the first search result...")
        result = interact.execute("Click on the first search result")
        
        if not result.get("success", False):
            print(f"Failed to click on result: {result.get('error')}")
            return
            
        # wait for the page to load
        time.sleep(3)
        
        # get information about the current page
        page_info = interact.get_page_state()
        print(f"Navigated to: {page_info.get('url', 'Unknown')}")
        print(f"Page title: {page_info.get('title', 'Unknown')}")
        
        # go back to search results
        print("\nGoing back to search results...")
        result = interact.execute("Go back to the search results")
        
        if not result.get("success", False):
            print(f"Failed to go back: {result.get('error')}")
            return
            
        # click on the second result
        print("\nClicking on the second search result...")
        result = interact.execute("Click on the second search result")
        
        if not result.get("success", False):
            print(f"Failed to click on result: {result.get('error')}")
            return
            
        # wait for the page to load
        time.sleep(3)
        
        # take a screenshot
        print("\nTaking a screenshot...")
        interact.execute("Take a screenshot and save it as 'search_result.png'")
        
        # save the action history
        print("\nSaving action history...")
        interact.save_history("search_history.json")
            
    finally:
        # ensure we always close the browser when done
        print("\nEnding browser session...")
        interact.end_session()
        
if __name__ == "__main__":
    main() 