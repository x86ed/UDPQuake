# COPILOT EDITS OPERATIONAL GUIDELINES

## PRIME DIRECTIVE

 Avoid working on more than one file at a time.
 Multiple simultaneous edits to a file will cause corruption.
 Be chatting and teach about what you are doing while coding.

## LARGE FILE & COMPLEX CHANGE PROTOCOL

### MANDATORY PLANNING PHASE

When working with large files (>300 lines) or complex changes:

1. ALWAYS start by creating a detailed plan BEFORE making any edits
2. Your plan MUST include:
    - All functions/sections that need modification
    - The order in which changes should be applied
    - Dependencies between changes
    - Estimated number of separate edits required

3. Format your plan as:

## PROPOSED EDIT PLAN

Working with: [filename]
Total planned edits: [number]

### MAKING EDITS

- Focus on one conceptual change at a time
- Show clear "before" and "after" snippets when proposing changes
- Include concise explanations of what changed and why
- Always check if the edit maintains the project's coding style

### Edit sequence:

1. [First specific change] - Purpose: [why]
2. [Second specific change] - Purpose: [why]
3. Do you approve this plan? I'll proceed with Edit [number] after your confirmation.
4. WAIT for explicit user confirmation before making ANY edits when user ok edit [number]

### EXECUTION PHASE

- After each individual edit, clearly indicate progress:
"✅ Completed edit [#] of [total]. Ready for next edit?"
- If you discover additional needed changes during editing:
- STOP and update the plan
- Get approval before continuing

### REFACTORING GUIDANCE

When refactoring large files:

- Break work into logical, independently functional chunks
- Ensure each intermediate state maintains functionality
- Consider temporary duplication as a valid interim step
- Always indicate the refactoring pattern being applied

### RATE LIMIT AVOIDANCE
	- For very large files, suggest splitting changes across multiple sessions
	- Prioritize changes that are logically complete units
	- Always provide clear stopping points
            
## General Requirements
	Use modern technologies as described below for all code suggestions. Prioritize clean, maintainable code with appropriate comments.
            
### Accessibility
	- Ensure compliance with **WCAG 2.1** AA level minimum, AAA whenever feasible.
	- Always suggest:
	- Labels for form fields.
	- Proper **ARIA** roles and attributes.
	- Adequate color contrast.
	- Alternative texts (`alt`, `aria-label`) for media elements.
	- Semantic HTML for clear structure.
	- Tools like **Lighthouse** for audits.
        
## Browser Compatibility
	- Prioritize feature detection (`if ('fetch' in window)` etc.).
        - Support latest two stable releases of major browsers:
	- Firefox, Chrome, Edge, Safari (macOS/iOS)
        - Emphasize progressive enhancement with polyfills or bundlers (e.g., **Babel**, **Vite**) as needed.
            
## Python Requirements
	- **Target Version**: Python 3.12 or higher
	- **Modern Features to Use**:
	- Type hints with generics and union types (`list[str]`, `str | None`)
	- Dataclasses and dataclass features
	- Match statements (structural pattern matching)
	- Walrus operator (`:=`) for assignment expressions
	- f-strings with format specifiers and debugging (`f"{var=}"`)
	- Context managers and `with` statements
	- Async/await for asynchronous operations
	- Pathlib for file system operations
	- Enums for constants and configuration
	- **Coding Standards**:
	- Follow PEP 8 style guidelines
	- Use type hints consistently throughout codebase
	- Prefer composition over inheritance
	- Use dependency injection patterns
	- Keep functions focused and single-purpose
	- Use descriptive variable and function names
	- **Package Management**:
	- Use **UV** for fast dependency management and virtual environments
	- Define dependencies in `pyproject.toml` with version constraints
	- Separate runtime and development dependencies
	- Pin major versions, allow minor/patch updates
	- **Type Checking & Static Analysis**:
	- Include comprehensive type hints compatible with **mypy**
	- Use `typing` module imports for advanced type annotations
	- Configure mypy with strict settings in `pyproject.toml`
	- Include docstring type information for complex return types
	- **Error Handling**:
	- Use specific exception types rather than generic `Exception`
	- Implement proper exception hierarchies for domain-specific errors
	- Provide clear, actionable error messages
	- Use logging instead of print statements for debugging
	- Handle network and I/O errors gracefully with retries where appropriate
	- **Testing Requirements**:
	- Use **pytest** for all test implementations
	- Achieve high test coverage (>90%) with **pytest-cov**
	- Mock external dependencies and network calls
	- Write both unit tests and integration tests
	- Use descriptive test names that explain the scenario being tested
	- **Code Quality Tools**:
	- Use **black** for consistent code formatting
	- Use **isort** for import organization
	- Use **mypy** for static type checking
	- Include pre-commit hooks for automated quality checks
            
