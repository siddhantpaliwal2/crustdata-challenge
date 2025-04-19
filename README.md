# Browser-AI: Natural Language Browser Automation

Control your browser with natural language commands through a simple API.

## Quick Start Guide

### Prerequisites

- Python 3.11 or 3.12 (not 3.13)
- OpenAI API key

### Installation

1. Clone this repository
2. Create a virtual environment (optional but recommended):
   ```
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   playwright install
   ```
4. Set your OpenAI API key:
   ```
   # Create a .env file with your API key
   echo "OPENAI_API_KEY=your_api_key_here" > .env
   ```

## Usage Options

### Option 1: REST API (Recommended)

Start the server:
```bash
python isolated_api_server.py
```

Then use curl to automate the browser:
```bash
# Start a browser session
curl -X POST http://localhost:5020/start -H "Content-Type: application/json" -d '{"headless": false}'

# Execute a command
curl -X POST http://localhost:5020/execute -H "Content-Type: application/json" -d '{"command": "Navigate to google.com"}'

# Stop the browser
curl -X POST http://localhost:5020/stop
```

### Option 2: Python API

```python
from browser_ai import InteractAPI

# Initialize and start session
interact = InteractAPI(headless=False)
interact.start_session()

# Execute commands
interact.execute("Navigate to google.com")
interact.execute("Search for Python programming")

# End session
interact.end_session()
```

### Option 3: Example Scripts

Run one of the example scripts:
```bash
python examples/dom_aware_amazon.py  # Amazon shopping with DOM awareness
python examples/inspect_dom.py       # Interactive DOM inspection tool
```

## Key Files

- `isolated_api_server.py` - REST API server
- `browser_ai/interact_api.py` - Core API implementation
- `examples/` - Example automation scripts

