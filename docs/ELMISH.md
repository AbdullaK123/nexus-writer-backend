# State Machine Component Architecture for React

**A pattern for building deterministic, type-safe React applications where every component is a state machine, every prop is a discriminated union, every user event is a message, every side effect is an explicit command, and illegal states are structurally unrepresentable.**

---

## The Problem

React's component model encourages a props pattern that creates implicit, unmanaged complexity. A typical component receives a flat bag of optional fields — booleans, nullable values, and loosely typed handlers — that interact combinatorially to produce a vast space of possible states, most of which are invalid.

Consider a standard data-fetching component. The common approach models it as `{ isLoading: boolean; isError: boolean; data: T | null; error: Error | null }`. This creates sixteen possible combinations of those four fields. Only four or five of those combinations are valid. The remaining eleven are illegal states — loading with data, error without an error object, data and error simultaneously — that the type system permits, the component must silently tolerate, and the developer must mentally track.

This pattern compounds across a page. Ten components with three boolean flags each produce 59,049 possible combinations. No developer can reason about that state space. No test suite can cover it. Bugs hide in the combinations nobody anticipated, surfacing as blank screens, stale data, or impossible UI states that are difficult to reproduce and painful to debug.

The root cause is that React's prop model, as conventionally used, does not distinguish between states — it describes fields. Fields combine. States select.

---

## The Pattern

This architecture replaces field-based props with variant-based props. Every component receives a single discriminated union (DU) that enumerates the exact states the component can occupy. Each variant carries only the data and handlers relevant to that state. The component body is a switch expression that pattern-matches on the status discriminant and renders the appropriate output.

The architecture has six structural layers.

**The Foundation Layer** provides `Option<T>` and `Result<T, E>` types that replace `null`, `undefined`, and untyped exceptions. These are the primitives that make the upper layers possible.

**The Query Layer** owns server state. TanStack Query remains responsible for fetching, caching, deduplication, abort signals, retries, invalidation, and refetching. Query hooks expose server state as `AsyncState<T, E>` instead of boolean matrices.

**The Elmish Layer** owns feature behavior. Local feature state lives in a `Model`. User and system events are represented as `Msg` values. A pure `update(model, msg)` function returns `[nextModel, Cmd[]]`. An `init` function returns the initial model and mount-time commands. A `subscriptions` function derives active external event sources from the current model. Commands describe side effects as data; they do not perform them.

**The Effect Runner Layer** interprets commands and manages subscriptions. It runs mutations, invalidates queries, refetches, navigates, shows toasts, focuses elements, copies text, starts streams, and dispatches follow-up messages. Effects are imperative, but they are centralized and explicit.

**The Hook Layer** orchestrates route state, query state, Elmish model state, mutations, and effect runners. It transforms raw inputs into fully resolved discriminated unions for every component on the page. Page hooks coordinate; child hooks derive props.

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

## Resolving Many AsyncStates

Real pages rarely depend on one endpoint. A story detail view may need story metadata, chapter lists, chapter summaries, statistics, vocabulary, AI pulse reports, chat threads, and permission data. If each endpoint exposes `idle | loading | error | empty | success`, the raw state space grows combinatorially.

Five endpoints with five states each produce 3,125 possible combinations. Six endpoints produce 15,625. A component should not reason about that directly.

The solution is a resolver: a pure function that compresses many `AsyncState` machines into one resolved state machine according to a single dominance policy.

```typescript
type ResolvedAsyncState<T, E> =
  | { status: 'loading' }
  | { status: 'error'; errors: E[] }
  | { status: 'empty' }
  | { status: 'success'; data: T }

function resolveAsyncStates<T extends Record<string, unknown>, E>(
  states: { [K in keyof T]: AsyncState<T[K], E> },
): ResolvedAsyncState<T, E> {
  const errors: E[] = []
  const data = {} as Partial<T>
  let hasEmpty = false

  for (const key in states) {
    const state = states[key]

    switch (state.status) {
      case 'idle':
      case 'loading':
        return { status: 'loading' }
      case 'error':
        errors.push(state.error)
        break
      case 'empty':
        hasEmpty = true
        break
      case 'success':
        data[key] = state.data.unwrap().unwrap()
        break
    }
  }

  if (errors.length > 0)
    return { status: 'error', errors }

  if (hasEmpty)
    return { status: 'empty' }

  return { status: 'success', data: data as T }
}
```

The default policy is:

