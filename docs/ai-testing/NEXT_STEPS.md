# OmniParser AI Features - Next Steps Action Plan

**Status:** Integration tests created, initial run complete with 69% pass rate
**Current Coverage:** 32% for AI modules (215/668 statements tested)
**Target Coverage:** 80%+ for production readiness
**Last Updated:** 2025-10-29

---

## 📊 Executive Summary

### What We Accomplished ✅
- Created 39 comprehensive integration tests across 3 test files
- Added 10 diverse test images (photos, diagrams, charts)
- Validated core AI features: tagging, summarization, quality scoring
- Confirmed vision API integration works with Claude Haiku
- Established baseline coverage metrics for all AI modules

### What Needs Fixing 🔧
- **6 image description tests failing** (API contract mismatch)
- **1 retry logic test failing** (invalid API key handling)
- **17% coverage on ai_image_describer** (most code untested)
- **Various coverage gaps** across all AI modules (32% overall)

### Priority Breakdown
- 🔴 **Critical:** Fix failing tests (7 tests, ~2-3 hours)
- 🟡 **High:** Increase coverage to 60%+ (~1-2 days)
- 🟢 **Medium:** Achieve 80%+ coverage (~3-5 days)
- 🔵 **Low:** Add advanced features and edge cases (~1 week)

---

## 🚨 PHASE 1: Critical Fixes (Immediate - 2-3 hours)

**Goal:** Get all integration tests passing (27/39 → 39/39)

### Task Group 1.1: Fix Image Description Test Failures (6 tests)

**Problem:** Tests expect dict-like results but get `ImageAnalysis` dataclass
**Location:** `tests/integration/test_ai_vision_integration.py`
**Estimated Time:** 30 minutes per test (3 hours total)

#### Task 1.1.1: Fix `test_describe_single_image_anthropic`
```yaml
File: tests/integration/test_ai_vision_integration.py
Lines: ~290-310
Error: AttributeError: 'PosixPath' has no 'file_path'
Issue: Test passing Path object instead of string, expecting dict instead of dataclass
Fix:
  - Convert Path to string: str(image_path)
  - Change assertions from dict to dataclass attributes
  - Example: result["description"] → result.description
Subagent: house-coder
Complexity: Simple (0-50 lines changed)
```

#### Task 1.1.2: Fix `test_describe_image_with_context`
```yaml
File: tests/integration/test_ai_vision_integration.py
Lines: ~312-330
Error: Same as 1.1.1
Issue: Same as 1.1.1
Fix: Same pattern as 1.1.1
Subagent: house-coder
Complexity: Simple (0-50 lines changed)
```

#### Task 1.1.3: Fix `test_describe_document_images_batch`
```yaml
File: tests/integration/test_ai_vision_integration.py
Lines: ~332-355
Error: TypeError: unexpected keyword 'width'
Issue: ImageReference initialization with wrong parameters
Fix:
  - Check ImageReference dataclass definition
  - Update test to use correct parameters (size tuple instead of width/height)
  - Example: ImageReference(width=800, height=600) → ImageReference(size=(800, 600))
Subagent: house-coder
Complexity: Simple (0-50 lines changed)
```

#### Task 1.1.4: Fix `test_update_image_descriptions_in_document`
```yaml
File: tests/integration/test_ai_vision_integration.py
Lines: ~357-380
Error: Same as 1.1.3
Issue: ImageReference parameter mismatch
Fix: Same pattern as 1.1.3
Subagent: house-coder
Complexity: Simple (0-50 lines changed)
```

#### Task 1.1.5: Fix `test_describe_image_error_handling`
```yaml
File: tests/integration/test_ai_vision_integration.py
Lines: ~382-398
Error: AttributeError on Path object
Issue: Path object handling
Fix: Convert Path to string before passing to describe_image()
Subagent: house-coder
Complexity: Simple (0-50 lines changed)
```

#### Task 1.1.6: Fix `test_vision_capable_model_works`
```yaml
File: tests/integration/test_ai_vision_integration.py
Lines: ~420-438
Error: TypeError: ImageAnalysis not iterable
Issue: Test trying to iterate over dataclass
Fix:
  - Check what the test is trying to iterate
  - Fix to access dataclass attributes correctly
  - Remove any dict-like iteration patterns
Subagent: house-coder
Complexity: Simple (0-50 lines changed)
```

