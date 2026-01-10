# Settings Manager Implementation

## Summary

This branch implements a secure settings management system that removes all hardcoded credentials and allows users to configure Google Cloud credentials through a built-in Settings dialog.

## Changes Made

### 1. New Settings Manager (`src/ocr_fresh/utils/settings_manager.py`)
- Stores settings in user config directory (not in repository)
- Platform-specific locations:
  - macOS: `~/Library/Application Support/PhilOcr/settings.json`
  - Windows: `%APPDATA%/PhilOcr/settings.json`
  - Linux: `~/.config/philocr/settings.json`
- Secure file permissions (600 on Unix systems)
- Settings persist across application restarts

### 2. Updated Environment Utilities (`src/ocr_fresh/utils/env_utils.py`)
- Now loads settings from user settings first, then falls back to ENV.local
- Removed hardcoded credential filename reference
- Maintains backward compatibility with ENV.local files

### 3. Enhanced Credentials Dialog (`src/ocr_fresh/ui/dialogs.py`)
- Now saves settings to the settings manager
- Validates required fields before saving
- Shows confirmation messages
- Automatically updates environment variables for current session

### 4. Main Window Integration (`src/ocr_fresh/ui/main_window.py`)
- Added "Settings" button in header
- Integrated settings dialog
- Configuration warning now offers to open settings dialog
- Automatically reloads settings after changes

### 5. Test Updates (`tests/test_package.py`)
- Removed hardcoded credential filename from test
- Tests now focus on optional ENV.local for backward compatibility

### 6. Migration Script (`migrate_settings.py`)
- Migrates existing ENV.local settings to new system
- Can be run to transfer current configuration

## Testing

Your current settings have been migrated:
- ✅ Settings saved to: `/Users/james/Library/Application Support/PhilOcr/settings.json`
- ✅ Settings load correctly
- ✅ Environment variables are set from settings
- ✅ No hardcoded references remain in source code

## Next Steps

1. **Test the application**: Run the app and verify it works with the new settings system
2. **Test Settings Dialog**: Click the "Settings" button and verify you can view/edit settings
3. **Verify Processing**: Test that document processing still works with migrated settings

## For Public Sharing

Before making this repository public:

1. ✅ Hardcoded credentials removed
2. ✅ Settings stored outside repository
3. ✅ User-friendly settings dialog implemented
4. ⚠️  Consider making credentials_path absolute (currently relative)
5. ⚠️  Remove or update ENV.local (contains sensitive data)
6. ⚠️  Remove secrets/ directory from repository
7. ⚠️  Update README with new settings instructions

## Docker Considerations

For future dockerization:
- Settings can be mounted as volume or passed via environment variables
- Settings manager can be configured to use different paths
- Consider supporting both file-based and environment variable configuration