```text
loading > error > empty > success
```

If any required state is still idle or loading, the combined state is loading. If none are loading but one or more failed, the combined state is error. If none failed but one or more are empty, the combined state is empty. Only when every required state succeeds does the resolver return success with a fully typed data object.

In practice:

```typescript
function useStoryOverviewProps(args: {
  storyState: AsyncState<ChapterListResponse, ApiError>
  summaryState: AsyncState<ChapterSummaryResponse, ApiError>
  statsState: AsyncState<StoryStatsResponse, ApiError>
  onRetryStats: () => void
  onRetrySummary: () => void
}): StoryOverviewProps {
  const resolved = resolveAsyncStates({
    story: args.storyState,
    summary: args.summaryState,
    stats: args.statsState,
  })

  switch (resolved.status) {
    case 'loading':
      return { status: 'loading' }

    case 'error':
      return {
        status: 'error',
        headline: 'Error',
        title: 'Failed to fetch story info',
        description: 'Something went wrong. The server might be experiencing issues.',
        onRetryStats: args.onRetryStats,
        onRetrySummary: args.onRetrySummary,
      }

    case 'empty':
      return {
        status: 'empty',
        badge: toStatusBadgeVariant('Ongoing'),
        startedText: 'N/A',
        titleText: 'N/A',
      }

    case 'success':
      return {
        status: 'ready',
        badge: toStatusBadgeVariant(resolved.data.story.storyStatus),
        startedText: `STARTED ${formatDistanceToNow(
          resolved.data.story.storyLastUpdated,
          { addSuffix: true },
        )}`,
        titleText: resolved.data.story.storyTitle,
        summaryText: resolved.data.summary.summary,
        stats: resolved.data.stats,
      }
  }
}
```

The resolver removes the need for every page hook to manually coordinate every endpoint state. A component can depend on five or six endpoints without inheriting a five- or six-dimensional state space. Endpoint composition becomes algebraic instead of procedural.

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

## Elmish Feature Behavior

DU props model render states. `AsyncState` models server-data states. For complex features, user behavior should be modeled just as explicitly.

The Elmish layer introduces four types and two functions.

**`Model`** is the feature's local state: selected IDs, open modals, form values, draft input, active tabs, optimistic UI markers. It should store intent and local interaction state, not server data that TanStack Query already owns.

**`Msg`** is every event the feature understands. Messages are split into two categories:

- **`ExternalMsg`** — messages components can dispatch: user clicks, form input changes, keyboard shortcuts, modal open/close requests, item selections.
- **`InternalMsg`** — messages only the effect runner dispatches: mutation success/failure results, stream events, timer completions, subscription events.

The full `Msg` is the union of both. Components receive a `Dispatch<ExternalMsg>` that only accepts user-facing messages. The effect runner receives the full `dispatch` that accepts any `Msg`. The type system prevents components from firing internal messages that would corrupt the state machine.

```typescript
type ExternalMsg =
  | { type: 'chapterSelected'; chapterId: string }
  | { type: 'newChapterModalOpened' }
  | { type: 'newChapterModalClosed' }
  | { type: 'chapterTitleChanged'; value: string }
  | { type: 'createChapterSubmitted' }

type InternalMsg =
  | { type: 'createChapterSucceeded' }
  | { type: 'createChapterFailed'; error: ApiError }
  | { type: 'extractionProgress'; data: ExtractionEvent }
  | { type: 'sseDisconnected' }

type Msg = ExternalMsg | InternalMsg

// Components only see this
type Dispatch = (msg: ExternalMsg) => void
```

**`Cmd`** is every side effect the feature requests: run a mutation, invalidate a query, refetch data, navigate, show a toast, focus an element, copy to clipboard, start an SSE stream, cancel a stream, or emit analytics.

```typescript
type Cmd =
  | { type: 'createChapter'; title: string; content: string }
  | { type: 'invalidateStory'; storyId: string }
  | { type: 'toastSuccess'; title: string; description: string }
  | { type: 'toastError'; title: string; description: string }
  | { type: 'navigate'; to: string }
  | { type: 'focusElement'; selector: string }
  | { type: 'copyToClipboard'; text: string }
```

**`Sub`** is every external event source the feature listens to. Subscriptions are derived from the current model — when the model changes, the active subscriptions change. The subscription runner manages lifecycles automatically.