### Task Group 1.2: Fix Retry Logic Test Failure (1 test)

#### Task 1.2.1: Fix `test_invalid_api_key_no_retry`
```yaml
File: tests/integration/test_ai_retry_integration.py
Lines: ~104-135
Error: Did not raise expected Exception
Issue: Invalid API key test not triggering authentication error
Fix:
  - Add explicit error injection/mocking
  - Test the _is_retriable_error() method directly with 401 errors
  - Consider splitting into two tests: one for error classification, one for no-retry behavior
Subagent: house-coder
Complexity: Medium (50-150 lines changed)
Alternative: Skip this test if it's testing external API behavior unreliably
```

---

## 🟡 PHASE 2: High Priority Coverage Improvements (1-2 days)

**Goal:** Increase coverage from 32% → 60%+ by adding unit tests with mocked responses

### Task Group 2.1: Add Unit Tests for ai_image_describer (17% → 70%)

**Current:** 17% coverage (18/106 statements)
**Target:** 70% coverage (~74/106 statements)
**Gap:** 88 statements untested

#### Task 2.1.1: Add unit tests for describe_image() function
```yaml
File: tests/unit/test_ai_image_describer.py (NEW FILE)
Function: describe_image()
Coverage Gap: Lines 152-180, 195-220
Tests Needed:
  - test_describe_image_with_anthropic_mock
  - test_describe_image_with_openai_mock
  - test_describe_image_with_ollama_mock
  - test_describe_image_with_context
  - test_describe_image_without_context
  - test_describe_image_truncates_long_descriptions
Mock: AIConfig.generate() to return sample descriptions
Lines: ~100 lines of test code
Subagent: house-coder
Complexity: Medium (100-200 lines)
```

#### Task 2.1.2: Add unit tests for describe_document_images()
```yaml
File: tests/unit/test_ai_image_describer.py
Function: describe_document_images()
Coverage Gap: Lines 228-267
Tests Needed:
  - test_describe_document_images_all_images
  - test_describe_document_images_with_context_extraction
  - test_describe_document_images_empty_document
  - test_describe_document_images_no_images
Mock: describe_image() to return sample descriptions
Lines: ~80 lines of test code
Subagent: house-coder
Complexity: Medium (50-150 lines)
```

#### Task 2.1.3: Add unit tests for _describe_image_anthropic()
```yaml
File: tests/unit/test_ai_image_describer.py
Function: _describe_image_anthropic()
Coverage Gap: Lines 275-305
Tests Needed:
  - test_anthropic_vision_api_call_structure
  - test_anthropic_response_parsing
  - test_anthropic_error_handling
Mock: anthropic.Anthropic client
Lines: ~60 lines of test code
Subagent: house-coder
Complexity: Medium (50-150 lines)
```

#### Task 2.1.4: Add unit tests for _get_image_context()
```yaml
File: tests/unit/test_ai_image_describer.py
Function: _get_image_context()
Coverage Gap: Lines 315-345
Tests Needed:
  - test_get_context_from_chapter_content
  - test_get_context_from_document_content
  - test_get_context_with_no_surrounding_text
  - test_get_context_extraction_and_truncation
Mock: Document and Chapter objects
Lines: ~70 lines of test code
Subagent: house-coder
Complexity: Simple (0-50 lines)
```

### Task Group 2.2: Add Unit Tests for ai_image_analyzer (72% → 85%)

**Current:** 72% coverage (105/146 statements)
**Target:** 85% coverage (~124/146 statements)
**Gap:** 41 statements untested

#### Task 2.2.1: Add unit tests for analyze_images_batch()
```yaml
File: tests/unit/test_ai_image_analyzer.py (NEW FILE)
Function: analyze_images_batch()
Coverage Gap: Lines 355-394
Tests Needed:
  - test_batch_processing_multiple_images
  - test_batch_processing_with_memory_limit
  - test_batch_processing_error_handling
  - test_batch_processing_empty_list
Mock: analyze_image() to return sample ImageAnalysis objects
Lines: ~80 lines of test code
Subagent: house-coder
Complexity: Medium (50-150 lines)
```