## Folder Structure

Follow this Python package structure based on the UDPQuake repository:

		UDPQuake/
		├── .bumpversion.cfg      # Version management configuration
		├── .coverage             # Test coverage data
		├── .env                  # Environment variables (local config)
		├── .git/                 # Git repository data
		├── .github/              # GitHub-specific files
		│   └── copilot-instructions.md
		├── .gitignore            # Git ignore patterns
		├── .pytest_cache/        # Pytest cache directory
		├── .venv/                # Python virtual environment (UV managed)
		├── .vscode/              # VS Code workspace settings
		├── LICENSE               # GPL-3.0 license file
		├── README.md             # Main project documentation
		├── SoCal.json           # Sample earthquake data (for testing)
		├── __pycache__/         # Python bytecode cache
		├── htmlcov/             # HTML coverage reports
		├── pyproject.toml       # Python project configuration (UV/pip)
		├── src/                 # Source code directory
		│   └── udpquake/        # Main package directory
		│       ├── __init__.py  # Package initialization
		│       ├── __main__.py  # Module entry point (python -m udpquake)
		│       ├── earthquake_service.py  # USGS API integration
		│       ├── main.py      # Main application logic
		│       ├── mudp.py      # Meshtastic UDP protocol handler
		│       └── __pycache__/ # Package bytecode cache
		└── tests/               # Unit and integration tests
		    ├── __init__.py
		    ├── test_earthquake_service.py
		    ├── test_main_module.py
		    ├── test_main.py
		    ├── test_mudp.py
		    └── __pycache__/     # Test bytecode cache

### Key Directory Purposes:
- **src/udpquake/**: Main application package following PEP 518 source layout
- **tests/**: Comprehensive test suite with >90% coverage
- **pyproject.toml**: Modern Python packaging with UV dependency management
- **.env**: Local environment configuration (not committed to git)
- **htmlcov/**: Coverage reports for quality assurance
- **.github/**: GitHub-specific configuration and workflows

## Documentation Requirements

- **Python Docstrings**: Use comprehensive docstrings following PEP 257 conventions
- **Docstring Format**: Prefer Google-style or NumPy-style docstrings for consistency
- **Type Information**: Include type hints in function signatures, supplement with docstring details for complex types
- **Function Documentation**: Document all public functions, methods, and classes with:
  - Brief description of purpose
  - Args/Parameters with types and descriptions
  - Returns with type and description
  - Raises for documented exceptions
  - Examples for complex functionality
- **Module Documentation**: Include module-level docstrings explaining purpose and usage
- **Class Documentation**: Document class purpose, attributes, and usage patterns
- **Inline Comments**: Use for complex logic, algorithms, or non-obvious code sections
- **README Documentation**: Maintain comprehensive Markdown documentation for:
  - Installation and setup instructions
  - Configuration options
  - Usage examples
  - API reference
  - Troubleshooting guides
- **Code Examples**: Include working code examples in docstrings and README
- **pydoc Compatibility**: Ensure all docstrings work well with `python -m pydoc` for automatic documentation generation

### Example Documentation Format:
```python
def fetch_earthquakes(self, min_magnitude: float = 2.0, **kwargs) -> EarthquakeResponse:
    """
    Fetch earthquake data from USGS with configurable parameters.
    
    This method queries the USGS earthquake API and returns parsed earthquake
    data within the configured geographic boundaries.
    
    Args:
        min_magnitude: Minimum earthquake magnitude to include (default: 2.0)
        **kwargs: Additional query parameters:
            - start_time: ISO format start time
            - end_time: ISO format end time  
            - limit: Maximum number of results
            
    Returns:
        EarthquakeResponse: Parsed earthquake data with events and metadata
        
    Raises:
        ConnectionError: If unable to connect to USGS API
        ValueError: If response data is invalid or malformed
        
    Example:
        >>> service = EarthquakeService()
        >>> earthquakes = service.fetch_earthquakes(min_magnitude=3.0, limit=10)
        >>> print(f"Found {earthquakes.count} earthquakes")
    """
```

## Security Considerations

- Sanitize all user inputs thoroughly.
- Parameterize database queries.
- Enforce strong Content Security Policies (CSP).
- Use CSRF protection where applicable.
- Ensure secure cookies (`HttpOnly`, `Secure`, `SameSite=Strict`).
- Limit privileges and enforce role-based access control.
- Implement detailed internal logging and monitoring.