```typescript
type Sub<Msg> =
  | { type: 'keyboard'; key: string; msg: Msg }
  | { type: 'interval'; ms: number; msg: Msg }
  | { type: 'sse'; url: string; onMessage: (event: MessageEvent) => Msg; onDisconnect: Msg }
  | { type: 'visibilityChange'; onVisible: Msg; onHidden: Msg }
  | { type: 'windowResize'; onResize: (width: number, height: number) => Msg }
```

### Init

Elm's `init` returns `[Model, Cmd[]]`, not just a model. Some features need side effects on mount — start a WebSocket, prefetch related data, fire an analytics event, focus an input. The init function formalizes this.

```typescript
function init(storyId: string): readonly [Model, Cmd[]] {
  return [
    {
      storyId,
      selectedChapterId: None,
      modalOpen: false,
      chapterTitle: '',
      extractionRunning: false,
    },
    Cmd.of(
      { type: 'focusElement', selector: '[data-autofocus]' },
    ),
  ]
}
```

Mount-time effects flow through the same command pipeline as everything else. No separate `useEffect` for initialization. No special case. The init function is pure — given the same inputs it returns the same model and command list.

### Update

The pure update function owns all state transitions:

```typescript
function update(model: Model, msg: Msg): readonly [Model, Cmd[]] {
  switch (msg.type) {
    case 'chapterSelected':
      return [{ ...model, selectedChapterId: Some(msg.chapterId) }, Cmd.none]

    case 'newChapterModalOpened':
      return [
        { ...model, modalOpen: true },
        Cmd.of({ type: 'focusElement', selector: '[data-chapter-title-input]' }),
      ]

    case 'newChapterModalClosed':
      return [{ ...model, modalOpen: false, chapterTitle: '' }, Cmd.none]

    case 'chapterTitleChanged':
      return [{ ...model, chapterTitle: msg.value }, Cmd.none]

    case 'createChapterSubmitted':
      return [
        model,
        Cmd.of({ type: 'createChapter', title: model.chapterTitle, content: '' }),
      ]

    case 'createChapterSucceeded':
      return [
        { ...model, modalOpen: false, chapterTitle: '' },
        Cmd.of(
          { type: 'toastSuccess', title: 'Chapter created!', description: 'Happy writing!' },
          { type: 'invalidateStory', storyId: model.storyId },
        ),
      ]

    case 'createChapterFailed':
      return [
        { ...model, modalOpen: false },
        Cmd.of(
          { type: 'toastError', title: 'Failed to create chapter', description: msg.error.detail },
        ),
      ]

    case 'extractionProgress':
      return [{ ...model, /* update extraction state */ }, Cmd.none]

    case 'sseDisconnected':
      return [{ ...model, extractionRunning: false }, Cmd.none]
  }
}
```

The update function is pure. It does not call APIs, navigate, show toasts, or mutate caches. It only returns the next model and a list of command values. This makes feature behavior testable without React, without the DOM, and without network mocks.

```typescript
const [next, cmds] = update(model, { type: 'createChapterSubmitted' })

expect(next).toEqual(model)
expect(cmds).toEqual([
  { type: 'createChapter', title: model.chapterTitle, content: '' },
])
```

### Subscriptions

Subscriptions model external event sources that produce messages. They are derived from the current model — when the model changes, the subscription runner diffs the active subscriptions and starts or stops them accordingly.

```typescript
function subscriptions(model: Model): Sub<Msg>[] {
  const subs: Sub<Msg>[] = [
    { type: 'keyboard', key: 'Escape', msg: { type: 'newChapterModalClosed' } },
  ]

  if (model.extractionRunning) {
    subs.push({
      type: 'sse',
      url: `/api/extractions/${model.storyId}/stream`,
      onMessage: (e) => ({ type: 'extractionProgress', data: JSON.parse(e.data) }),
      onDisconnect: { type: 'sseDisconnected' },
    })
  }

  return subs
}
```

The subscription list is reactive to the model. When `extractionRunning` becomes true, the SSE subscription activates. When it becomes false, the subscription disappears and the stream closes. No manual cleanup. No `useEffect` dependency arrays. The model drives which external sources are active, and the subscription runner manages the lifecycle.

This replaces ad-hoc `useEffect` blocks scattered across the hook layer. Every external event source — keyboard shortcuts, timers, server-sent events, visibility changes, resize observers — is declared in one place, derived from one source of truth.

### Cmd Helpers

Small ergonomic utilities that compound across the codebase:

