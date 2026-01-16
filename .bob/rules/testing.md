# Testing Rules

## Test Completion Requirements

**CRITICAL RULE**: Tasks involving test creation, modification or running CANNOT be marked as complete unless ALL relevant tests are passing.

### Requirements for Test-Related Task Completion

1. **All Tests Must Pass**: Every test that is part of the task scope must pass successfully
2. **No Skipped Tests**: Tests cannot be skipped or marked as "expected to fail" without explicit user approval
3. **Verification Required**: Must run the full test suite and verify results before attempting completion
4. **Exit Code Check**: Test runner must return exit code 0 (success)

### Exceptions

The only acceptable reasons to complete a task with failing tests:
1. User explicitly approves completing with known failures
2. Failing tests are explicitly out of scope for the current task
3. User provides alternative acceptance criteria

### Enforcement

Before using `attempt_completion` on any test-related task:
1. Run the full test suite
2. Check the exit code and pass/fail counts
3. If ANY tests fail, continue working to fix them
4. Only attempt completion when all tests pass

### Example

```bash
# Good - all tests passing
pytest tests/ -v
# Result: 25 passed, 0 failed
# ✅ Can attempt completion

# Bad - some tests failing  
pytest tests/ -v
# Result: 22 passed, 3 failed
# ❌ CANNOT attempt completion - must fix failing tests first
```

## Test Quality Standards

- Tests must be meaningful and test actual functionality
- Tests must not be overly permissive (e.g., accepting any non-empty response)
- Tests must have clear assertions that verify expected behavior
- Test failures must be investigated and root causes fixed

## Documentation

When tests are failing:
- Document the specific failures
- Identify root causes
- Create a plan to fix them
- Execute the fixes
- Verify all tests pass
- Only then attempt completion