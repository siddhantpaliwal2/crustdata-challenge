import os
import json
import openai
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# load environment variables
load_dotenv()

# set up openai api key
openai.api_key = os.getenv("OPENAI_API_KEY")

class NLPEngine:
    """
    handles natural language processing using openai's api
    translates user commands into executable browser actions
    """
    
    def __init__(self):
        """initialize the nlp engine"""
        self.model = "gpt-4-turbo"  # using gpt-4 for better understanding of browser automation tasks
    
    def parse_command(self, command: str, browser_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        parse natural language command into executable actions
        
        args:
            command: user's natural language command
            browser_context: current state of the browser and DOM information (optional)
            
        returns:
            dictionary with action details
        """
        try:
            # create system message that instructs the model how to respond
            system_message = """
            You are a browser automation assistant that converts natural language commands into precise Playwright actions.
            
            You have DOM information from the current page that you should use to generate accurate selectors and actions.
            
            Return JSON with these fields:
            - action_type: navigate, click, fill, scroll, wait, back, forward, reload, screenshot, select, etc.
            - selector: CSS selector or XPath when applicable (make it as specific and reliable as possible)
            - value: Any value needed (URL, text input, etc.)
            - fallback_strategies: Array of alternative actions if the primary method fails
            
            When generating selectors:
            1. Prefer IDs (#element-id) when available
            2. Use text selectors when appropriate (button:has-text("Login"))
            3. Use data attributes for stability ([data-testid="search-input"])
            4. For forms, use label associations (form#login input[name="username"])
            5. When clicking, make sure you're targeting clickable elements (a, button, [role="button"], etc.)
            6. For navigation elements, look at the navigation info in the DOM snapshot
            
            For complex operations, return an "actions" array with multiple steps.
            
            Always check the DOM snapshot for accurate element information before generating selectors.
            
            Return ONLY valid JSON with no additional text.
            """
            
            # prepare the user message with enhanced browser context
            user_message = command
            
            if browser_context:
                # Filter and simplify DOM information to stay within token limits
                filtered_context = self._prepare_context_for_api(browser_context)
                context_json = json.dumps(filtered_context, ensure_ascii=False)
                user_message += f"\n\nCurrent browser context: {context_json}"
            
            # call openai api
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                response_format={"type": "json_object"}
            )
            
            # parse json response
            action_data = json.loads(response.choices[0].message.content)
            
            # validate response has required fields
            if "action_type" not in action_data and "actions" not in action_data:
                raise ValueError("Action type or actions array missing from API response")
                
            return action_data
            
        except Exception as e:
            # handle errors gracefully
            error_msg = f"Failed to parse command: {str(e)}"
            return {
                "action_type": "error",
                "error": error_msg
            }
    
    def _prepare_context_for_api(self, browser_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        prepare and filter browser context to fit within token limits
        
        args:
            browser_context: full browser context including DOM snapshot
            
        returns:
            filtered context suitable for API consumption
        """
        filtered_context = {}
        
        # extract essential page state info
        if "page_state" in browser_context:
            page_state = browser_context["page_state"]
            filtered_context["page_info"] = {
                "url": page_state.get("url", ""),
                "title": page_state.get("title", "")
            }
            
            # include preview of text content if available
            if "text_preview" in page_state:
                text_preview = page_state["text_preview"]
                # truncate if too long
                if len(text_preview) > 500:
                    text_preview = text_preview[:500] + "..."
                filtered_context["page_info"]["text_preview"] = text_preview
        
        # extract essential DOM elements
        if "dom_snapshot" in browser_context and browser_context["dom_snapshot"]:
            dom_snapshot = browser_context["dom_snapshot"]
            
            # include metadata
            if "metadata" in dom_snapshot:
                filtered_context["metadata"] = dom_snapshot["metadata"]
            
            # include interactive elements (limited to most relevant)
            if "interactive_elements" in dom_snapshot:
                interactive_elements = dom_snapshot["interactive_elements"]
                # sort by y position to prioritize elements at the top of the page
                interactive_elements.sort(key=lambda x: x.get("rect", {}).get("y", 1000))
                # limit to 30 most relevant elements
                filtered_context["interactive_elements"] = interactive_elements[:30]
            
            # include navigation info
            if "navigation" in dom_snapshot:
                navigation = dom_snapshot["navigation"]
                if navigation:
                    # limit to first 3 navigation areas
                    filtered_context["navigation"] = navigation[:3]
            
            # include form elements
            if "form_elements" in dom_snapshot:
                form_elements = dom_snapshot["form_elements"]
                if form_elements:
                    # limit to first 3 forms
                    filtered_context["forms"] = form_elements[:3]
        
        return filtered_context
            
    def generate_fallback_strategies(self, action: Dict[str, Any], error_message: str) -> List[Dict[str, Any]]:
        """
        generate fallback strategies when an action fails
        
        args:
            action: the failed action
            error_message: the error that occurred
            
        returns:
            list of alternative actions to try
        """
        try:
            system_message = """
            You are a browser automation troubleshooter. Given a failed browser action and an error message,
            suggest 2-3 alternative approaches to accomplish the same task.
            
            Consider these common failure patterns:
            1. Selector not found - Try different selector strategies (ID, text, aria-label, etc.)
            2. Element not visible - Try waiting longer or scrolling to make the element visible
            3. Timing issues - Add explicit waits before the action
            4. Dynamic IDs - Use more stable attributes like data-* attributes, text content, or relative positions
            5. Popup/overlay interference - Look for and dismiss any popups first
            
            For each alternative, provide:
            - action_type: The Playwright action to perform (click, fill, etc.)
            - selector: A different selector strategy than the original
            - value: Any value needed (same as original or modified if needed)
            - description: Brief explanation of this alternative approach
            
            Return a JSON array of these alternatives.
            Return ONLY valid JSON with no additional text.
            """
            
            user_message = f"""
            Failed action: {json.dumps(action, ensure_ascii=False)}
            Error message: {error_message}
            
            Suggest alternative approaches.
            """
            
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                response_format={"type": "json_object"}
            )
            
            fallbacks = json.loads(response.choices[0].message.content)
            if "alternatives" in fallbacks:
                return fallbacks["alternatives"]
            elif isinstance(fallbacks, list):
                return fallbacks
            else:
                # if response doesn't match expected format, wrap it
                return [fallbacks]
            
        except Exception as e:
            # return empty list if error occurs
            return [] 