```typescript
const Cmd = {
  none: [] as Cmd[],
  of: (...cmds: Cmd[]): Cmd[] => cmds,
}

// Without helpers
return [{ ...model, modalOpen: false }, []]

// With helpers — intentional, readable
return [{ ...model, modalOpen: false }, Cmd.none]

// Multiple commands — clean, scannable
return [model, Cmd.of(
  { type: 'createChapter', title: model.chapterTitle, content: '' },
  { type: 'toastSuccess', title: 'Created!', description: 'Happy writing!' },
)]
```

`Cmd.none` is more intentional than `[]`. It says "I deliberately chose to produce no side effects" rather than "I returned an empty array." Same value, different signal to the reader.

---

## Command Batches and useElmish

Commands should be executed once. They are not long-lived model state. The `useElmish` hook stores the model, manages command batching with monotonically increasing IDs, and runs the subscription lifecycle.

```typescript
type CommandBatch<Cmd> = {
  id: number
  cmds: Cmd[]
}

function useElmish<Model, Msg, Cmd>(
  init: () => readonly [Model, Cmd[]],
  update: (model: Model, msg: Msg) => readonly [Model, Cmd[]],
  subscriptions?: (model: Model) => Sub<Msg>[],
) {
  const [state, setState] = useState(() => {
    const [model, initCmds] = init()
    return {
      model,
      batch: initCmds.length > 0
        ? Some({ id: 0, cmds: initCmds } as CommandBatch<Cmd>)
        : None as Option<CommandBatch<Cmd>>,
      nextBatchId: 1,
    }
  })

  const dispatch = useCallback((msg: Msg) => {
    setState((current) => {
      const [model, cmds] = update(current.model, msg)
      return {
        model,
        batch: cmds.length > 0
          ? Some({ id: current.nextBatchId, cmds })
          : None,
        nextBatchId: current.nextBatchId + 1,
      }
    })
  }, [update])

  const clearBatch = useCallback((id: number) => {
    setState((current) => {
      if (current.batch.isSome() && current.batch.unwrap().id === id) {
        return { ...current, batch: None }
      }
      return current
    })
  }, [])

  // Subscription lifecycle management
  const activeSubsRef = useRef<Map<string, () => void>>(new Map())

  useEffect(() => {
    if (!subscriptions) return

    const desired = subscriptions(state.model)
    const desiredKeys = new Set(desired.map(subKey))
    const currentKeys = new Set(activeSubsRef.current.keys())

    // Tear down removed subscriptions
    for (const key of currentKeys) {
      if (!desiredKeys.has(key)) {
        activeSubsRef.current.get(key)?.()
        activeSubsRef.current.delete(key)
      }
    }

    // Start new subscriptions
    for (const sub of desired) {
      const key = subKey(sub)
      if (!activeSubsRef.current.has(key)) {
        const cleanup = startSubscription(sub, dispatch)
        activeSubsRef.current.set(key, cleanup)
      }
    }

    return () => {
      for (const cleanup of activeSubsRef.current.values()) {
        cleanup()
      }
      activeSubsRef.current.clear()
    }
  }, [state.model, subscriptions, dispatch])

  return [state.model, dispatch, state.batch, clearBatch] as const
}
```

This gives the effect runner a precise contract:

- No batch means no work.
- A batch ID identifies one command list.
- Commands inside the batch run sequentially.
- The runner clears the batch after executing it.
- Init commands are batch ID 0 — they flow through the same pipeline.
- Subscriptions are automatically started and stopped based on model changes.

---

## Query-to-Msg Bridge

When an `AsyncState` transitions from loading to success or error, that is an event. But without a bridge, it is handled through ad-hoc `useEffect` blocks watching `state.status` — imperative React leaking into what should be message-driven flow.

The bridge converts query state transitions into messages:

```typescript
function useQueryMsg<T, E, Msg>(
  state: AsyncState<T, E>,
  toMsg: {
    onSuccess?: (data: T) => Msg
    onError?: (error: E) => Msg
  },
  dispatch: (msg: Msg) => void,
) {
  const prevStatus = useRef(state.status)

  useEffect(() => {
    if (prevStatus.current !== state.status) {
      if (state.status === 'success' && toMsg.onSuccess) {
        dispatch(toMsg.onSuccess(state.data.unwrap().unwrap()))
      }
      if (state.status === 'error' && toMsg.onError) {
        dispatch(toMsg.onError(state.error))
      }
      prevStatus.current = state.status
    }
  }, [state.status])
}
```

