# Pipeline Tests

Comprehensive test suite for the PhilOcr advanced pipeline implementation.

## Test Structure

### Unit Tests

- **`test_models_config.py`**: Tests for `PipelineConfig` dataclass
- **`test_detection_profiles.py`**: Tests for projection profile utilities (`find_gaps`, `Gap`)
- **`test_detection_zones.py`**: Tests for zone detection functions (header, footer, margins)
- **`test_utils_deskew.py`**: Tests for deskewing utilities
- **`test_utils_image_io.py`**: Tests for image I/O operations
- **`test_stage1_normalise.py`**: Tests for Stage 1 (PDF to normalized PNG)
- **`test_stage2_template.py`**: Tests for Stage 2b (template extraction)

### Integration Tests

- **`test_integration.py`**: End-to-end pipeline integration tests

## Running Tests

Run all pipeline tests:
```bash
pytest tests/pipeline/ -v
```

Run specific test file:
```bash
pytest tests/pipeline/test_models_config.py -v
```

Run with markers:
```bash
# Unit tests only
pytest tests/pipeline/ -m unit -v

# Integration tests only
pytest tests/pipeline/ -m integration -v
```

## Test Coverage

The test suite covers:
- ✅ Configuration management
- ✅ Image processing utilities (deskew, I/O)
- ✅ Zone detection algorithms
- ✅ Template extraction with robust statistics
- ✅ Individual pipeline stages
- ✅ End-to-end pipeline integration

## Fixtures

Shared fixtures in `conftest.py`:
- `default_config`: Default `PipelineConfig`
- `sample_page_image`: Sample `PageImage` object
- `sample_page_zones`: Sample `PageZones` object
- `sample_image_array`: Sample numpy image array
- `mock_pdf_file`: Mock PDF file path

## Future Test Additions

Planned additions:
- Stage 2a (zone detection) detailed tests
- Stage 2c (masking/cropping) tests
- Stage 3 (OCR) tests with Document AI mocking
- Stage 4 (assembly) tests
- UI component tests
- Performance/benchmark tests
