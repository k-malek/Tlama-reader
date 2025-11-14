# Tlama Reader

A project for calling Tlama games.

## Website Caller Utility

A simple utility class for making HTTP requests to websites by URL.

### Installation

#### Using pip

```bash
pip install -e .
```

Or install dependencies only:

```bash
pip install .
```

#### Using uv

**Recommended:** Sync the project (creates virtual environment and installs dependencies):

```bash
uv sync
```

This will create a virtual environment at `.venv` and install all dependencies automatically.

Run scripts directly with uv:

```bash
uv run python main.py
```

Or activate the virtual environment and use Python normally:

```bash
source .venv/bin/activate  # On macOS/Linux
python main.py
```

**Alternative:** Install in editable mode (requires venv first):

```bash
uv venv  # Create venv first
uv pip install -e .
```

### Usage

```python
from website_caller import WebsiteCaller

# Create a caller instance
caller = WebsiteCaller(timeout=10)

# Simple GET request
response = caller.get("https://example.com")
print(response.status_code)
print(response.text)

# GET with query parameters
response = caller.get("https://api.example.com/data", params={"key": "value"})

# GET JSON response
data = caller.get_json("https://api.example.com/json")

# GET text response
text = caller.get_text("https://example.com")

# POST request with JSON
response = caller.post("https://api.example.com/endpoint", json={"name": "value"})

# POST request with form data
response = caller.post("https://api.example.com/endpoint", data={"field": "value"})

# Custom headers
response = caller.get("https://example.com", headers={"User-Agent": "MyApp/1.0"})

# Generic call method
response = caller.call("https://example.com", method="GET")

# Clean up
caller.close()
```

### Example

Run the example script:

```bash
python example.py
```