Now query state transitions become messages flowing into the update function. The update function decides what to do — update the model, emit commands, trigger follow-up actions. No scattered `useEffect` blocks watching individual query statuses. One bridge per query, all behavior centralized in `update`.

```typescript
// In the page hook
useQueryMsg(storiesState, {
  onError: (error) => ({ type: 'storiesLoadFailed', error }),
}, dispatch)

// In the update function
case 'storiesLoadFailed':
  return [model, Cmd.of(
    { type: 'toastError', title: 'Failed to load stories', description: msg.error.detail },
  )]
```

---

## Effect Runners

An effect runner is the imperative interpreter for `Cmd[]`. It is the only place where commands become real side effects.

```typescript
function useStoryDetailEffectRunner(args: {
  batch: Option<CommandBatch<Cmd>>
  clearBatch: (id: number) => void
  dispatch: (msg: Msg) => void
  createChapter: (payload: CreateChapterRequest) => Promise<unknown>
  queryClient: QueryClient
  success: (title: string, description: string) => void
  error: (title: string, description: string) => void
  navigate: (to: string) => void
}) {
  useEffect(() => {
    if (args.batch.isNone()) return

    const { id, cmds } = args.batch.unwrap()

    async function run() {
      for (const cmd of cmds) {
        switch (cmd.type) {
          case 'createChapter':
            try {
              await args.createChapter({
                title: cmd.title,
                content: cmd.content,
              })
              args.dispatch({ type: 'createChapterSucceeded' })
            } catch (e) {
              args.dispatch({
                type: 'createChapterFailed',
                error: e as ApiError,
              })
            }
            break

          case 'invalidateStory':
            await args.queryClient.invalidateQueries({
              queryKey: storyKeys.detail(cmd.storyId),
            })
            break

          case 'toastSuccess':
            args.success(cmd.title, cmd.description)
            break

          case 'toastError':
            args.error(cmd.title, cmd.description)
            break

          case 'navigate':
            args.navigate(cmd.to)
            break

          case 'focusElement':
            document.querySelector(cmd.selector)?.focus()
            break

          case 'copyToClipboard':
            await navigator.clipboard.writeText(cmd.text)
            break
        }
      }

      args.clearBatch(id)
    }

    void run()
  }, [args.batch])
}
```

Effect runners should be thin. They should not decide business rules. They should not compute component props. They should not contain feature policy. Their job is to execute the commands produced by `update` and dispatch follow-up messages — always `InternalMsg` — when effects complete.

Note that the effect runner dispatches `InternalMsg` values (`createChapterSucceeded`, `createChapterFailed`). Components dispatch `ExternalMsg` values (`createChapterSubmitted`, `chapterTitleChanged`). The type boundary ensures each side only emits the messages it should.

---

## Data Fetching With TanStack Query

Data fetching remains declarative. Full Elmish does not mean every fetch becomes an imperative command. TanStack Query should continue to own server state.

The rule:

```text
Model stores query inputs.
TanStack Query owns fetched data.
update changes the model or emits commands.
queries react to the model.
commands handle imperative effects.
```

For example, the selected chapter is local feature state:

```typescript
type Model = {
  selectedChapterId: Option<string>
}
```

The query hook uses that model value as input:

```typescript
function useChapterSummary(chapterId: Option<string>) {
  const api = useApi()
  const id = chapterId.unwrapOr('__none__')

  const result = useQuery<ChapterSummaryResponse, ApiError>({
    queryKey: chapterKeys.summary(id),
    queryFn: ({ signal }) =>
      unwrapResultAsync(
        api.chapter.summarizeChapter(id, requestOptions({ signal })),
      ),
    enabled: chapterId.isSome(),
  })

  return [toAsyncState(result), result.refetch] as const
}
```

When the user selects a chapter, the view dispatches a message:

```typescript
dispatch({ type: 'chapterSelected', chapterId })
```

The update function changes the model:

```typescript
case 'chapterSelected':
  return [{ ...model, selectedChapterId: Some(msg.chapterId) }, Cmd.none]
```

The query reacts automatically because its input changed:

```typescript
const [summaryState, refetchSummary] =
  useChapterSummary(model.selectedChapterId)
```

Server state flows downward through query hooks as `AsyncState`. User intent flows upward through messages. Imperative work flows through commands. Query transitions flow through the query-to-msg bridge.

Use commands for:

