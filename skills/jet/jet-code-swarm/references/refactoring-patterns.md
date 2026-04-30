# Refactoring Patterns by Stack

Reference for the Analyst and Architect agents. Use this to identify stack-specific
anti-patterns and to select appropriate refactoring techniques.

---

## Kotlin / Spring Boot

### Common Anti-Patterns to Flag

| Anti-Pattern | Signs | Preferred Alternative |
|---|---|---|
| Anemic domain model | Entities with only getters/setters, all logic in services | Move behaviour into domain classes where it belongs |
| God service | `*Service` class with 500+ lines and 10+ injected dependencies | Split by subdomain or use case |
| Transaction leakage | `@Transactional` on controllers or repositories instead of services | Move `@Transactional` to service layer |
| Nullable misuse | `!!` operator (non-null assertion), especially chained `x?.y!!` which guarantees NPE when `x` is null | Use `?.let`, `?:`, `requireNotNull()` with message, or restructure to avoid null |
| Exception domain mismatch | Throwing the wrong exception type when logic is moved between layers — e.g. throwing `PromptNotFoundException` inside a block that just failed a project lookup | Use the exception that names the actual missing resource; check all `?: throw` sites after extraction |
| Unconstrained inheritance | Deep class hierarchies for code reuse | Favour composition via delegation (`by` keyword) |
| Raw string SQL in repository | SQL strings in JPA repository methods or services | Use Spring Data JPA query methods or `@Query` |
| Missing `data class` | Regular `class` used for DTOs with manual `equals`/`hashCode` | Convert to `data class` |
| Mutable `var` in DTOs | Request/response objects with `var` fields | Use `val` — DTOs should be immutable |
| Returning `null` from service | Service methods that return `null` to indicate "not found" | Throw `ResourceNotFoundException` or return `Optional` |
| Fat controller | Controller methods with business logic beyond delegation | Extract to service |
| Duplicated utility logic | Extracting a helper method whose body is identical to an existing one elsewhere (e.g. a `deserialize` in a mapper copying one already in a service) | Search before writing — call the existing method instead |

### Useful Kotlin Refactoring Techniques

- **Extract to extension function** — move utility logic off a class into a top-level extension
- **Sealed class** — replace `when (type)` on string/enum with exhaustive sealed class hierarchy
- **Object expressions / companion objects** — replace static utility classes
- **Scope functions** (`let`, `run`, `apply`, `also`, `with`) — reduce repetition in object setup chains
- **`typealias`** — give meaningful names to complex generic types
- **Result type** — use `kotlin.Result` or a domain-specific sealed class instead of throwing for expected failures

### Spring Boot Specifics

- Constructor injection only — never field injection (`@Autowired` on a field)
- `@Component`, `@Service`, `@Repository` for stereotype, `@Bean` in `@Configuration` for third-party types
- Use `application.yaml` with `@ConfigurationProperties` data classes, not `@Value` scattered across beans
- Repository interfaces extend `JpaRepository<Entity, ID>` — avoid `EntityManager` unless necessary
- Flyway migrations in `src/main/resources/db/migration/V{n}__description.sql`

### Testing Conventions

- `@WebMvcTest` for controller layer — do not load the full context
- `@MockBean` to stub dependencies in Spring tests; `mockk` + `@MockkBean` if using MockK
- Integration tests in a separate source set (`src/integrationTest/kotlin`) requiring a real DB
- Test class: `class FooServiceTest` (unit) or `class FooIntegrationTest` (integration)

---

## TypeScript / Node.js

### Common Anti-Patterns to Flag

