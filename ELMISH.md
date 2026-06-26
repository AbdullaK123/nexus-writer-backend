# State Machine Component Architecture for React

**A pattern for building deterministic, type-safe React applications where every component is a state machine, every prop is a discriminated union, and illegal states are structurally unrepresentable.**

---

## The Problem

React's component model encourages a props pattern that creates implicit, unmanaged complexity. A typical component receives a flat bag of optional fields — booleans, nullable values, and loosely typed handlers — that interact combinatorially to produce a vast space of possible states, most of which are invalid.

Consider a standard data-fetching component. The common approach models it as `{ isLoading: boolean; isError: boolean; data: T | null; error: Error | null }`. This creates sixteen possible combinations of those four fields. Only four or five of those combinations are valid. The remaining eleven are illegal states — loading with data, error without an error object, data and error simultaneously — that the type system permits, the component must silently tolerate, and the developer must mentally track.

This pattern compounds across a page. Ten components with three boolean flags each produce 59,049 possible combinations. No developer can reason about that state space. No test suite can cover it. Bugs hide in the combinations nobody anticipated, surfacing as blank screens, stale data, or impossible UI states that are difficult to reproduce and painful to debug.

The root cause is that React's prop model, as conventionally used, does not distinguish between states — it describes fields. Fields combine. States select.

---

## The Pattern

This architecture replaces field-based props with variant-based props. Every component receives a single discriminated union (DU) that enumerates the exact states the component can occupy. Each variant carries only the data and handlers relevant to that state. The component body is a switch expression that pattern-matches on the status discriminant and renders the appropriate output.

The architecture has three structural layers.

**The Foundation Layer** provides `Option<T>` and `Result<T, E>` types that replace `null`, `undefined`, and untyped exceptions. These are the primitives that make the upper layers possible.

**The Hook Layer** owns raw state — async queries, user input, route params, UI flags — and transforms it into fully resolved discriminated unions for every component on the page. Each hook is a pure transformation: state in, props out. All conditional logic, error handling, and state derivation lives here.

**The Component Layer** receives resolved DU props and pattern-matches on the status field. Components contain zero business logic, zero data fetching, zero conditional branching beyond the switch. They are pure functions from variant to JSX.

---

## Foundation: Option and Result

The pattern requires eliminating `null`, `undefined`, and `any` from the codebase. These three types represent the invisible failure modes that make field-based props dangerous.

### Option\<T\>

Replaces all uses of `T | null`, `T | undefined`, and optional fields (`field?: T`).

```typescript
type Option<T> = Some<T> | None

class Some<T> {
  readonly value: T
  isSome(): this is Some<T>  // returns true
  isNone(): false
  unwrap(): T
  unwrapOr(_fallback: T): T
  map<U>(fn: (v: T) => U): Option<U>
  andThen<U>(fn: (v: T) => Option<U>): Option<U>
  match<R>(handlers: { Some: (v: T) => R; None: () => R }): R
}

class None {
  isSome(): false
  isNone(): this is None  // returns true
  unwrap(): never  // throws — compile-time guard only
  unwrapOr<T>(fallback: T): T
  map<U>(_fn: unknown): None
  andThen<U>(_fn: unknown): None
  match<R>(handlers: { Some: never; None: () => R }): R
}
```

The critical invariant: `unwrap()` is only safe after narrowing via `isSome()`, `match`, or exhaustive conditional checks. In practice, `match` is the primary access pattern, making `unwrap` rare outside of already-narrowed contexts.

At the boundary where external APIs return nullable values, `fromNullable(value)` converts to `Option`, quarantining nullability at the edge.

### Result\<T, E\>

Replaces `try/catch` with typed, composable error handling.

```typescript
type Result<T, E> = Ok<T> | Err<E>

class Ok<T> {
  readonly value: T
  isOk(): this is Ok<T>
  isErr(): false
  unwrap(): T
  match<R>(handlers: { Ok: (v: T) => R; Err: (e: never) => R }): R
}

class Err<E> {
  readonly error: E
  isOk(): false
  isErr(): this is Err<E>
  unwrapErr(): E
  match<R>(handlers: { Ok: (v: never) => R; Err: (e: E) => R }): R
}
```

Every API call returns `Result<T, ApiError>` — never a thrown exception. The caller is forced by the type system to handle both success and failure. Error types are visible in the function signature.

### Boundary Enforcement

These types are enforced at the two critical boundaries where untrusted data enters the application.

**The HTTP boundary.** Every API response passes through a `fetchApi` function that validates the response body against a Zod schema, wraps successes in `Ok`, and wraps failures in `Err`. No unvalidated data enters the application. No error can be silently ignored.