- mutations
- query invalidation
- query refetching
- prefetching
- navigation
- toasts
- focus management
- clipboard operations
- downloads
- streaming and cancellation
- analytics

Do not use commands for ordinary declarative reads. Queries are subscriptions to server state. Commands are imperative actions.

---

## The Hook Layer: Orchestration and State-to-Props Transformation

Page hooks are the orchestration layer. They compose route params, query hooks, Elmish model state, query-to-msg bridges, mutations, effect runners, and child prop derivation hooks.

```typescript
function useStoryDetailPage(): StoryDetailPageProps {
  const { storyId } = useSearch({ from: '/app/stories/$storyId' })
  const navigate = useNavigate()

  // Elmish core
  const [model, dispatch, batch, clearBatch] = useElmish(
    () => init(storyId),
    update,
    subscriptions,
  )

  // Server state
  const [storyState, refetchStory] = useStoryChapters(storyId)
  const [statsState, refetchStats] = useStoryStats(storyId)
  const [summaryState, refetchSummary] =
    useChapterSummary(model.selectedChapterId)
  const bookPulse = useBookPulse(storyId)

  // Query-to-Msg bridges
  useQueryMsg(storyState, {
    onError: (e) => ({ type: 'storiesLoadFailed', error: e }),
  }, dispatch)

  // Mutations
  const createChapter = useCreateChapter(storyId)
  const queryClient = useQueryClient()
  const toast = useToast()

  // Effect runner
  useStoryDetailEffectRunner({
    batch,
    clearBatch,
    dispatch,
    createChapter: createChapter.mutateAsync,
    queryClient,
    success: toast.success,
    error: toast.error,
    navigate: (to) => navigate({ to }),
  })

  // External dispatch for components (only ExternalMsg allowed)
  const externalDispatch: Dispatch = dispatch

  // Child prop derivation — pure transformations
  const storyHeader = useStoryHeaderProps({
    chaptersState: storyState,
    chapterTitle: model.chapterTitle,
    modalOpen: model.modalOpen,
    onChapterTitleChange: (value) =>
      externalDispatch({ type: 'chapterTitleChanged', value }),
    onModalOpenChange: (open) =>
      externalDispatch(open
        ? { type: 'newChapterModalOpened' }
        : { type: 'newChapterModalClosed' }),
    onNavigateToLibrary: () =>
      externalDispatch({ type: 'navigateToLibraryRequested' }),
    onNewChapter: () =>
      externalDispatch({ type: 'createChapterSubmitted' }),
    onRetry: refetchStory,
  })

  const storyOverview = useStoryOverviewProps({
    storyState,
    summaryState,
    statsState,
    onRetryStats: refetchStats,
    onRetrySummary: refetchSummary,
  })

  const chapterList = useChapterListProps({
    chaptersState: storyState,
    selectedChapterId: model.selectedChapterId,
    onRetry: refetchStory,
    onChapterClick: (chapterId) =>
      externalDispatch({ type: 'chapterSelected', chapterId }),
  })

  return { storyHeader, storyOverview, chapterList, bookPulse }
}
```

The page hook coordinates, but it does not render. It delegates:

- server data to query hooks
- query transitions to the query-to-msg bridge
- local transitions to `update`
- effects to the effect runner
- external events to subscriptions
- endpoint state composition to `resolveAsyncStates`
- component prop derivation to child hooks
- rendering to components

Child prop hooks are pure transformations. Raw state enters, a fully resolved variant exits. The component never sees the raw state. It never makes decisions. It receives a verdict and renders it.

### Composing Item-Level State Machines

Individual items within a list each have their own state machine, resolved by child prop hooks.

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
function StoryDetailPage() {
  const { storyHeader, storyOverview, chapterList, bookPulse } = useStoryDetailPage()

  return (
    <div>
      <StoryHeader {...storyHeader} />
      <StoryOverview {...storyOverview} />
      <ChapterList {...chapterList} />
      <BookPulse {...bookPulse} />
    </div>
  )
}
```

No logic. No conditionals. No imports beyond the components and the hook. The page is a pure composition of resolved state machines.

---

## Data Flow Summary

The complete data flow through the architecture:

```text
User Event
  → Component dispatches ExternalMsg
  → update(model, msg) returns [nextModel, Cmd[]]
  → Model change triggers query input change
  → TanStack Query refetches automatically
  → AsyncState updates
  → Query-to-Msg bridge dispatches InternalMsg (if transition occurred)
  → update(model, msg) handles the transition
  → Command batch triggers effect runner
  → Effect runner executes Cmd[] (mutations, toasts, navigation, etc.)
  → Effect runner dispatches InternalMsg on completion
  → update(model, msg) handles the result
  → Page hook derives child props via resolveAsyncStates + child hooks
  → Components receive resolved DU props
  → Components switch on status and render