#### Task 2.2.2: Add unit tests for _parse_analysis_response()
```yaml
File: tests/unit/test_ai_image_analyzer.py
Function: _parse_analysis_response()
Coverage Gap: Lines 450-520
Tests Needed:
  - test_parse_complete_response
  - test_parse_partial_response_missing_fields
  - test_parse_malformed_response
  - test_parse_response_with_confidence_scores
  - test_parse_response_extracts_objects_list
Mock: Raw AI response strings
Lines: ~100 lines of test code
Subagent: house-coder
Complexity: Medium (50-150 lines)
```

#### Task 2.2.3: Add unit tests for error handling edge cases
```yaml
File: tests/unit/test_ai_image_analyzer.py
Function: analyze_image() error paths
Coverage Gap: Lines 608-611, 180-195
Tests Needed:
  - test_analyze_image_file_not_found
  - test_analyze_image_file_too_large
  - test_analyze_image_unsupported_format
  - test_analyze_image_non_vision_model_error
Mock: File system operations, AIConfig
Lines: ~60 lines of test code
Subagent: house-coder
Complexity: Simple (0-50 lines)
```

### Task Group 2.3: Add Unit Tests for ai_summarizer (49% → 75%)

**Current:** 49% coverage (27/55 statements)
**Target:** 75% coverage (~41/55 statements)
**Gap:** 28 statements untested

#### Task 2.3.1: Add unit tests for summarize_chapter()
```yaml
File: tests/unit/test_ai_summarizer.py (extend existing)
Function: summarize_chapter()
Coverage Gap: Lines 183-210
Tests Needed:
  - test_summarize_chapter_with_all_styles
  - test_summarize_chapter_with_metadata
  - test_summarize_chapter_invalid_chapter_id
  - test_summarize_chapter_empty_chapter
Mock: AIConfig.generate()
Lines: ~70 lines of test code
Subagent: house-coder
Complexity: Simple (0-50 lines)
```

#### Task 2.3.2: Add unit tests for detailed summary style
```yaml
File: tests/unit/test_ai_summarizer.py
Function: summarize_document() with style="detailed"
Coverage Gap: Lines 215-229
Tests Needed:
  - test_detailed_summary_respects_max_length
  - test_detailed_summary_longer_than_concise
  - test_detailed_summary_with_custom_options
Mock: AIConfig.generate()
Lines: ~50 lines of test code
Subagent: house-coder
Complexity: Simple (0-50 lines)
```

### Task Group 2.4: Add Unit Tests for ai_quality (67% → 85%)

**Current:** 67% coverage (54/81 statements)
**Target:** 85% coverage (~69/81 statements)
**Gap:** 27 statements untested

#### Task 2.4.1: Add unit tests for detailed quality metrics
```yaml
File: tests/unit/test_ai_quality.py (extend existing)
Function: score_quality() detailed metrics
Coverage Gap: Lines 312-339
Tests Needed:
  - test_quality_scoring_all_five_metrics
  - test_quality_scoring_with_metadata_context
  - test_quality_scoring_score_normalization
  - test_quality_scoring_strengths_and_suggestions_parsing
Mock: AIConfig.generate() with complete quality response
Lines: ~60 lines of test code
Subagent: house-coder
Complexity: Simple (0-50 lines)
```

### Task Group 2.5: Add Unit Tests for ai_tagger (66% → 85%)

**Current:** 66% coverage (35/53 statements)
**Target:** 85% coverage (~45/53 statements)
**Gap:** 18 statements untested

#### Task 2.5.1: Add unit tests for generate_tags_batch()
```yaml
File: tests/unit/test_ai_tagger.py (extend existing)
Function: generate_tags_batch()
Coverage Gap: Lines 188-198
Tests Needed:
  - test_batch_tag_generation_multiple_documents
  - test_batch_tag_generation_with_errors
  - test_batch_tag_generation_empty_list
  - test_batch_tag_generation_preserves_order
Mock: generate_tags() to return sample tag lists
Lines: ~60 lines of test code
Subagent: house-coder
Complexity: Simple (0-50 lines)
```

### Task Group 2.6: Add Unit Tests for ai_config (72% → 85%)

**Current:** 72% coverage (97/134 statements)
**Target:** 85% coverage (~114/134 statements)
**Gap:** 37 statements untested