| Anti-Pattern | Signs | Preferred Alternative |
|---|---|---|
| `any` everywhere | `any` type annotations silencing the compiler | Explicit types or `unknown` with narrowing |
| Callback hell | Deeply nested `.then().then()` chains | `async/await` |
| Barrel export abuse | `index.ts` re-exporting everything | Explicit imports; barrel only at public API boundary |
| Missing error handling | `await` calls without `try/catch` or `.catch()` | Wrap in `try/catch`; use a Result pattern for expected failures |
| Mutable shared state | Module-level mutable variables | Encapsulate in class or use dependency injection |
| Fat route handler | Express/Fastify handler with business logic inline | Extract to service/use-case layer |
| `console.log` in production code | Debugging logs left in committed code | Replace with structured logger (e.g. `pino`) |
| Missing `readonly` | Interfaces with mutable fields that should be immutable | Add `readonly` to fields that do not change after construction |
| `interface` for everything | Using `interface` where `type` alias is simpler | Use `type` for unions, intersections, mapped types |
| Unsafe non-null assertion | `!` operator on a value that may genuinely be `undefined` or `null` — e.g. `map.get(key)!` when the key might not exist | Use optional chaining (`?.`), nullish coalescing (`??`), or an explicit guard before access |
| Error domain mismatch | Throwing a generic `Error` or the wrong Error subclass when logic is moved — e.g. throwing `PromptNotFoundError` when the project lookup fails | Use the error class or discriminated union variant that names the actual failure; audit all `?? throw` and `if (!x) throw` sites after extraction |
| Duplicated utility logic | Writing a helper function whose body is identical to an existing one in another module | Search with grep before writing — import and reuse the existing one |

### Useful TypeScript Refactoring Techniques

- **Extract custom hook** (React) — move stateful logic out of components into `use*` hooks
- **Discriminated union** — replace `switch (event.type)` on strings with a typed union
- **Zod schema** — add runtime validation at trust boundaries (HTTP input, external API response)
- **Dependency injection** — pass dependencies as constructor arguments rather than importing directly
- **Mapped types / generics** — eliminate copy-pasted type definitions
- **`satisfies` operator** — validate object shape at compile time without widening the type

### Testing Conventions

- Jest or Vitest; prefer Vitest for new code (faster, ESM-native)
- Test files co-located: `foo.service.test.ts` next to `foo.service.ts`
- Mock with `jest.fn()` / `vi.fn()` — avoid `jest.mock()` module mocks where possible
- Use `describe` blocks to group related cases
- Async tests: `async () => { await expect(...).resolves.toBe(...) }`

---

## C# / .NET

### Common Anti-Patterns to Flag

| Anti-Pattern | Signs | Preferred Alternative |
|---|---|---|
| Service locator | `IServiceProvider` injected and called at runtime | Constructor inject the specific dependency |
| Synchronous blocking | `.Result` or `.Wait()` on async tasks | `await` throughout the call chain |
| Missing cancellation | Async methods with no `CancellationToken` parameter | Add `CancellationToken ct = default` to async signatures |
| Magic strings | Configuration keys, event names, route paths as raw strings | `const` or `static readonly` fields; `nameof()` |
| Fat controller | `ApiController` with 300+ lines and business logic | Extract to service / command handler |
| Missing `IOptions<T>` | `IConfiguration` injected into services and `.GetSection()` called inline | Bind to a `record` / POCO via `IOptions<T>` |
| `public` everything | Classes and members defaulting to `public` | Explicit accessibility — `internal` for types not part of the public API |
| Mutable records | `class` with public setters for value objects | `record` with `init`-only setters, or immutable `class` |
| Unsafe `.Value` access | Calling `.Value` on a `Nullable<T>` without checking `HasValue`, or using `null!` to suppress warnings | Pattern matching (`is not null`), `??`, or throw explicitly |
| Exception domain mismatch | Throwing the wrong exception type after extracting logic — e.g. a method that looks up a project throws an exception named after a different entity | Name the exception after the resource that is actually missing; audit all `throw` sites after extraction |
| Duplicated utility logic | Writing a private helper method whose logic is identical to an existing extension or utility elsewhere | Search before writing — call or inherit the existing method |

### Useful C# Refactoring Techniques

- **`record` types** — replace value-object classes with concise records
- **Primary constructors** (.NET 8+) — simplify class and struct constructors
- **Pattern matching** — replace type checks and switch statements with `switch` expressions
- **`IResult` / minimal API** — simplify controller logic in .NET 6+ minimal API style
- **Mediator pattern (MediatR)** — decouple controllers from business logic via commands/queries
- **`Result<T>` / `OneOf`** — explicit error handling without exceptions for expected failures