**The nullability boundary.** Every nullable value from browser APIs, library return types, or external sources is converted to `Option` via `fromNullable` at the point of entry. From that point inward, the entire application operates on explicit presence-or-absence types.

---

## AsyncState: The Data-Fetching State Machine

`AsyncState<T, E>` is a five-variant discriminated union that models every possible state of an async data operation. It replaces TanStack Query's `{ isLoading, isError, data, error }` boolean matrix with an explicit state machine.

```typescript
type AsyncState<T, E> =
  | { status: 'idle'; data: Option<never> }
  | { status: 'loading'; data: Option<never> }
  | { status: 'error'; data: Some<Err<E>>; error: E }
  | { status: 'empty'; data: Some<Ok<[]>> }
  | { status: 'success'; data: Some<Ok<T>> }
```

Design decisions in this type:

**`idle` is not `loading`.** Idle means no request has been made — `enabled` is false, or the component just mounted. Loading means a request is in flight. Conflating them leads to spinners before any request fires.

**`empty` is not `success`.** An empty array is a valid success response with its own UX — "no items yet" messaging, creation CTAs, onboarding prompts. Treating it as generic success forces `if (data.length === 0)` checks across the rendering layer.

**`data` uses `Option<never>` in non-data states.** This makes it a compile error to access data when the status is `idle` or `loading`. The type system — not runtime checks — prevents stale data access.

**`error` carries both the typed `Err<E>` wrapper and the unwrapped error.** This provides ergonomic access for display while maintaining the Result chain for programmatic handling.

A `toAsyncState` adapter converts TanStack Query's result shape into this union at the hook boundary, keeping the async state machine consistent across all data-fetching hooks.

---

## Component Props as Discriminated Unions

The core principle: every component's props type is a discriminated union where each variant represents one valid state the component can occupy. Each variant carries exactly the fields needed for that state — no more, no fewer.

### Basic Example: Button

The conventional approach:

```typescript
// CONVENTIONAL: boolean matrix, 8 possible combinations, most invalid
type ButtonProps = {
  label: string
  onClick?: () => void
  disabled?: boolean
  loading?: boolean
}
```

The state machine approach:

```typescript
// STATE MACHINE: 4 states, all valid, exhaustively handled
type ButtonProps =
  | { status: 'idle'; label: string; onClick: () => void }
  | { status: 'loading'; label: string }
  | { status: 'disabled'; label: string; reason: string }
  | { status: 'success'; label: string }
```

What changes:

- `loading` has no `onClick`. You cannot click a loading button. The type forbids constructing one that accepts clicks.
- `disabled` requires a `reason`. Accessibility demands an explanation. The type prevents a disabled button without one.
- `success` is its own state, not a boolean flag that might persist into the next interaction cycle.
- `idle` is the only state with `onClick`. The handler exists precisely where it's valid.

### Data Component Example: Task List

```typescript
type TaskListProps =
  | { status: 'loading' }
  | { status: 'error'; error: string; onRetry: () => void }
  | { status: 'empty'; message: string }
  | { status: 'ready'; items: TaskItemProps[]; counts: Counts }
```

Each variant is a self-contained rendering contract. The `loading` variant carries nothing — the component shows a skeleton. The `error` variant carries the error message and a retry handler — the component shows the error and a button. The `empty` variant carries a contextual message. The `ready` variant carries the data and derived counts.

No variant can be confused for another. No field leaks across states. The component renders by switching on status, and the compiler ensures every case is handled.

### Interactive Component Example: Task Item

```typescript
type TaskItemProps =
  | { status: 'idle'; task: Task; onToggle: () => void; onEdit: () => void; onDelete: () => void }
  | { status: 'editing'; task: Task; editValue: string; onEditChange: (v: string) => void; onSave: () => void; onCancel: () => void }
  | { status: 'saving'; task: Task; label: string }
  | { status: 'deleting'; task: Task }
```

The `saving` variant has no action handlers. A saving task cannot be edited, toggled, or deleted. The `editing` variant has no `onToggle` or `onDelete` — those actions are unavailable during editing. The type system encodes which actions are valid in which states.

### Form Example: Input with Validation

```typescript
type InputProps =
  | { status: 'idle'; value: string; onChange: (v: string) => void }
  | { status: 'focused'; value: string; onChange: (v: string) => void }
  | { status: 'invalid'; value: string; onChange: (v: string) => void; error: string }
  | { status: 'disabled'; value: string }
```

`disabled` has no `onChange`. A disabled input cannot accept changes. `invalid` must carry an `error` — no red border without an explanation.