#### Task 2.6.1: Add unit tests for retry logic execution
```yaml
File: tests/unit/test_ai_config.py (extend existing)
Function: generate() retry behavior
Coverage Gap: Lines 343-386
Tests Needed:
  - test_retry_on_retriable_error_with_backoff
  - test_no_retry_on_non_retriable_error
  - test_max_retries_respected
  - test_exponential_backoff_timing
Mock: API calls to raise specific errors
Lines: ~80 lines of test code
Subagent: house-coder
Complexity: Medium (50-150 lines)
```

#### Task 2.6.2: Add unit tests for OpenRouter and LM Studio providers
```yaml
File: tests/unit/test_ai_config.py
Function: _init_client() for OpenRouter and LM Studio
Coverage Gap: Lines 263-320
Tests Needed:
  - test_openrouter_client_initialization
  - test_lmstudio_client_initialization
  - test_provider_base_url_configuration
  - test_provider_fallback_behavior
Mock: openai.OpenAI client initialization
Lines: ~70 lines of test code
Subagent: house-coder
Complexity: Simple (0-50 lines)
```

---

## 🟢 PHASE 3: Medium Priority - Achieve 80%+ Coverage (3-5 days)

**Goal:** Increase coverage from 60% → 80%+ by adding comprehensive edge case tests

### Task Group 3.1: Add Vision API Provider Tests

#### Task 3.1.1: Add OpenAI vision API tests
```yaml
File: tests/unit/test_ai_image_analyzer.py, test_ai_image_describer.py
Function: _analyze_image_openai(), _describe_image_openai()
Tests Needed:
  - test_openai_vision_api_call_structure
  - test_openai_response_parsing
  - test_openai_model_validation
Mock: openai.OpenAI client
Lines: ~100 lines of test code
Subagent: house-coder
Complexity: Medium (50-150 lines)
```

#### Task 3.1.2: Add Ollama vision API tests
```yaml
File: tests/unit/test_ai_image_analyzer.py, test_ai_image_describer.py
Function: Ollama model detection and validation
Tests Needed:
  - test_ollama_llava_model_detection
  - test_ollama_bakllava_model_detection
  - test_ollama_non_vision_model_rejection
Mock: Ollama API responses
Lines: ~60 lines of test code
Subagent: house-coder
Complexity: Simple (0-50 lines)
```

### Task Group 3.2: Add Error Handling Tests

#### Task 3.2.1: Add comprehensive error handling for all AI functions
```yaml
Files: All AI processor test files
Tests Needed:
  - test_api_timeout_handling
  - test_api_rate_limit_handling
  - test_network_error_handling
  - test_invalid_response_format_handling
  - test_missing_api_key_handling
Mock: Various API error scenarios
Lines: ~150 lines of test code across all files
Subagent: house-coder
Complexity: Medium (100-200 lines)
```

### Task Group 3.3: Add Integration Tests with Mock API

#### Task 3.3.1: Create mock API server for testing
```yaml
File: tests/fixtures/mock_ai_server.py (NEW FILE)
Purpose: Mock Anthropic/OpenAI API for testing without real API calls
Features:
  - Mock endpoints for text generation
  - Mock endpoints for vision API
  - Configurable responses (success, error, rate limit)
  - Response delay simulation
Lines: ~200 lines of code
Subagent: house-coder
Complexity: High (200+ lines)
```

#### Task 3.3.2: Add integration tests using mock API
```yaml
File: tests/integration/test_ai_mock_integration.py (NEW FILE)
Purpose: Integration tests that don't require real API keys
Tests Needed:
  - test_end_to_end_tagging_workflow
  - test_end_to_end_summarization_workflow
  - test_end_to_end_vision_workflow
  - test_error_recovery_workflow
Mock: Use mock_ai_server.py
Lines: ~250 lines of test code
Subagent: house-coder
Complexity: High (200+ lines)
```

---

## 🔵 PHASE 4: Low Priority - Advanced Features (1 week)

**Goal:** Add advanced features and comprehensive edge case coverage

### Task Group 4.1: Add Performance Tests

#### Task 4.1.1: Add performance benchmarking tests
```yaml
File: tests/performance/test_ai_performance.py (NEW FILE)
Tests Needed:
  - test_batch_processing_performance
  - test_large_document_processing_time
  - test_concurrent_request_handling
  - test_memory_usage_with_large_images
Lines: ~150 lines of test code
Subagent: house-coder
Complexity: Medium (100-200 lines)
```

### Task Group 4.2: Add Advanced Integration Scenarios