External Events
  → Subscriptions derived from Model
  → Subscription runner starts/stops based on model diffs
  → External event fires
  → Subscription maps event to Msg
  → Flows into update like any other message
```

Every arrow in this flow is typed. Every transition is explicit. Every side effect is a command value before it becomes an action. The complete state at any moment is the Model plus the AsyncState values plus the resolved DU props tree — all serializable, all inspectable, all deterministic.

---

## Architectural Properties

### Linear Complexity Scaling

In conventional React, complexity grows combinatorially — each optional prop multiplies the implicit state space. With DU props, complexity grows linearly. Ten components with four variants each produce forty total states, not a combinatorial explosion. Adding a component adds its variants to the count without multiplying against existing components.

### Endpoint State Compression

Components that depend on many endpoints do not inherit the full product of every endpoint's state machine. `resolveAsyncStates` compresses many `AsyncState` values into one resolved state according to a central policy. Six endpoints do not produce 15,625 UI branches; they produce `loading | error | empty | success`.

### Self-Documenting Contracts

The props type is the complete contract. A new developer reads a component's DU and immediately knows every state it can occupy, every piece of data each state requires, and every action available in each state. The `Msg` union documents every event the feature handles. The `Cmd` union documents every side effect the feature can produce. No tribal knowledge required.

### Compiler-Enforced Exhaustiveness

Adding a new variant to a DU causes every consumer to fail compilation until the new case is handled. Adding a new `Msg` variant breaks the `update` function until the new case is handled. Adding a new `Cmd` variant breaks the effect runner until the new case is handled. The compiler finds every call site automatically.

### Isolated State Machines

Components are independent state machines. A change to one component's variant set does not affect other components. The interaction between components happens in the hook layer, where state-to-props transformation is explicit and centralized, not in the component layer where it would be distributed and implicit.

### Pure Testability

Init functions are pure — given inputs, assert the initial model and commands. Update functions are pure — given a model and message, assert the next model and command list. Child prop hooks are pure — given raw state, assert resolved variants. Components are pure renderers — given a variant, assert JSX output. The imperative layer is isolated in effect runners, which can be integration-tested separately.

### Explicit Side Effects

Side effects are represented as command values before they are executed. Navigation, mutations, toasts, invalidation, focus, clipboard, downloads, streams, and analytics are not hidden inside callbacks scattered through the tree. They are visible in the `Cmd` union and interpreted in one place.

### Explicit External Events

External event sources are declared in the `subscriptions` function, derived from the model, and managed by the subscription runner. No ad-hoc `useEffect` blocks for keyboard listeners, timers, or streams. Every external event source is visible in one place.

### Snapshot Debugging

At any moment, the complete UI state is the Elmish Model, the active AsyncState values, the latest command batch, and the resolved DU props tree. All of this can be serialized, logged, diffed, and replayed. Bug reports can include the exact model, message sequence, command list, and variant tree that produced the broken render, making reproduction deterministic.

### Message-Driven Architecture

Every state change traces back to a message. User actions are messages. Query transitions are messages. Effect completions are messages. Subscription events are messages. The update function is the single source of truth for how the feature responds to any event. This makes the feature's behavior auditable by reading one function.

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

8. **Multiple AsyncStates must be resolved before reaching component props.** A component that depends on several endpoints receives one resolved DU, not several raw query states. Use `resolveAsyncStates` or a feature-specific resolver.

9. **TanStack Query owns server state.** Do not copy fetched data into Elmish model state unless there is a specific reason. Store query inputs in the model; let query hooks own fetched data, caching, retries, abort signals, invalidation, and refetching.

10. **Feature behavior is modeled with `Model`, `Msg`, `init`, `update`, `Cmd`, and `subscriptions`.** User events and system events are messages. State transitions happen in a pure update function. Initialization returns a model and commands. Side effects are returned as command values. External event sources are declared as subscriptions derived from the model.

11. **Init and update functions must be pure.** No API calls, no navigation, no toasts, no cache mutation, no DOM effects, no timers, no logging that affects behavior. Given the same inputs, they must return the same outputs.

12. **Effect runners are the only command interpreters.** Mutations, query invalidation, refetching, navigation, toasts, focus, clipboard, downloads, streams, and analytics run in effect runners. They dispatch follow-up messages when they complete.

13. **Messages are split into External and Internal.** Components receive `Dispatch<ExternalMsg>` and can only dispatch user-facing messages. Effect runners and subscription runners dispatch `InternalMsg` for system events. The update function handles both. The type boundary prevents components from dispatching internal messages.

14. **Components emit messages or call message-shaped handlers.** Event handlers should be thin. They should not contain business logic. Prefer `dispatch({ type: '...' })` or prop callbacks that are already message adapters.

15. **Subscriptions are derived from the model.** External event sources (keyboard, timers, SSE, visibility, resize) are declared in a `subscriptions` function. The subscription runner manages lifecycles automatically. No ad-hoc `useEffect` blocks for external events.

16. **Query state transitions flow through the query-to-msg bridge.** When an AsyncState transitions from loading to success or error, the bridge dispatches a message into the update function. No ad-hoc `useEffect` blocks watching query status.

---

## Relationship to Existing Patterns

**The Elm Architecture (TEA).** This pattern is full Elm Architecture in React. `init` returns the initial model and commands. `update` takes a model and message and returns the next model and commands. `subscriptions` derives active external event sources from the model. `view` (components) pattern-matches on resolved props. Effect runners interpret commands and dispatch follow-up messages. The only Elm concept not present is the runtime — React, TanStack Query, and the `useElmish` hook fill that role.

**MVVM.** Page and child prop hooks serve as ViewModels, mediating between the Model (local Elmish state plus server state from TanStack Query) and the View (JSX). Unlike classical MVVM frameworks, there are no classes, no decorators, no framework abstractions — just functions.

**State Machines / Statecharts.** Each component's DU is a state machine definition. The Elmish update layer manages feature transitions. The pattern is compatible with but does not require formal statechart libraries like XState — the type system itself provides the guarantees.

**Functional Core, Imperative Shell.** The functional core is init, update, subscriptions, resolvers, prop derivation hooks, and component render functions. The imperative shell is the effect runner, subscription runner, query-to-msg bridge, and TanStack Query's mutation/query-client operations. The boundary between them is data: Msg, Model, Cmd, Sub, AsyncState, and DU props.

**Redux.** The `Msg` and `update` pair resembles actions and reducers, but the scope is feature-local by default. Commands make effects explicit without requiring global middleware. The ExternalMsg/InternalMsg split provides type-safe action boundaries that Redux's string-based action types cannot enforce. TanStack Query owns server state, so this pattern avoids storing remote data in a global client store.

**GraphQL / BFF Endpoints.** This pattern does not replace GraphQL's schema, resolver, and field-selection capabilities. It does remove one common motivation for adopting GraphQL too early: frontend chaos from coordinating many REST endpoints. `resolveAsyncStates` collapses many endpoint states into one UI state, while page-specific BFF endpoints remain available when network round-trips or response shape demand backend aggregation.

---

## When to Use This Pattern

This architecture is designed for stateful, interactive applications — editors, dashboards, creative tools, real-time interfaces, form-heavy workflows. Applications where the user is producing or manipulating rather than consuming.

It is most valuable in large applications, but it is worth practicing in small applications too. Small apps are where architectural discipline is cheap. If a project starts with loose booleans, nullable fields, hidden effects, and unmodeled events, that looseness hardens as the app grows. Refactoring later means rebuilding the foundations under existing features.

The lightweight version is enough for small apps:

- DU props for every meaningful component.
- `AsyncState` for every query.
- `resolveAsyncStates` when composing multiple endpoints.
- `Model`, `Msg`, `init`, `update`, `Cmd`, and `subscriptions` for page-level features, forms, modals, editors, chat panels, dashboards, and workflows.
- Plain presentational components for simple, stateless leaf UI.

It is not necessary for static content sites, marketing pages, or read-heavy applications where server rendering handles the dominant use case and interactivity is minimal. Even there, reusable interactive widgets can still benefit from DU props.

The investment is in upfront type design — defining the DU for each component, the Msg union for each feature, and the Cmd union for each effect surface before building. This cost is repaid through eliminated bug classes, self-documenting contracts, compiler-enforced completeness, explicit side effects, auditable behavior, and linear complexity scaling as the application grows.