---

## The Component Layer

Components are pure functions that pattern match on their props' status field. They contain zero business logic, zero data fetching, zero state management, zero conditional branching beyond the switch.

```typescript
function TaskList(props: TaskListProps) {
  switch (props.status) {
    case 'loading':
      return <TaskListSkeleton />
    case 'error':
      return <ErrorState error={props.error} onRetry={props.onRetry} />
    case 'empty':
      return <EmptyState message={props.message} />
    case 'ready':
      return (
        <ul>
          {props.items.map(item => <TaskItem key={item.task.id} {...item} />)}
        </ul>
      )
  }
}
```

Properties of this layer:

**Exhaustiveness.** The switch covers every variant. If a new variant is added to the union, every component that consumes it fails to compile until the new case is handled. The compiler — not discipline, not code review, not testing — ensures completeness.

**No defensive checks.** There is no `if (props.data)` guard, no `props.error?.message` optional chaining, no `props.onClick && props.onClick()` existence check. The type narrowing within each case guarantees that the fields exist. The code expresses only what should happen, not what might go wrong.

**Independent testability.** Each case is a pure function from a known variant to a known JSX output. Testing requires no mocking, no async setup, no simulated API calls. Pass a variant, assert the output.

---

## The Hook Layer: State-to-Props Transformation

Page hooks are the brain of the architecture. They own raw state, manage side effects, handle transitions, and transform everything into resolved discriminated unions for every component on the page.

### Structure

```typescript
function useTasksPage() {
  // ---- raw state ----
  const [tasks, setTasks] = useState<Option<Result<Task[], string>>>(None)
  const [filter, setFilter] = useState<Filter>('all')
  const [editingId, setEditingId] = useState<Option<string>>(None)
  const [savingIds, setSavingIds] = useState<Set<string>>(new Set())

  // ---- actions ----
  const handleToggle = useCallback(async (id: string) => { /* ... */ }, [])
  const handleDelete = useCallback(async (id: string) => { /* ... */ }, [])

  // ---- state → props transformation ----
  const listProps: TaskListProps = deriveListProps(tasks, filter, editingId, savingIds)
  const filterBarProps: FilterBarProps = deriveFilterProps(tasks, filter)
  const formProps: TaskFormProps = deriveFormProps(formValue, isSubmitting, formError)

  return { listProps, filterBarProps, formProps }
}
```

### Transformation Logic

The transformation from raw state to component DU is the core operation. For each component, the hook inspects raw state and selects the appropriate variant.

```typescript
function deriveListProps(
  tasks: Option<Result<Task[], string>>,
  filter: Filter,
  editingId: Option<string>,
  savingIds: Set<string>
): TaskListProps {
  // Option is None → still loading
  if (tasks.isNone()) {
    return { status: 'loading' }
  }

  // Result is Err → fetch failed
  const result = tasks.unwrap()
  if (result.isErr()) {
    return { status: 'error', error: result.unwrapErr(), onRetry: loadTasks }
  }

  const taskList = result.unwrap()
  const filtered = applyFilter(taskList, filter)

  // Empty after filtering
  if (filtered.length === 0) {
    return { status: 'empty', message: `No ${filter} tasks.` }
  }

  // Ready — build item DUs
  return {
    status: 'ready',
    items: filtered.map(task => deriveTaskItemProps(task, editingId, savingIds)),
    counts: deriveCounts(taskList),
  }
}
```

Each derivation function is a pure transformation. Raw state enters, a fully resolved variant exits. The component never sees the raw state. It never makes decisions. It receives a verdict and renders it.

### Composing Item-Level State Machines

Individual items within a list each have their own state machine, resolved by the hook.

```typescript
function deriveTaskItemProps(
  task: Task,
  editingId: Option<string>,
  savingIds: Set<string>,
  deletingIds: Set<string>,
): TaskItemProps {
  if (deletingIds.has(task.id))
    return { status: 'deleting', task }

  if (savingIds.has(task.id))
    return { status: 'saving', task, label: task.title }

  if (editingId.isSome() && editingId.unwrap() === task.id)
    return { status: 'editing', task, editValue, onEditChange, onSave, onCancel }

  return { status: 'idle', task, onToggle, onEdit, onDelete }
}
```

Priority determines state. A deleting task cannot be editing. A saving task cannot be idle. The function checks states in order of precedence and returns the first match. The resulting variant is definitive.

---

## The Page Layer

The page component is the thinnest possible layer. It calls its hook, destructures the resolved DU props, and spreads them into child components.