#### Task 4.2.1: Add multi-provider failover tests
```yaml
File: tests/integration/test_ai_failover.py (NEW FILE)
Tests Needed:
  - test_failover_from_anthropic_to_openai
  - test_failover_to_local_ollama
  - test_provider_health_check
Lines: ~120 lines of test code
Subagent: house-coder
Complexity: Medium (100-200 lines)
```

### Task Group 4.3: Add Documentation and Examples

#### Task 4.3.1: Create testing documentation
```yaml
File: docs/TESTING_GUIDE.md (NEW FILE)
Content:
  - How to run unit tests
  - How to run integration tests
  - How to add new tests
  - Coverage requirements
  - Mock patterns and best practices
Lines: ~300 lines of documentation
Subagent: house-coder
Complexity: Medium (100-200 lines)
```

---

## 📋 Task Execution Guidelines

### For Each Task:

1. **Before Starting:**
   - Read the full task description
   - Understand the coverage gap being addressed
   - Review existing test patterns in the file

2. **Implementation:**
   - Follow existing test naming conventions
   - Use appropriate mocks (unittest.mock, pytest fixtures)
   - Add docstrings explaining what each test validates
   - Keep tests focused and independent

3. **After Completion:**
   - Run the specific test file: `uv run pytest tests/unit/test_<module>.py -v`
   - Check coverage: `uv run pytest --cov=omniparser.processors.<module> --cov-report=term-missing`
   - Commit with descriptive message following conventional commit format

4. **Quality Checklist:**
   - ✅ Test passes independently
   - ✅ Test is deterministic (no flakiness)
   - ✅ Mocks are properly configured
   - ✅ Coverage increased for target function
   - ✅ No side effects or test pollution
   - ✅ Clear test name and docstring

---

## 🎯 Success Metrics

### Phase 1 (Critical Fixes)
- **Metric:** All integration tests passing (39/39)
- **Target:** 100% pass rate
- **Validation:** `uv run pytest tests/integration/ -m integration -v`

### Phase 2 (High Priority Coverage)
- **Metric:** AI module coverage ≥ 60%
- **Target:**
  - ai_image_describer: 17% → 70%
  - ai_image_analyzer: 72% → 85%
  - ai_summarizer: 49% → 75%
  - ai_quality: 67% → 85%
  - ai_tagger: 66% → 85%
  - ai_config: 72% → 85%
- **Validation:** `uv run pytest --cov=omniparser --cov-report=term`

### Phase 3 (Medium Priority Coverage)
- **Metric:** AI module coverage ≥ 80%
- **Target:** All AI modules at 80%+ coverage
- **Validation:** `uv run pytest --cov=omniparser --cov-report=html`

### Phase 4 (Advanced Features)
- **Metric:** Comprehensive test suite
- **Target:** Performance tests, failover tests, documentation complete
- **Validation:** Manual review and stakeholder approval

---

## 🚀 Quick Start Commands

### For Immediate Work (Phase 1):
```bash
# 1. Fix a specific test
uv run pytest tests/integration/test_ai_vision_integration.py::TestImageDescriptionIntegration::test_describe_single_image_anthropic -v

# 2. Run all vision integration tests
uv run pytest tests/integration/test_ai_vision_integration.py -v

# 3. Check coverage for a specific module
uv run pytest --cov=omniparser.processors.ai_image_describer --cov-report=term-missing
```

### For Adding Unit Tests (Phase 2):
```bash
# 1. Create new test file
touch tests/unit/test_ai_image_describer.py

# 2. Run tests as you develop
uv run pytest tests/unit/test_ai_image_describer.py -v -k test_describe_image_with_anthropic_mock

# 3. Check coverage improvement
uv run pytest tests/unit/test_ai_image_describer.py --cov=omniparser.processors.ai_image_describer --cov-report=term-missing
```

### For Full Validation:
```bash
# 1. Run all tests (unit + integration)
uv run pytest tests/ -v

# 2. Generate full coverage report
uv run pytest --cov=omniparser --cov-report=html

# 3. Open coverage report in browser
open htmlcov/index.html
```

---

## 📁 Files Reference

