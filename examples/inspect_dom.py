#!/usr/bin/env python
"""
DOM inspection utility that helps users understand the page structure
and find reliable CSS selectors for automation.
"""

import os
import sys
import time
import json
import argparse
from dotenv import load_dotenv

# add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_ai import InteractAPI

# load environment variables
load_dotenv()

def print_interactive_elements(elements, limit=20):
    """Print a formatted list of interactive elements"""
    print("\n=== Interactive Elements ===")
    print(f"Found {len(elements)} interactive elements. Showing top {min(limit, len(elements))}:")
    
    for i, element in enumerate(elements[:limit]):
        selector = element.get('selector', 'N/A')
        text = element.get('text', '').strip()
        if len(text) > 50:
            text = text[:47] + "..."
        
        tag = element.get('tagName', 'unknown')
        element_type = element.get('type', tag)
        
        print(f"{i+1}. {tag}[{element_type}] - '{text}' - Selector: {selector}")

def print_form_elements(forms):
    """Print a formatted list of form elements"""
    print("\n=== Form Elements ===")
    print(f"Found {len(forms)} forms:")
    
    for i, form in enumerate(forms):
        print(f"\nForm {i+1}:")
        form_id = form.get('id', 'No ID')
        form_name = form.get('name', 'No name')
        print(f"ID: {form_id}, Name: {form_name}")
        
        elements = form.get('elements', [])
        print(f"Form fields ({len(elements)}):")
        
        for j, field in enumerate(elements):
            field_type = field.get('type', 'unknown')
            field_name = field.get('name', 'unnamed')
            field_id = field.get('id', 'no-id')
            field_label = field.get('label', '')
            placeholder = field.get('placeholder', '')
            
            label_info = f", Label: '{field_label}'" if field_label else ""
            placeholder_info = f", Placeholder: '{placeholder}'" if placeholder else ""
            
            print(f"  {j+1}. {field_type} - Name: '{field_name}', ID: '{field_id}'{label_info}{placeholder_info}")

def print_navigation(navigation):
    """Print a formatted list of navigation elements"""
    print("\n=== Navigation Elements ===")
    print(f"Found {len(navigation)} navigation areas:")
    
    for i, nav in enumerate(navigation):
        selector = nav.get('selector', 'Unknown')
        nav_id = nav.get('id', 'No ID')
        
        print(f"\nNavigation {i+1}: {selector} (ID: {nav_id})")
        
        links = nav.get('links', [])
        print(f"Links ({len(links)}):")
        
        for j, link in enumerate(links[:10]):  # Show first 10 links
            text = link.get('text', '').strip()
            href = link.get('href', '')
            aria = link.get('ariaLabel', '')
            
            if len(text) > 30:
                text = text[:27] + "..."
                
            aria_info = f", Aria: '{aria}'" if aria else ""
            href_info = f" -> {href}" if href else ""
            
            print(f"  {j+1}. '{text}'{aria_info}{href_info}")