```typescript
function TasksPage() {
  const { toastProps, formProps, listProps, filterBarProps, statsProps } = useTasksPage()

  return (
    <div className="page">
      <Toast {...toastProps} />
      <StatsBar {...statsProps} />
      <TaskForm {...formProps} />
      <FilterBar {...filterBarProps} />
      <TaskList {...listProps} />
    </div>
  )
}
```

No logic. No conditionals. No imports beyond the components and the hook. The page is a pure composition of resolved state machines.

---

## Architectural Properties

### Linear Complexity Scaling

In conventional React, complexity grows combinatorially — each optional prop multiplies the implicit state space. With DU props, complexity grows linearly. Ten components with four variants each produce forty total states, not a combinatorial explosion. Adding a component adds its variants to the count without multiplying against existing components.

### Self-Documenting Contracts

The props type is the complete contract. A new developer reads a component's DU and immediately knows every state it can occupy, every piece of data each state requires, and every action available in each state. No tribal knowledge required. No reading three other files to understand the component's behavior.

### Compiler-Enforced Exhaustiveness

Adding a new variant to a DU causes every consumer to fail compilation until the new case is handled. The compiler finds every call site automatically. No grep, no global search, no hoping code review catches the missing case.

### Isolated State Machines

Components are independent state machines. A change to one component's variant set does not affect other components. The interaction between components happens in the hook layer, where state-to-props transformation is explicit and centralized, not in the component layer where it would be distributed and implicit.

### Pure Testability

Hooks are pure transformations — given raw state, assert resolved variants. Components are pure renderers — given a variant, assert JSX output. Both are independently testable with no mocking, no DOM rendering, no async setup for the unit under test.

### Snapshot Debugging

At any moment, the complete UI state is a tree of resolved DU variants. This tree can be serialized, logged, diffed, and replayed. Bug reports can include the exact variant tree that produced the broken render, making reproduction deterministic.

---

## Rules

These rules define the architectural boundaries. Violating any of them reintroduces the implicit state problems the pattern exists to eliminate.

1. **Every component's props must be a discriminated union with a `status` field.** No flat bags of optional fields. No boolean flags. The union enumerates every valid state.

2. **Each variant carries only the fields relevant to that state.** Handlers that are invalid in a given state must not appear in that variant. Data that doesn't exist in a given state must not be typed as present.

3. **Components contain only a switch on status.** No business logic, no data fetching, no state management, no conditional branching beyond the switch. The component is a pure function from variant to JSX.

4. **Page hooks transform raw state into resolved DU props.** All conditional logic, error handling, state derivation, and handler binding happens in the hook. The hook's return type is a record of fully resolved DUs, one per child component.

5. **`null`, `undefined`, and `any` are banned.** Use `Option<T>` for presence/absence. Use `Result<T, E>` for success/failure. Use explicit types for everything else. These are enforced at the boundary and propagated inward.

6. **Boundary validation is mandatory.** Every API response is validated through a schema (Zod) and wrapped in `Result`. Every nullable external value is wrapped in `Option` via `fromNullable`. No unvalidated data enters the application.

7. **AsyncState replaces boolean loading/error flags.** All async data operations use the five-variant `AsyncState<T, E>` union. No `{ isLoading: boolean; data: T | null }` patterns.

---

## Relationship to Existing Patterns

**The Elm Architecture (TEA).** This pattern is structurally equivalent to TEA: the DU props are the Model, the component switch is the View, and the hook combines Update and Model management. The difference is enforcement — Elm enforces at the language level; this pattern enforces at the architectural level within TypeScript.

**MVVM.** The hook serves as the ViewModel, mediating between the Model (server state, async data) and the View (JSX). Unlike classical MVVM frameworks, there are no classes, no decorators, no framework abstractions — just functions.

**State Machines / Statecharts.** Each component's DU is a state machine definition. The hook layer manages transitions. The pattern is compatible with but does not require formal statechart libraries like XState — the type system itself provides the guarantees.

**Functional Core, Imperative Shell.** The hook is the imperative shell — it manages effects, calls APIs, handles side effects. The component is the functional core — a pure function from props to output. The boundary between them is the DU props interface.

---

## When to Use This Pattern

This architecture is designed for stateful, interactive applications — editors, dashboards, creative tools, real-time interfaces, form-heavy workflows. Applications where the user is producing or manipulating rather than consuming.

It is not necessary for static content sites, marketing pages, or read-heavy applications where server rendering handles the dominant use case and interactivity is minimal.

The investment is in upfront type design — defining the DU for each component before building it. This cost is repaid through eliminated bug classes, self-documenting contracts, compiler-enforced completeness, and linear complexity scaling as the application grows.
