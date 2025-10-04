# Taiwan ECMO CDSS - Test Suite

Comprehensive test suite for the Taiwan ECMO Clinical Decision Support System.

## Overview

This test suite provides comprehensive coverage of all project modules:
- **WP0**: Data dictionary and ELSO code mappings
- **SQL**: ECMO identification from MIMIC-IV
- **WP1**: NIRS+EHR risk models (VA/VV separation, calibration)
- **WP2**: Cost-effectiveness analysis
- **WP3**: VR training assessment
- **WP4**: SMART on FHIR integration

## Test Structure

```
tests/
├── conftest.py                 # Shared fixtures and utilities
├── test_nirs_models.py         # WP1: Risk model unit tests
├── test_cost_effectiveness.py  # WP2: CEA module tests
├── test_fhir_integration.py    # WP4: FHIR client tests
├── test_vr_training.py         # WP3: VR assessment tests
├── test_integration.py         # End-to-end integration tests
└── README.md                   # This file
```

## Running Tests

### Install Test Dependencies

```bash
pip install -r requirements.txt
```

### Run All Tests

```bash
# Run all tests with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=. --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_nirs_models.py -v

# Run specific test class
pytest tests/test_nirs_models.py::TestModelTraining -v

# Run specific test
pytest tests/test_nirs_models.py::TestModelTraining::test_fit_basic -v
```

### Run Tests by Category

```bash
# Unit tests only (fast)
pytest tests/ -m "not integration" -v

# Integration tests only
pytest tests/test_integration.py -v

# Mark slow tests to skip
pytest tests/ -m "not slow" -v
```

### Parallel Test Execution

```bash
# Run tests in parallel (requires pytest-xdist)
pytest tests/ -n auto
```

## Test Coverage

### Coverage Requirements

- **Statements**: >80%
- **Branches**: >75%
- **Functions**: >80%
- **Lines**: >80%

### View Coverage Report

```bash
# Generate HTML coverage report
pytest tests/ --cov=. --cov-report=html

# Open in browser
open htmlcov/index.html  # macOS
start htmlcov/index.html # Windows
```

## Test Categories

### Unit Tests

**test_nirs_models.py** - Risk Model Testing
- Model configuration and initialization
- Feature preparation and extraction
- Model training with class weights
- Calibrated predictions
- Feature importance
- APACHE-II stratification
- VA/VV separation

**test_cost_effectiveness.py** - CEA Testing
- Cost calculations (ICU, ward, ECMO)
- QALY computations
- CER/ICER calculations
- Quintile-stratified analysis
- CEAC generation
- Sensitivity analysis (1-way, 2-way)
- Probabilistic sensitivity analysis (PSA)
- Value of Information (VOI)
- Budget impact analysis
- Taiwan NHI calculations

**test_fhir_integration.py** - FHIR Client Testing
- Patient resource parsing
- Observation retrieval (NIRS, labs, vitals)
- Procedure and condition parsing
- Feature extraction from FHIR
- LOINC/SNOMED code mappings
- Pagination handling
- Error handling

**test_vr_training.py** - VR Assessment Testing
- Scenario loading from YAML
- Session scoring
- Decision point evaluation
- Performance reporting (text, JSON, HTML)
- Statistical analysis (group comparison, retention, correlation)
- Learning curve fitting
- Data model validation

### Integration Tests

**test_integration.py** - End-to-End Testing
- SQL → Features → Model pipeline
- Features → CEA pipeline
- Model → CEA → Report pipeline
- FHIR → Model integration
- VR → Outcomes integration
- Cross-module data consistency
- Performance and scalability
- Error handling and robustness

## Test Fixtures

### Synthetic Data Fixtures (conftest.py)

- `synthetic_ecmo_data`: 200 realistic ECMO patient records
- `synthetic_cea_data`: Quintile-stratified CEA data
- `synthetic_vr_scenarios`: VR training scenarios
- `synthetic_vr_log_data`: VR session logs
- `mock_fhir_server`: Mock FHIR server with test data

### Temporary Files

- `temp_sqlite_db`: Temporary SQLite database
- `temp_yaml_file`: Temporary YAML file
- `temp_output_dir`: Temporary output directory

### Utilities

- `assert_dataframe_schema()`: Validate DataFrame columns
- `assert_metric_in_range()`: Validate metric bounds
- `assert_probabilities_valid()`: Validate probability distributions

## Testing Best Practices

### 1. Test Organization