### Testing Conventions

- xUnit preferred; NUnit acceptable
- Mock with Moq or NSubstitute
- Test class: `public class FooServiceTests`
- `[Fact]` for single case, `[Theory]` + `[InlineData]` for parameterised
- `WebApplicationFactory<Program>` for integration tests

---

## Python

### Common Anti-Patterns to Flag

| Anti-Pattern | Signs | Preferred Alternative |
|---|---|---|
| Missing type hints | Functions and variables with no annotations | Add type hints; use `mypy` to validate |
| `dict` as data container | Passing `dict` instead of a typed object | `dataclass` or `TypedDict` or Pydantic model |
| God module | Single `.py` file >500 lines with mixed concerns | Split into subpackage |
| Mutable default argument | `def foo(items=[])` | Use `None` as default and create inside the function |
| Bare `except` | `except:` catching everything silently | `except SpecificException as e:` |
| Missing `__init__.py` | Implicit namespace packages where explicit is intended | Add `__init__.py` to control the public API |
| String formatting via `%` or `.format()` | Old-style string formatting | f-strings |
| Global state | Module-level mutable variables | Encapsulate in a class or use dependency injection |
| Unsafe `Optional` access | Accessing an attribute on an `Optional[T]` value without a prior `is not None` guard — raises `AttributeError` at runtime | Guard with `if obj is not None:` or raise a descriptive exception before access |
| Exception domain mismatch | Using a broad or wrong exception class when logic is moved — e.g. raising `ValueError("Prompt not found")` when the project lookup fails | Use a custom exception class named after the actual failing resource; audit all `raise` sites after extraction |
| Duplicated utility logic | Defining a helper function whose body is identical to an existing one in another module | Search with grep before writing — import the existing function |

### Useful Python Refactoring Techniques

- **`dataclass`** — replace plain classes used as data containers
- **`Protocol`** — define structural interfaces without inheritance
- **`functools.lru_cache` / `cache`** — memoize pure functions
- **Context managers (`__enter__`/`__exit__`)** — replace try/finally patterns
- **Generator expressions** — replace list comprehensions when the result is consumed once
- **`pathlib.Path`** — replace `os.path` string manipulation

### Testing Conventions

- pytest; use fixtures for shared setup, not `setUp` / `tearDown`
- Mock with `pytest-mock` (`mocker` fixture) or `unittest.mock`
- Test file: `test_<module>.py` in a `tests/` directory mirroring the source tree
- Parameterise with `@pytest.mark.parametrize`
- Integration tests: mark with `@pytest.mark.integration` and run separately

---

## Cross-Stack Principles

These apply regardless of the stack:

### Extract Don't Rewrite
Prefer extracting existing logic into a new function/class over rewriting it. Extraction
preserves behaviour; rewriting introduces risk. The Analyst should flag rewrites that
masquerade as refactorings.

### One Reason to Change
Every function and class should have one reason to change (Single Responsibility).
A good test: can you name the class without using "and" or "or"?

### Make the Implicit Explicit
Configuration buried in logic, magic numbers, silent defaults — these should become
named constants, explicit parameters, or typed configuration objects.

### Shrink the Public Surface
Every `public` method or exported function is a commitment. If something is only used
internally, make it private/internal. Smaller public surfaces = easier to change.

### Tests First, Then Refactor
If the target code has low test coverage, the Architect should plan a "add tests for
existing behaviour" step *before* the refactoring steps. Refactoring without tests is
rearranging furniture in the dark.

### Reuse, Don't Duplicate
Before writing a new helper, utility method, or mapping function, search the codebase
for an existing implementation. If equivalent logic already exists in a service, utility
class, or module, call it — do not copy it. Extracting a function that duplicates existing
logic defeats the purpose of the refactoring and creates two places to update when
behaviour changes. This applies across all stacks:
- Kotlin: search with `rg` or IDE before writing a new `fun`
- TypeScript: check if a util or service already exports the logic before adding a new one
- C#: check extension methods, static helpers, and base classes before adding a new method
- Python: check existing modules with `grep` before defining a new function
