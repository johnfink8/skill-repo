---
name: type-safety
description: "Use when (a) a type error needs fixing, (b) `Any`/`any`/`unknown`/`object` or any cast (`as`, `as unknown as X`, `cast`, `# type: ignore`) is about to be written or has appeared in code being reviewed, (c) you're designing the shape of data crossing a boundary (API, service, frontend↔backend, third-party input), (d) you're choosing between a naked dict/object and a structured schema (pydantic, zod, dataclass, interface), (e) you're setting up a new typed project or adjusting tsconfig/mypy/pyright strictness, or (f) the user is asking about typing principles. NOT needed for plain edits that don't introduce, modify, or interact with types."
---

# Type safety

Types catch bugs, document intent, and make refactors safe. They are not a tax to pay to make the checker happy — they're the most leverage you'll get for the time you invest in them.

## 1. Never silence a type error

If the type checker complains, it has either found a real bug or found a place where the types don't reflect reality. Both call for fixing something, not silencing the checker.

**TypeScript: `as` is almost never okay.** If you find yourself writing `foo as Bar`, stop and ask whether it's actually safe. The legitimate uses are narrow: bridging untyped JSON immediately after schema-validating it, narrowing after a runtime check the compiler can't see, casting from `unknown` inside a type-guard. Inside your own code, `as` means "I'm lying to the compiler" — almost always a bug or a missing type.

**TypeScript: `as unknown as X` is *never* okay.** Not "almost never" — never. The double-cast exists specifically to bypass TypeScript's structural check between unrelated types; reaching for it means you've told the compiler to stand down. This rule holds even at uncontrolled boundaries: if you're receiving an `unknown` from a third-party API or `JSON.parse`, the right move is `XSchema.parse(value)` (zod) — runtime validation, not compiler silencing. `as unknown as X` gives you neither type safety nor runtime safety; it's the worst of both worlds. If you find one in code under review, treat it as a bug.

**Python: `# type: ignore` is almost never okay.** Same rule as `as`. If you must, use `# type: ignore[specific-code]` not a bare `# type: ignore`, and leave a comment explaining the reason. `cast(X, value)` is the Python analogue of `as` — same standard applies.

## 2. `Any`, `unknown`, `object` are not a hierarchy — they're all admissions of defeat

There is a popular framing that goes `Any` < `unknown` < `object` < specific types, suggesting that `unknown` is the "good escape hatch." That framing is wrong in the cases that actually matter.

**If you own both ends of the wire, none of these are acceptable.** A function you wrote calling a function you wrote, in a service you wrote, talking to a database you control — there is no reason for `any`/`Any`/`unknown`/`object` to appear anywhere in that path. If they do, you've given up on type safety somewhere upstream and the badness is propagating.

**If you don't own both ends, they're excusable but not preferable.** Talking to a third-party API with no published types, parsing a JSON file someone else writes, receiving a webhook payload from a service whose schema you can't pin — fine, the value arrives as `unknown`. But that's the moment to **immediately** parse it with zod / pydantic / a dataclass, after which the rest of your code gets real types. The `unknown` lives in exactly one line: the input to your validator.

**`Any`/`any` is the worst of the three** because it silently propagates — once it touches your code, the checker stops helping everywhere downstream. Use `unknown` if you must use one.

## 3. Aim for full-stack type contracts

The types should be shared across the wire, not retyped on each side.

