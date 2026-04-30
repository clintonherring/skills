# Review Checklist

Used by the Reviewer agent in Step 6. Each gate must be assessed for every file changed
by the Coder. Mark each as ✅ Pass, ❌ Fail, or N/A with a note.

---

## 1. Plan Compliance

- [ ] Every step in the approved plan that was marked "Done" or "Partial" in the Coder report
  is reflected in the actual diff
- [ ] No files outside the agreed scope were modified without an explicit note in the Coder report
- [ ] Any deviation from the plan is flagged, even if the deviation looks correct — deviations
  may have consequences the Coder didn't foresee
- [ ] Files marked as "deletion candidates" were NOT deleted (per safety rules) — verify they
  are still present

---

## 2. Correctness

- [ ] The refactored code is logically equivalent to the original for all cases in scope
- [ ] No existing behaviour has been silently removed
- [ ] All callers of changed functions/methods/classes have been updated
- [ ] Return types, error types, and exception contracts match the original (or are explicitly
  planned changes)
- [ ] Concurrency concerns are preserved or improved: no new race conditions, no removed locks
- [ ] No duplicated logic introduced — new or extracted code reuses existing utility methods
  rather than copying them. Flag any new function whose body is substantively identical to
  an existing one elsewhere in the codebase.

---

## 3. Public API Preservation

- [ ] All public methods, exported functions, and HTTP endpoints that existed before still
  exist after (unless explicitly changed by the plan)
- [ ] Method signatures match the originals or are backward-compatible
- [ ] No new required parameters were added to public APIs without a migration path
- [ ] HTTP status codes and response shapes are unchanged for existing endpoints

---

## 4. Error Handling

- [ ] All error paths that existed before are still handled
- [ ] No new unhandled exceptions or error paths introduced
- [ ] Error messages and codes are preserved or improved
- [ ] **Exception/error types match the actual failure domain.** For every new or moved
  error-throwing path, verify the exception/error type describes the resource that is
  actually missing or invalid — not a different entity's exception used for convenience.
  A missing project must produce a project-not-found error; a missing prompt must produce
  a prompt-not-found error. This is a **Blocking** issue if violated.
  - Kotlin: exception class name from `DomainExceptions.kt` hierarchy
  - TypeScript: Error subclass or discriminated union variant
  - C#: exception type or `ProblemDetails` type field
  - Python: custom exception class name
- [ ] Stack-specific error handling patterns are followed:
  - Kotlin: domain exceptions from `DomainExceptions.kt` hierarchy
  - TypeScript: structured error objects or Result types, not bare `throw new Error(string)`
  - C#: `ProblemDetails` or appropriate HTTP exception types
  - Python: custom exception classes, not bare `raise Exception(string)`

---

## 5. Test Coverage

- [ ] Every changed function or method has at least one corresponding test
- [ ] Happy path is covered for each refactored unit
- [ ] At least one unhappy path / error case is covered for each refactored unit
- [ ] Tests that were passing before are still passing (no regressions introduced)
- [ ] No test was deleted without a replacement that covers the same behaviour
- [ ] No stale or orphaned mock setups remain for methods that were moved, renamed, or
  removed by the refactoring. A mock targeting a method that no longer exists on the
  mocked class is a dead stub — it passes silently while the actual behaviour goes
  untested. This is a **Major** issue.

---

## 6. Naming and Readability

- [ ] New names (classes, functions, variables) follow the codebase's naming conventions
- [ ] No misleading names: names describe what the code does, not what it used to do
- [ ] No leftover names from the old structure (e.g. a class extracted out of `FooService`
  should not still be called `FooServiceHelper` if it is now independent)
- [ ] Comments are updated: no comments that reference the old structure or are now stale
- [ ] No `TODO` or `FIXME` comments added without a linked ticket

---

## 7. Stack-Specific Quality Gates

### Kotlin / Spring Boot
- [ ] `@Transactional` is only on service layer methods, not controllers or repositories
- [ ] No `!!` (non-null assertion) added in new code — especially the chained form `x?.y!!`
  which combines a safe-call with an immediate non-null assertion and guarantees an NPE
  when the left-hand side is null. Use `requireNotNull(x?.y) { "..." }`, `x?.y ?: throw`,
  or restructure to avoid null altogether. This is a **Blocking** issue.
- [ ] DTOs use `val`, not `var`
- [ ] Constructor injection used — no `@Autowired` on fields
- [ ] New entities have Flyway migration if schema changed
- [ ] No raw SQL strings in service layer

### TypeScript / Node.js
- [ ] No `any` type added — use explicit types or `unknown` with narrowing
- [ ] No `!` (non-null assertion operator) added in new code where the value may genuinely
  be `undefined` or `null`. Use optional chaining (`?.`), nullish coalescing (`??`), or
  an explicit guard before access. This is a **Blocking** issue.
- [ ] All `await` calls are inside `try/catch` or have `.catch()` handlers
- [ ] No new `console.log` left in production code
- [ ] No barrel exports (`index.ts`) created where not appropriate

### C# / .NET
- [ ] No `.Result` or `.Wait()` on async tasks (sync-over-async)
- [ ] New async methods include `CancellationToken ct = default` parameter
- [ ] No `IConfiguration` injected into services — use `IOptions<T>` instead
- [ ] No bare `catch (Exception)` swallowing errors silently
- [ ] No `null!` suppression or `.Value` on `Nullable<T>` without a prior null check.
  Use pattern matching (`is not null`), `??`, or throw explicitly. This is a **Blocking**
  issue when applied to values that can genuinely be null at runtime.

### Python
- [ ] All new functions and methods have type hints
- [ ] No mutable default arguments (`def foo(items=[])`)
- [ ] No bare `except:` clauses
- [ ] New data containers use `dataclass` or Pydantic, not plain `dict`
- [ ] No unsafe attribute access on `Optional` values without a prior `is not None` guard.
  Accessing `obj.attr` when `obj` is `Optional[T]` without checking raises `AttributeError`.
  Use an explicit guard or raise a descriptive exception. This is a **Blocking** issue.

---

## 8. Performance

- [ ] No N+1 query patterns introduced (new loops calling the DB or an external service)
- [ ] No synchronous I/O calls added in an async context
- [ ] No obviously expensive operations (sorting, filtering) moved to happen more frequently
  than before

---

## 9. Security

- [ ] No secrets, credentials, or API keys appear in the changed code
- [ ] Input validation is preserved or improved at trust boundaries
- [ ] No new SQL injection surface (raw string queries with unescaped input)
- [ ] File paths from user input are not used without sanitisation

---

## Severity Guide for Issue Classification

| Severity | When to use |
|---|---|
| **Blocking** | Correctness bug, broken API contract, security issue, or the build/tests fail |
| **Major** | Missing error handling, naming that actively misleads, significant test gap |
| **Minor** | Style inconsistency, suboptimal but not wrong, optional improvement |
