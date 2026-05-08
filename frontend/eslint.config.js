import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'
import { defineConfig, globalIgnores } from 'eslint/config'

// ─── Option/Result discipline ───────────────────────────────
//
// These rules enforce the project-wide rule: anything possibly
// null/undefined is `Option<T>`; anything that can fail is
// `Result<T, E>`. Everything goes through oxide.ts chained
// methods.  Backsliding categories we ban:
//
//   1. Non-null assertions (`x!`)            → use `.expect()` / `match`
//   2. Importing the legacy hand-rolled combinator names from
//      shared/types (`isSome`, `getOrElse`, `tryCatch`, …)  →
//      use the chained methods on the value instead.
//   3. Tag comparisons against Option/Result discriminants
//      (`x._tag === "Some"`, …) → use `.isSome()` etc.
//
// The query/auth boundary helpers (`unwrapResultAsync`,
// `useAuthOrThrow`, `.expect()`, `.unwrap()`) are intentionally
// allowed — they are the documented escape hatches at the
// React-Query / programmer-error boundary.

const BANNED_COMBINATOR_NAMES = [
    'isSome',
    'isNone',
    'isOk',
    'isErr',
    'getOrElse',
    'getOrElseLazy',
    'getOrElseResult',
    'getOrElseResultLazy',
    'mapOption',
    'mapResult',
    'flatMapOption',
    'flatMapResult',
    'mapErr',
    'fold',
    'toNullable',
    'tryCatch',
    'tryCatchAsync',
    'unwrapOption',
    'unwrapResult',
    'resultToOption',
    'optionToResult',
    'orElseOption',
]

export default defineConfig([
    globalIgnores(['dist']),
    {
        files: ['**/*.{ts,tsx}'],
        extends: [
            js.configs.recommended,
            tseslint.configs.recommended,
            reactHooks.configs.flat.recommended,
            reactRefresh.configs.vite,
        ],
        languageOptions: {
            globals: globals.browser,
        },
        rules: {
            // Ban `x!` non-null assertions — they bypass the Option
            // discipline. Use `.expect("…")` at the boundary instead.
            '@typescript-eslint/no-non-null-assertion': 'error',

            // Ban legacy combinator names from any import path. The
            // chained method on the Option/Result value is the only
            // approved API.
            'no-restricted-syntax': [
                'error',
                {
                    selector:
                        'ImportSpecifier[imported.name=/^(' +
                        BANNED_COMBINATOR_NAMES.join('|') +
                        ')$/]',
                    message:
                        'Use the chained Option/Result method instead of the legacy combinator (e.g. `opt.unwrapOr(d)` not `getOrElse(opt, d)`).',
                },
                // Ban `x._tag === "Some" | "None" | "Ok" | "Err"` —
                // use `.isSome()` / `.isNone()` / `.isOk()` /
                // `.isErr()` instead. Domain tagged unions with
                // other discriminant values remain allowed.
                {
                    selector:
                        'BinaryExpression[operator=/^===?$/] > MemberExpression.left[property.name="_tag"] + Literal[value=/^(Some|None|Ok|Err)$/]',
                    message:
                        'Do not branch on Option/Result `_tag`. Use `.isSome()` / `.isNone()` / `.isOk()` / `.isErr()`.',
                },
            ],
        },
    },
    {
        // The shared/types.ts module IS the boundary that re-exports
        // oxide.ts. It does not consume the banned names itself, but
        // we exempt it defensively so future shims can be added
        // without fighting the linter.
        files: ['src/shared/types.ts'],
        rules: {
            'no-restricted-syntax': 'off',
        },
    },
])