```python
class TestFeatureName:
    """Test specific feature."""

    def test_basic_functionality(self):
        """Test basic use case."""
        # Arrange
        data = create_test_data()

        # Act
        result = function_under_test(data)

        # Assert
        assert result == expected_value
```

### 2. Parametrized Tests

```python
@pytest.mark.parametrize("ecmo_mode", ["VA", "VV"])
def test_all_modes(ecmo_mode):
    """Test all ECMO modes."""
    config = ModelConfig(ecmo_mode=ecmo_mode)
    assert config.ecmo_mode == ecmo_mode
```

### 3. Fixtures for Reusability

```python
@pytest.fixture
def trained_model(synthetic_ecmo_data):
    """Provide pre-trained model."""
    model = ECMORiskModel(ModelConfig(ecmo_mode='VA'))
    X, y, features = model.prepare_features(synthetic_ecmo_data)
    model.fit(X, y, features)
    return model
```

### 4. Test Edge Cases

- Empty inputs
- Missing data
- Invalid parameters
- Boundary conditions
- Error states

### 5. Mocking External Dependencies

```python
from unittest.mock import Mock, patch

@patch('requests.get')
def test_api_call(mock_get):
    """Test with mocked API."""
    mock_get.return_value = Mock(json=lambda: {...})
    result = fetch_data()
    assert result is not None
```

## Continuous Integration

### GitHub Actions Workflow

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - run: pip install -r requirements.txt
      - run: pytest tests/ --cov=. --cov-report=xml
      - uses: codecov/codecov-action@v2
```

## Debugging Tests

### Run with PDB

```bash
# Drop into debugger on failure
pytest tests/ --pdb

# Drop into debugger on first failure
pytest tests/ -x --pdb
```

### Verbose Output

```bash
# Show print statements
pytest tests/ -s

# Very verbose
pytest tests/ -vv
```

### Filter Tests

```bash
# Run tests matching pattern
pytest tests/ -k "test_feature"

# Run tests NOT matching pattern
pytest tests/ -k "not slow"
```

## Performance Testing

### Profiling Tests

```bash
# Profile test execution time
pytest tests/ --durations=10

# Show slowest 20 tests
pytest tests/ --durations=20
```

### Memory Profiling

```bash
# Install memory profiler
pip install pytest-memprof

# Run with memory profiling
pytest tests/ --memprof
```

## Test Data

### Synthetic Data Characteristics

**ECMO Patient Data** (200 patients)
- 60% VA, 40% VV
- APACHE-II: 10-40
- Realistic NIRS values correlated with outcomes
- Survival probability based on APACHE, lactate, NIRS
- Length of stay distributions

**CEA Data** (200 patients, 5 quintiles)
- Risk-stratified outcomes (Q1: 65% survival → Q5: 25%)
- LOS increases with risk quintile
- Realistic cost distributions

**VR Training Data**
- Multiple scenarios with decision points
- Scoring rubrics
- Session logs with timing

**FHIR Test Data**
- Patient demographics
- NIRS observations
- Laboratory results
- ECMO procedures
- Conditions/diagnoses

## Common Issues

### Import Errors

```bash
# Ensure PYTHONPATH includes project root
export PYTHONPATH="${PYTHONPATH}:."

# Or use editable install
pip install -e .
```

### Missing Dependencies

```bash
# Install all test dependencies
pip install -r requirements.txt

# Install specific packages
pip install pytest pytest-cov
```

### FHIR Mock Issues

- Ensure `mock_fhir_server` fixture is imported
- Check patch targets match actual import paths
- Verify mock return values match FHIR spec

## Contributing

### Adding New Tests

1. Create test file: `test_<module>.py`
2. Import necessary modules and fixtures
3. Organize into test classes by feature
4. Follow naming convention: `test_<what_it_tests>`
5. Add docstrings explaining test purpose
6. Use fixtures from conftest.py
7. Run tests locally before committing

### Test Coverage Goals

- Every public function should have tests
- All edge cases should be covered
- Integration tests for workflows
- Performance tests for critical paths

## References

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [ELSO Registry](https://www.elso.org/)
- [FHIR R4 Specification](https://hl7.org/fhir/R4/)
- [MIMIC-IV Documentation](https://mimic.mit.edu/)

## License

Same as main project (see root LICENSE file).

## Contact

For questions about testing:
- Review test documentation
- Check existing tests for examples
- Open an issue in the project repository