def interactive_inspect(interact):
    """Interactive inspection mode where user can explore elements"""
    while True:
        # Get current page info
        url = interact.page.url
        title = interact.page.title()
        
        print("\n" + "="*80)
        print(f"Current page: {title}")
        print(f"URL: {url}")
        print("="*80)
        
        # Show menu
        print("\nInspection Menu:")
        print("1. View all interactive elements")
        print("2. View form elements")
        print("3. View navigation elements")
        print("4. Inspect specific element (by selector)")
        print("5. Navigate to URL")
        print("6. Execute command")
        print("7. Save DOM snapshot to file")
        print("8. Take screenshot")
        print("9. Exit")
        
        choice = input("\nEnter choice (1-9): ").strip()
        
        # Get fresh DOM snapshot
        snapshot = interact.get_dom_snapshot()
        
        if choice == '1':
            # View interactive elements
            elements = snapshot.get('interactive_elements', [])
            print_interactive_elements(elements)
            
            # Allow clicking on an element
            element_choice = input("\nEnter element number to click (or Enter to skip): ").strip()
            if element_choice.isdigit() and 1 <= int(element_choice) <= len(elements):
                idx = int(element_choice) - 1
                selector = elements[idx].get('selector')
                
                if selector:
                    print(f"Clicking element with selector: {selector}")
                    try:
                        interact.page.click(selector)
                        print("Click successful")
                        time.sleep(2)  # Wait for any navigation
                    except Exception as e:
                        print(f"Error clicking element: {e}")
        
        elif choice == '2':
            # View form elements
            forms = snapshot.get('form_elements', [])
            print_form_elements(forms)
        
        elif choice == '3':
            # View navigation elements
            navigation = snapshot.get('navigation', [])
            print_navigation(navigation)
        
        elif choice == '4':
            # Inspect specific element
            selector = input("Enter CSS selector to inspect: ").strip()
            if selector:
                element_info = interact.inspect_element(selector)
                
                if 'error' in element_info:
                    print(f"Error: {element_info['error']}")
                else:
                    print("\n=== Element Details ===")
                    for key, value in element_info.items():
                        if key != 'attributes' and key != 'rect':
                            print(f"{key}: {value}")
                    
                    print("\nPosition:")
                    for key, value in element_info.get('rect', {}).items():
                        print(f"  {key}: {value}")
                    
                    print("\nAttributes:")
                    for attr in element_info.get('attributes', []):
                        print(f"  {attr.get('name')}: {attr.get('value')}")
        
        elif choice == '5':
            # Navigate to URL
            url = input("Enter URL to navigate to: ").strip()
            if url:
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                
                print(f"Navigating to {url}...")
                interact.page.goto(url)
                interact.page.wait_for_load_state("networkidle")
                print("Navigation complete")
        
        elif choice == '6':
            # Execute command
            command = input("Enter natural language command: ").strip()
            if command:
                print(f"Executing: {command}")
                result = interact.execute(command)
                print(f"Result: {'Success' if result.get('success', False) else 'Failed'}")
                if not result.get('success', False) and 'error' in result:
                    print(f"Error: {result['error']}")
        
        elif choice == '7':
            # Save DOM snapshot
            filename = input("Enter filename to save snapshot (default: dom_snapshot.json): ").strip()
            if not filename:
                filename = "dom_snapshot.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(snapshot, f, indent=2, ensure_ascii=False)
            print(f"DOM snapshot saved to {filename}")
        
        elif choice == '8':
            # Take screenshot
            filename = input("Enter filename for screenshot (default: screenshot.png): ").strip()
            if not filename:
                filename = "screenshot.png"
            
            interact.page.screenshot(path=filename)
            print(f"Screenshot saved to {filename}")
        
        elif choice == '9':
            # Exit
            print("Exiting inspection mode")
            break
        
        else:
            print("Invalid choice. Please enter a number from 1-9.")

def main():
    """Main function for DOM inspection utility"""
    parser = argparse.ArgumentParser(description='DOM inspection utility')
    parser.add_argument('url', nargs='?', default='https://www.google.com',
                        help='URL to inspect (default: google.com)')
    parser.add_argument('--headless', action='store_true',
                        help='Run in headless mode (no visible browser)')
    args = parser.parse_args()
    
    # check for openai api key
    if not os.getenv("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY not found. Some features may not work properly.")
    
    # create the interact api instance
    interact = InteractAPI(headless=args.headless)
    
    try:
        # start a browser session
        print("Starting browser session...")
        if not interact.start_session():
            print("Failed to start browser session.")
            return
        
        # Navigate to the specified URL
        print(f"Navigating to {args.url}...")
        interact.page.goto(args.url)
        interact.page.wait_for_load_state("networkidle")
        
        # Start interactive inspection
        interactive_inspect(interact)
        
    finally:
        # ensure we always close the browser when done
        print("Ending browser session...")
        interact.end_session()

if __name__ == "__main__":
    main() 