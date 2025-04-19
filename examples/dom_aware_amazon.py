#!/usr/bin/env python
"""
Enhanced example demonstrating the DOM-aware capabilities of the browser-ai API
for navigating Amazon with improved reliability.
"""

import os
import sys
import time
import json
from dotenv import load_dotenv

# add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_ai import InteractAPI

# load environment variables
load_dotenv()

def save_dom_snapshot(interact, filename):
    """Save DOM snapshot to a file for debugging"""
    snapshot = interact.get_dom_snapshot()
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)
    print(f"DOM snapshot saved to {filename}")

def main():
    """
    demonstrate dom-aware browser-ai capabilities by navigating amazon
    """
    # check for openai api key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found in environment variables or .env file.")
        print("Please set your OpenAI API key before running this example.")
        return
    
    # create the interact api instance
    # setting headless=False to see the browser in action
    interact = InteractAPI(headless=False)
    
    try:
        # start a browser session
        print("Starting browser session with enhanced DOM awareness...")
        if not interact.start_session():
            print("Failed to start browser session.")
            return
        
        # Navigate to Amazon
        print("\n1. Navigating to Amazon.com...")
        result = interact.execute("Navigate to Amazon.com")
        
        print(f"Navigation successful: {result.get('success', False)}")
        print(f"Current URL: {interact.page.url}")
        print(f"Page title: {interact.page.title()}")
        
        # Wait for page to fully load
        print("\nWaiting for page to fully load...")
        time.sleep(3)
        
        # Take DOM snapshot to enhance context
        print("\nTaking DOM snapshot to enhance context...")
        interact.get_dom_snapshot()
        
        # Try to navigate to fashion department
        print("\n2. Looking for the fashion department...")
        result = interact.execute("Find and click on the Fashion department or clothing category")
        
        if result.get('success', False):
            print("Successfully navigated to Fashion department!")
        else:
            print("Failed to find Fashion department with first attempt. Trying alternative approach...")
            
            # Save DOM snapshot for debugging
            save_dom_snapshot(interact, "amazon_home_snapshot.json")
            
            # Try a more specific approach
            print("\nTrying with more specific instructions...")
            result = interact.execute("Look at the navigation menu elements in the DOM and find one containing 'fashion' or 'clothing', then click it")
        
        # Wait for page to load
        time.sleep(3)
        
        # Take new DOM snapshot after navigation
        print("\nTaking updated DOM snapshot after navigation...")
        interact.get_dom_snapshot()
        
        # Try to navigate to women's clothing with DOM awareness
        print("\n3. Navigating to women's clothing section...")
        result = interact.execute("Using the interactive elements in the DOM, find and click on a link or element for women's clothing or women's fashion")
        
        if result.get('success', False):
            print("Successfully navigated to women's clothing!")
        else:
            print("Failed to navigate to women's clothing. Trying alternative approach...")
            
            # Save DOM snapshot for debugging
            save_dom_snapshot(interact, "amazon_fashion_snapshot.json")
            
            # Try with direct text search
            print("\nTrying with direct text search...")
            interact.execute("Look for any element containing the exact text 'Women' and click it")
        
        # Wait for page to load
        time.sleep(3)
        
        # Scroll to see more products
        print("\n4. Scrolling to see more products...")
        interact.execute("Scroll down to see more products")
        
        # Take updated DOM snapshot
        print("\nTaking updated DOM snapshot after scrolling...")
        interact.get_dom_snapshot()
        
        # Try to click on a product with improved context awareness
        print("\n5. Finding and clicking on a product...")
        result = interact.execute("Find a product item in the DOM and click on it. Look specifically for product cards, items, or links with images")
        
        if result.get('success', False):
            print("Successfully clicked on a product!")
        else:
            print("Failed to click on a product. Trying alternative approach...")
            
            # Try more specific selector-aware approach
            print("\nTrying with more specific selector instructions...")
            interact.execute("Look for elements with class names containing 'product', 'item', or 'card' in their selectors and click one")
        
        # Wait for product page to load
        time.sleep(5)
        
        # Take screenshot of final state
        print("\nTaking screenshot of final state...")
        interact.execute("Take a screenshot and save it as 'dom_aware_result.png'")
        
        # Save final DOM snapshot 
        save_dom_snapshot(interact, "amazon_final_snapshot.json")
        
        # Save the action history
        print("\nSaving action history...")
        interact.save_history("dom_aware_amazon_history.json")
            
    finally:
        # ensure we always close the browser when done
        print("\nEnding browser session...")
        interact.end_session()
        
if __name__ == "__main__":
    main() 