### Test Files to Modify:
- `tests/integration/test_ai_vision_integration.py` (Phase 1)
- `tests/integration/test_ai_retry_integration.py` (Phase 1)
- `tests/unit/test_ai_image_describer.py` (NEW - Phase 2)
- `tests/unit/test_ai_image_analyzer.py` (NEW - Phase 2)
- `tests/unit/test_ai_summarizer.py` (EXTEND - Phase 2)
- `tests/unit/test_ai_quality.py` (EXTEND - Phase 2)
- `tests/unit/test_ai_tagger.py` (EXTEND - Phase 2)
- `tests/unit/test_ai_config.py` (EXTEND - Phase 2)

### Source Files Being Tested:
- `src/omniparser/ai_config.py`
- `src/omniparser/processors/ai_image_analyzer.py`
- `src/omniparser/processors/ai_image_describer.py`
- `src/omniparser/processors/ai_quality.py`
- `src/omniparser/processors/ai_summarizer.py`
- `src/omniparser/processors/ai_tagger.py`

### Coverage Reports:
- `htmlcov/index.html` (Interactive HTML report)
- `COVERAGE_REPORT_AI_MODULES.md` (Detailed analysis)
- `COVERAGE_QUICK_REFERENCE.txt` (Quick overview)
- `AI_COVERAGE_SUMMARY.txt` (Executive summary)
- `COVERAGE_ANALYSIS_INDEX.md` (Navigation guide)

---

## 💡 Tips for Efficient Development

### Using house-coder Subagent:

1. **For Simple Fixes (<50 lines):**
   ```
   Use house-coder for Phase 1 tasks - these are surgical fixes to existing tests
   ```

2. **For New Test Files (50-200 lines):**
   ```
   Use house-coder for Phase 2 unit test creation
   Provide clear examples of existing test patterns to follow
   ```

3. **For Complex Features (>200 lines):**
   ```
   Break into smaller subtasks
   Use house-coder for individual components
   Manual integration and review
   ```

### Test Writing Patterns:

**Pattern 1: Simple Mock Test**
```python
@patch('omniparser.ai_config.AIConfig')
def test_function_with_mock(mock_config):
    mock_config.return_value.generate.return_value = "mocked response"
    result = function_to_test()
    assert result == expected_value
```

**Pattern 2: Fixture-Based Test**
```python
@pytest.fixture
def sample_image_analysis():
    return ImageAnalysis(
        image_path="/test/path.png",
        description="Test description",
        # ... other fields
    )

def test_with_fixture(sample_image_analysis):
    result = process_analysis(sample_image_analysis)
    assert result.description == "Test description"
```

**Pattern 3: Parametrized Test**
```python
@pytest.mark.parametrize("input,expected", [
    ("test1", "result1"),
    ("test2", "result2"),
    ("test3", "result3"),
])
def test_multiple_cases(input, expected):
    assert function(input) == expected
```

---

## 🔄 Continuous Improvement

### After Completing Phase 1:
- Run full integration suite: `uv run pytest tests/integration/ -m integration -v`
- Verify 100% pass rate
- Commit fixes with detailed commit message

### After Completing Phase 2:
- Run coverage report: `uv run pytest --cov=omniparser --cov-report=html`
- Verify ≥60% coverage for all AI modules
- Review uncovered lines in HTML report
- Commit new test files

### After Completing Phase 3:
- Run performance validation
- Check for test flakiness (run suite 5 times)
- Update documentation with new test patterns
- Commit comprehensive test suite

---

## 📞 Need Help?

### Common Issues:

**Issue: Tests are flaky**
- Solution: Check for time-dependent logic, random values, or uncontrolled external state
- Add `@pytest.mark.flaky(reruns=3)` for genuinely flaky tests

**Issue: Mocks not working**
- Solution: Verify mock path matches import path in source code
- Use `@patch('module.Class')` not `@patch('tests.module.Class')`

**Issue: Coverage not improving**
- Solution: Check if tests are actually executing the target code
- Use `--cov-report=term-missing` to see uncovered lines
- Add print statements to verify code paths

**Issue: Integration tests timing out**
- Solution: Increase timeout values in test configuration
- Check API key is valid and accessible
- Verify network connectivity

---

**Total Estimated Effort:**
- Phase 1 (Critical): 2-3 hours
- Phase 2 (High Priority): 1-2 days
- Phase 3 (Medium Priority): 3-5 days
- Phase 4 (Low Priority): 1 week

**Total Tasks:** 30+ discrete, actionable tasks broken down for efficient subagent execution

**End Goal:** Production-ready AI parsing features with 80%+ test coverage and comprehensive validation