- **Next.js / fullstack TS**: keep shared types in a `types/` or `shared/` package and import on both client and server. Don't define `type User` once in the API route and again in the client — they will drift.
- **GraphQL**: codegen the types from the schema. `relay-compiler`, `graphql-codegen`, or equivalent — never hand-write the client types.
- **Python → TypeScript**: generate the TS client from your Python schemas (pydantic + `datamodel-code-generator`, FastAPI's OpenAPI export → `openapi-typescript`). The Python schema is the source; the TS types are derived.
- **TypeScript → Python**: less common, but the same principle — pick a source of truth and codegen the other side.
- **Between two services in different languages**: protobuf, OpenAPI, or JSON Schema as the lingua franca, with codegen on both sides.

The point is **one source of truth per data shape**, regenerated whenever it changes. Hand-maintained parallel type declarations are guaranteed to diverge — usually right when you're shipping a fix.

## 4. Structured types over naked dicts/objects

A function that takes `Dict[str, Any]` or `Record<string, unknown>` is a function that has opted out of type safety. The right shape is almost always:

- **Python**: pydantic models for anything crossing a boundary; `@dataclass` for plain internal records; `TypedDict` when you genuinely need dict semantics (rare).
- **TypeScript**: a real `interface` / `type` definition. For untrusted input, a zod schema with `.parse()` at the boundary.

Use these *liberally* — having 30 small pydantic models is fine and good. The cost is one class definition; the benefit is every consumer of that shape gets autocomplete, validation, and a checked refactor when the shape changes.

Specifically don't do:
- `def process(data: dict): ...` — what keys? what types? unknown until you read the body.
- `function handle(payload: Record<string, any>) { ... }` — same problem.
- `JSON.parse(body)` left as `any` — parse, then validate with zod, then assign to a typed variable.

## 5. Narrow at the boundary; trust internally

The escape hatches live at the edge — HTTP request bodies, env vars, CLI args, third-party JSON, file contents. At that edge:

1. Receive as `unknown` / `Any`.
2. Validate with zod / pydantic / hand-written guard.
3. Assign to a properly-typed variable.
4. From here on, the rest of the codebase sees real types.

Inside the validated region, no defensive re-checking. If `user.email` is typed `string`, don't `if (typeof user.email === 'string')` "just in case." That's noise that masks real validation gaps.

## 6. Prefer narrow types to broad ones

- `string` is worse than `"asc" | "desc"` is worse than an `enum`.
- `number` for an ID is worse than a branded `UserId`.
- `Record<string, T>` is worse than a real interface.
- `Optional[X]` is worse than two functions: one that takes `X`, one that handles the missing case.

The goal is to make illegal states unrepresentable. If a function takes a `string` that "must be a valid email", the type is wrong — make it `EmailAddress` (a branded type or a small class) constructed only via a validator.

## 7. Function signatures are the contract — write them explicitly

Public function signatures: meaningful parameter names, narrow types, **explicit return types** even when inference would work. The return annotation pins the contract; it's how you and the type checker catch "oh, this function now returns `T | undefined`" before it lands in production.

For private helpers, inference is fine.

## 8. Strict mode on, no exceptions

- TypeScript: `"strict": true` in tsconfig. No `strictNullChecks: false`, no `noImplicitAny: false`, no exception files.
- Python: pyright `strict` or mypy `--strict`. Configure once; never weaken per-file unless there's a documented migration in flight.

If a third-party library has bad types, fix it locally with a `.d.ts` declaration or a typed wrapper module — never weaken the project-wide config to accommodate one bad neighbor.

## 9. Don't over-engineer types

Types are tools, not puzzles. If you find yourself writing a 5-level conditional type to express "the return type depends on which string was passed in," consider whether two overloads — or two separate functions with clearer names — would be clearer. Cleverness in types costs the reader more than cleverness in code.

A good rule: if reading the type signature is harder than reading the function body, the types are wrong.

## Common failure modes

| Symptom | Fix |
|---|---|
| `Any`/`any` appears in code you own end-to-end | Real types — you have all the information |
| Types defined twice (frontend + backend) | Codegen from one source |
| `dict[str, Any]` as a function parameter | pydantic model or dataclass |
| `JSON.parse()` result used directly | zod-validate at the parse site |
| `foo as Bar` to make a test compile | Fix the underlying type or the test |
| `foo as unknown as Bar` anywhere | Always wrong — use a zod/pydantic validator instead |
| `# type: ignore` with no `[code]` and no comment | Specify the rule, explain why |
| Strict mode disabled "for this one file" | Fix the file, not the config |
| Five-level conditional type | Overload or split the function |
