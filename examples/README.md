#!/usr/bin/env python3
"""
ImaLink Python Demos

Simple Python scripts for demonstrating the ImaLink API without complex dependencies.
"""

# Demo Scripts

## health_demo.py
Basic health check demo to verify the server is running.

**Usage:**
```bash
cd /home/kjell/git_prosjekt/imalink/fase1
uv run python python_demos/health_demo.py
```

## author_demo.py  
Complete Author CRUD operations demo:
- List authors
- Create author
- Get author by ID
- Update author
- Delete author

**Usage:**
```bash
cd /home/kjell/git_prosjekt/imalink/fase1
uv run python python_demos/author_demo.py
```

## api_demo_suite.py
Comprehensive demo of all API endpoints with success/failure tracking.

**Usage:**
```bash
cd /home/kjell/git_prosjekt/imalink/fase1
uv run python python_demos/api_demo_suite.py
```

## cli_tester.py
Command-line demo tool for API automation and bulk operations.

**Usage:**
```bash
cd /home/kjell/git_prosjekt/imalink/fase1
uv run python python_demos/cli_tester.py
```

## run_all_demos.py
Run all demo scripts in sequence for complete API demonstration.

**Usage:**
```bash
cd /home/kjell/git_prosjekt/imalink/fase1
uv run python python_demos/run_all_demos.py
```

## Prerequisites

1. **Start the FastAPI server:**
   ```bash
   cd /home/kjell/git_prosjekt/imalink/fase1/src
   uv run python main.py
   ```

2. **Run any test:**
   ```bash
   cd /home/kjell/git_prosjekt/imalink/fase1
   uv run python python_demos/<test_name>.py
   ```

## Features

- ✅ Simple stdout output
- ✅ No complex dependencies (just requests)
- ✅ Clear success/failure indicators
- ✅ JSON pretty printing
- ✅ Error handling
- ✅ Exit codes for automation
- ✅ Timestamps and logging