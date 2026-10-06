# Plan sections — definitions and arming

`/open` arms a subset; structural and campaign work arms all five.

| # | Section | Armed for | One-line test |
|---|---|---|---|
| 1 | Problem | always | Could the user have written this line themselves? |
| 2 | Mechanism | local + | Is every step attached to a named module/boundary? |
| 3 | Falsifiers | structural + | Would the named observation actually change the plan? |
| 4 | Cut list | structural + | Does the change retire anything? If not, why not? |
| 5 | Verification plan | local + | Are the commands named and ordered? |

## Falsifiers, done properly

A falsifier is an **observation that would prove the plan wrong** — not a
test that will pass. Weak: "tests will pass." Strong: "if the cache is the
cause, disabling it (`make build && CACHE=off ./bin/app`) changes the
latency numbers; if it does not, the plan's premise is wrong."

Three good falsifiers beat ten confirmations.

## The plan lives where?

Structural/campaign plans are filed under the campaign directory or
`docs/plans/` (never chat-only); local-change plans may live in the work
report. The queue entry links to the plan file.
