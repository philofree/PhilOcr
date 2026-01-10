# Configuration System Documentation

## Overview

PhilOcr uses a two-file configuration system to separate sensitive credentials from application settings:

1. **`settings.json`** - User credentials (sensitive, stored securely)
2. **`config.yaml`** - Application configuration (non-sensitive, human-readable)

Both files are stored in the user's configuration directory (outside the repository):
- **macOS**: `~/Library/Application Support/PhilOcr/`
- **Windows**: `%APPDATA%/PhilOcr/`
- **Linux**: `~/.config/philocr/`

## File Formats

### settings.json (JSON)
- **Purpose**: Store Google Cloud credentials
- **Format**: JSON (simple key-value pairs)
- **Permissions**: 600 (Unix) - readable/writable by owner only
- **Example**:
```json
{
  "credentials_path": "/absolute/path/to/credentials.json",
  "project_id": "your-project-id",
  "processor_id": "your-processor-id",
  "location": "eu"
}
```

### config.yaml (YAML)
- **Purpose**: Store application settings (non-sensitive)
- **Format**: YAML (allows comments, nested structures)
- **Fallback**: JSON if PyYAML not available
- **Permissions**: 600 (Unix) - readable/writable by owner only
- **Template**: See `config.yaml.template` in repository root

## Configuration Sections

### Processing Settings
```yaml
processing:
  max_pages_per_request: 15          # Google Document AI limit
  include_layout_info: true          # Include layout information
  rate_limit_requests_per_minute: 15 # API rate limit
  rate_limit_window_seconds: 60      # Rate limit window
```

### Memory Management
```yaml
memory:
  small_file_threshold_mb: 5         # Standard processing threshold
  medium_file_threshold_mb: 20       # Chunked processing threshold
  large_file_threshold_mb: 50        # Streaming processing threshold
  memory_check_threshold_mb: 100.0   # Warning threshold
```

### Formatting/Output Settings
```yaml
formatting:
  debug_mode: false                  # Enable debug output
  use_simple_formatting: true        # Simplified formatting
  html:
    font_family: "Arial, sans-serif"
    metadata_font_size: "12px"
    metadata_color: "#666"
    body_margin: "20px"
  thresholds:                        # For future advanced formatter
    indent_threshold: 0.06
    font_size_ratio_threshold: 0.85
    margin_left_threshold: 0.08
    margin_right_threshold: 0.92
```

### Markdown Converter Settings
```yaml
markdown:
  large_file_threshold_mb: 5         # Streaming parser threshold
  chunk_size_mb: 10                  # Chunk size for large files
```

### Error Handling/Retry Settings
```yaml
error_handling:
  max_retries: 3                     # Maximum retry attempts
  initial_delay_seconds: 1.0         # Initial retry delay
  max_delay_seconds: 60.0            # Maximum retry delay
  backoff_factor: 2.0                # Exponential backoff factor
```

### UI/Display Settings
```yaml
ui:
  default_window_width: 1000
  default_window_height: 800
  default_font_size: 14
  default_tab: "text"                # Options: text, markdown, html, json
```

## Usage in Code

### Loading Configuration

```python
from ocr_fresh.utils.config_manager import get_config_manager

# Get the config manager instance
config_manager = get_config_manager()

# Load all configuration
config = config_manager.load_config()

# Get a specific value using dot notation
max_pages = config_manager.get_config('processing.max_pages_per_request', 15)

# Set a value
config_manager.set_config('formatting.debug_mode', True)
```

### Using Configuration Values

```python
from ocr_fresh.utils.config_manager import get_config_manager

config = get_config_manager()

# Use in processing
max_pages = config.get_config('processing.max_pages_per_request', 15)
debug_mode = config.get_config('formatting.debug_mode', False)

# Use in memory management
large_threshold = config.get_config('memory.large_file_threshold_mb', 50)
```

## Initialization

On first run, if no config file exists:
1. Default configuration is loaded (from `get_default_config()`)
2. User can customize by editing the YAML file
3. Or use Settings UI (when implemented)

## Migration from Hardcoded Values

To migrate hardcoded configuration values:

1. Identify the value in code (e.g., `max_pages = 15`)
2. Add it to `get_default_config()` in `config_manager.py`
3. Update code to use `config_manager.get_config('processing.max_pages_per_request', 15)`
4. The default value (15) is used as fallback if config file doesn't exist

## Benefits

- ✅ **User Customizable**: Users can edit YAML without modifying code
- ✅ **Version Control Safe**: Config files stored outside repository
- ✅ **Human Readable**: YAML format with comments for documentation
- ✅ **Type Safe**: Supports nested structures and proper types
- ✅ **Graceful Fallback**: Works with JSON if PyYAML not available
- ✅ **Secure**: Config files have restrictive permissions (600)

## Dependencies

- **PyYAML** (optional but recommended): For YAML format support
  - Falls back to JSON if not available
  - Install with: `pip install pyyaml`
