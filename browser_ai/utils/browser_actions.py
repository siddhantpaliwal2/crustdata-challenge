from typing import Dict, Any, Optional, Tuple, List
from playwright.sync_api import Page, ElementHandle
import time
import logging
import json

# set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BrowserActions:
    """
    implements common browser actions using playwright
    """
    
    @staticmethod
    def navigate(page: Page, action: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        navigate to a url
        
        args:
            page: playwright page object
            action: action dictionary with navigation details
            
        returns:
            tuple of (success, error_message)
        """
        try:
            url = action.get("value", "")
            # ensure url has http/https prefix
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
                
            # navigate to the url
            page.goto(url)
            # wait for network idle to ensure page is loaded
            page.wait_for_load_state("networkidle")
            return True, None
        except Exception as e:
            error_msg = f"Navigation failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    @staticmethod
    def click(page: Page, action: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        click on an element
        
        args:
            page: playwright page object
            action: action dictionary with click details
            
        returns:
            tuple of (success, error_message)
        """
        try:
            selector = action.get("selector", "")
            if not selector:
                return False, "No selector provided for click action"
                
            # wait for the element to be visible
            page.wait_for_selector(selector, state="visible", timeout=10000)
            # click the element
            page.click(selector)
            return True, None
        except Exception as e:
            error_msg = f"Click failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    @staticmethod
    def fill(page: Page, action: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        fill a form field
        
        args:
            page: playwright page object
            action: action dictionary with fill details
            
        returns:
            tuple of (success, error_message)
        """
        try:
            selector = action.get("selector", "")
            value = action.get("value", "")
            
            if not selector:
                return False, "No selector provided for fill action"
                
            # wait for the element to be visible
            page.wait_for_selector(selector, state="visible", timeout=10000)
            # fill the element
            page.fill(selector, value)
            return True, None
        except Exception as e:
            error_msg = f"Fill failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    @staticmethod
    def wait(page: Page, action: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        wait for specified amount of time or for an element
        
        args:
            page: playwright page object
            action: action dictionary with wait details
            
        returns:
            tuple of (success, error_message)
        """
        try:
            # get wait type and value
            wait_type = action.get("wait_type", "time")
            value = action.get("value", 5000)  # default 5 seconds
            
            if wait_type == "time":
                # convert to milliseconds if it's a number
                try:
                    value_ms = int(value)
                except ValueError:
                    value_ms = 5000  # default if conversion fails
                # wait for specified time
                time.sleep(value_ms / 1000)
                return True, None
            elif wait_type == "selector":
                # wait for element to be visible
                selector = action.get("selector", "")
                if not selector:
                    return False, "No selector provided for element wait"
                page.wait_for_selector(selector, state="visible", timeout=int(value))
                return True, None
            elif wait_type == "navigation":
                # wait for navigation to complete
                page.wait_for_load_state("networkidle")
                return True, None
            else:
                return False, f"Unknown wait type: {wait_type}"
        except Exception as e:
            error_msg = f"Wait failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    @staticmethod
    def scroll(page: Page, action: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        scroll the page
        
        args:
            page: playwright page object
            action: action dictionary with scroll details
            
        returns:
            tuple of (success, error_message)
        """
        try:
            direction = action.get("direction", "down")
            selector = action.get("selector", None)
            
            if selector:
                # scroll the specific element into view
                element = page.query_selector(selector)
                if element:
                    element.scroll_into_view_if_needed()
                else:
                    return False, f"Element with selector '{selector}' not found"
            else:
                # scroll the entire page
                if direction == "down":
                    page.evaluate("window.scrollBy(0, window.innerHeight)")
                elif direction == "up":
                    page.evaluate("window.scrollBy(0, -window.innerHeight)")
                elif direction == "top":
                    page.evaluate("window.scrollTo(0, 0)")
                elif direction == "bottom":
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                else:
                    return False, f"Unknown scroll direction: {direction}"
            
            return True, None
        except Exception as e:
            error_msg = f"Scroll failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    @staticmethod
    def back(page: Page, action: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        navigate back in browser history
        
        args:
            page: playwright page object
            action: action dictionary
            
        returns:
            tuple of (success, error_message)
        """
        try:
            page.go_back()
            page.wait_for_load_state("networkidle")
            return True, None
        except Exception as e:
            error_msg = f"Back navigation failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    @staticmethod
    def forward(page: Page, action: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        navigate forward in browser history
        
        args:
            page: playwright page object
            action: action dictionary
            
        returns:
            tuple of (success, error_message)
        """
        try:
            page.go_forward()
            page.wait_for_load_state("networkidle")
            return True, None
        except Exception as e:
            error_msg = f"Forward navigation failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    @staticmethod
    def reload(page: Page, action: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        reload the current page
        
        args:
            page: playwright page object
            action: action dictionary
            
        returns:
            tuple of (success, error_message)
        """
        try:
            page.reload()
            page.wait_for_load_state("networkidle")
            return True, None
        except Exception as e:
            error_msg = f"Page reload failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    @staticmethod
    def screenshot(page: Page, action: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        take a screenshot of the page
        
        args:
            page: playwright page object
            action: action dictionary with screenshot details
            
        returns:
            tuple of (success, error_message)
        """
        try:
            path = action.get("value", "screenshot.png")
            page.screenshot(path=path)
            return True, None
        except Exception as e:
            error_msg = f"Screenshot failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    @staticmethod
    def select(page: Page, action: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        select an option from a dropdown
        
        args:
            page: playwright page object
            action: action dictionary with select details
            
        returns:
            tuple of (success, error_message)
        """
        try:
            selector = action.get("selector", "")
            value = action.get("value", "")
            
            if not selector:
                return False, "No selector provided for select action"
            if not value:
                return False, "No value provided for select action"
                
            # wait for the element to be visible
            page.wait_for_selector(selector, state="visible", timeout=10000)
            # select the option
            page.select_option(selector, value)
            return True, None
        except Exception as e:
            error_msg = f"Select failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
            
    @staticmethod
    def get_page_state(page: Page) -> Dict[str, Any]:
        """
        get current state of the page
        
        args:
            page: playwright page object
            
        returns:
            dictionary with page state information
        """
        try:
            state = {
                "url": page.url,
                "title": page.title(),
                "viewport": page.viewport_size,
            }
            
            # get visible text content (could be large)
            text_content = page.evaluate("""() => {
                return document.body.innerText.substring(0, 1000) + 
                       (document.body.innerText.length > 1000 ? '...' : '');
            }""")
            state["text_preview"] = text_content
            
            return state
        except Exception as e:
            logger.error(f"Failed to get page state: {str(e)}")
            return {"error": str(e)}
            
    @staticmethod
    def get_browser_info(page: Page) -> Dict[str, Any]:
        """
        get browser information
        
        args:
            page: playwright page object
            
        returns:
            dictionary with browser information
        """
        try:
            user_agent = page.evaluate("() => navigator.userAgent")
            platform = page.evaluate("() => navigator.platform")
            
            return {
                "user_agent": user_agent,
                "platform": platform
            }
        except Exception as e:
            logger.error(f"Failed to get browser info: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    def dom_snapshot(page: Page, action: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        take a detailed snapshot of the dom structure for better element targeting
        
        args:
            page: playwright page object
            action: action dictionary with optional parameters
            
        returns:
            tuple of (success, dom_snapshot_data)
        """
        try:
            # extract interactive elements (links, buttons, inputs, etc.)
            interactive_elements = page.evaluate("""() => {
                const getSelector = (el) => {
                    // try to create a unique and robust selector
                    if (el.id) return `#${el.id}`;
                    
                    // try data attributes which are often good identifiers
                    for (const attr of el.attributes) {
                        if (attr.name.startsWith('data-') && attr.value) {
                            return `[${attr.name}="${attr.value}"]`;
                        }
                    }
                    
                    // try with classes but be careful with dynamic classes
                    if (el.className && typeof el.className === 'string' && el.className.length < 50) {
                        const classes = Array.from(el.classList)
                            .filter(c => !c.includes('--') && c.length > 2 && !c.match(/^[0-9]/));
                        if (classes.length > 0) {
                            return `${el.tagName.toLowerCase()}.${classes.join('.')}`;
                        }
                    }
                    
                    // use text content for buttons and links
                    const text = el.innerText || el.textContent;
                    if (text && text.trim() && text.length < 50) {
                        // for exact text matching
                        return `${el.tagName.toLowerCase()}:has-text("${text.trim().replace(/"/g, '\\"')}")`;
                    }
                    
                    // fallback to tag name (less specific)
                    return el.tagName.toLowerCase();
                };
                
                // get element visibility
                const isVisible = (el) => {
                    if (!el.getBoundingClientRect) return false;
                    
                    const rect = el.getBoundingClientRect();
                    return (
                        rect.top >= 0 &&
                        rect.left >= 0 &&
                        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
                        rect.right <= (window.innerWidth || document.documentElement.clientWidth) &&
                        rect.width > 0 &&
                        rect.height > 0 &&
                        window.getComputedStyle(el).visibility !== 'hidden' &&
                        window.getComputedStyle(el).display !== 'none'
                    );
                };
                
                // find all interactive elements
                const elements = Array.from(document.querySelectorAll(
                    'a, button, input, select, textarea, [role="button"], [role="link"], [role="checkbox"], ' + 
                    '[role="radio"], [role="tab"], [role="menuitem"], [tabindex="0"], [type="submit"]'
                ));
                
                return elements
                    .filter(el => isVisible(el))
                    .map((el, index) => {
                        // get ancestor that might be a container
                        let container = el.closest('[class*="container"], [class*="wrapper"], [class*="item"], [class*="card"]');
                        let containerSelector = container && container !== el ? getSelector(container) : null;
                        
                        return {
                            index,
                            tagName: el.tagName.toLowerCase(),
                            type: el.type || el.getAttribute('role') || el.tagName.toLowerCase(),
                            text: (el.innerText || el.textContent || '').trim().substring(0, 100),
                            placeholder: el.placeholder || '',
                            name: el.name || '',
                            id: el.id || '',
                            href: el.href || '',
                            value: el.value || '',
                            selector: getSelector(el),
                            ariaLabel: el.getAttribute('aria-label') || '',
                            ariaExpanded: el.getAttribute('aria-expanded') || '',
                            containerSelector,
                            attributes: Array.from(el.attributes)
                                .filter(attr => !['style', 'class', 'id'].includes(attr.name))
                                .map(attr => ({ name: attr.name, value: attr.value })),
                            rect: {
                                x: Math.round(el.getBoundingClientRect().x),
                                y: Math.round(el.getBoundingClientRect().y),
                                width: Math.round(el.getBoundingClientRect().width),
                                height: Math.round(el.getBoundingClientRect().height)
                            }
                        };
                    });
            }""")
            
            # capture form elements for better form filling capabilities
            form_elements = page.evaluate("""() => {
                const forms = Array.from(document.querySelectorAll('form'));
                return forms.map(form => {
                    const inputs = Array.from(form.querySelectorAll('input, textarea, select'));
                    return {
                        id: form.id || '',
                        name: form.name || '',
                        action: form.action || '',
                        method: form.method || '',
                        elements: inputs.map(input => {
                            return {
                                tagName: input.tagName.toLowerCase(),
                                type: input.type || '',
                                name: input.name || '',
                                id: input.id || '',
                                placeholder: input.placeholder || '',
                                value: input.value || '',
                                required: input.required || false,
                                label: input.labels && input.labels.length > 0 
                                    ? (input.labels[0].innerText || input.labels[0].textContent || '').trim() 
                                    : ''
                            };
                        })
                    };
                });
            }""")
            
            # extract main content areas
            content_areas = page.evaluate("""() => {
                // look for common content container patterns
                const contentSelectors = [
                    'main', '#main', '[role="main"]', '.main-content', '#content', '.content',
                    'article', '.container', '.page-content', '#root > div', 'body > div'
                ];
                
                const results = [];
                for (const selector of contentSelectors) {
                    const elements = document.querySelectorAll(selector);
                    if (elements.length > 0) {
                        for (const el of elements) {
                            // only include if it has substantial content
                            if (el.offsetWidth > 200 && el.offsetHeight > 200) {
                                results.push({
                                    selector,
                                    id: el.id || '',
                                    classList: Array.from(el.classList || []),
                                    textLength: (el.innerText || '').length,
                                    childrenCount: el.children.length,
                                    rect: {
                                        width: el.offsetWidth,
                                        height: el.offsetHeight
                                    }
                                });
                            }
                        }
                    }
                }
                return results;
            }""")
            
            # extract navigation elements
            navigation = page.evaluate("""() => {
                const navSelectors = [
                    'nav', '[role="navigation"]', 'header', '#header', '.header', 
                    '.navigation', '#nav', '.nav', '.navbar'
                ];
                
                const results = [];
                for (const selector of navSelectors) {
                    const elements = document.querySelectorAll(selector);
                    if (elements.length > 0) {
                        for (const nav of elements) {
                            const links = Array.from(nav.querySelectorAll('a, button, [role="link"]'));
                            results.push({
                                selector,
                                id: nav.id || '',
                                classList: Array.from(nav.classList || []),
                                links: links.map(link => ({
                                    text: (link.innerText || link.textContent || '').trim(),
                                    href: link.href || '',
                                    ariaLabel: link.getAttribute('aria-label') || ''
                                })).filter(l => l.text || l.href || l.ariaLabel)
                            });
                        }
                    }
                }
                return results;
            }""")
            
            # extract page metadata
            metadata = page.evaluate("""() => {
                return {
                    title: document.title,
                    url: window.location.href,
                    metaDescription: document.querySelector('meta[name="description"]')?.content || '',
                    h1: Array.from(document.querySelectorAll('h1')).map(h => h.innerText.trim()),
                    h2: Array.from(document.querySelectorAll('h2')).map(h => h.innerText.trim()).slice(0, 5)
                };
            }""")
            
            snapshot_data = {
                "interactive_elements": interactive_elements,
                "form_elements": form_elements,
                "content_areas": content_areas,
                "navigation": navigation,
                "metadata": metadata,
                "url": page.url,
                "title": page.title()
            }
            
            return True, snapshot_data
            
        except Exception as e:
            error_msg = f"DOM snapshot failed: {str(e)}"
            logger.error(error_msg)
            return False, {"error": error_msg} 