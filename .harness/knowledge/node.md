# Node — learnings

**Read this when the project’s Tech specification names Node.** Nothing here is a choice; the
choice is spec-tech's.

## Installing a version is not selecting it

A fresh interactive shell resolves to the version manager's **default alias**. `.nvmrc` is read only
by an explicit `nvm use`. Install 24 while the default alias points at 20, and every one-shot command
runs 20 while `.nvmrc` and CI both say 24 — with nothing anywhere reporting the disagreement.

Two ways out, and they are not equivalent: `nvm use` in the project directory is scoped and reads
`.nvmrc`; `nvm alias default <v>` is **global** and hits every other project on the machine.

**Verify with `node -v` and `nvm alias default` separately.** They answer different questions — what
is running now, and what the next fresh shell will run — and either can be the wrong one.

The environment half of this — that a version manager loads only in an interactive shell — belongs to
the project's Setup Dev documentation, not here.

## A successful `npm install` can hide a failed lifecycle sub-operation

`npm install` may run project lifecycle scripts such as `prepare`. A successful install exit code therefore does not prove that every operation performed inside those scripts produced the intended project state: a tool invoked by the lifecycle script may report or internally recover from its own failure while the enclosing install still succeeds.

**Read lifecycle-script output when the project relies on generated/config-derived state, and verify that state directly rather than treating install exit 0 as sufficient evidence.**

Framework-specific examples and recovery steps belong in that framework's knowledge entry.

## `npm ci`, not `npm install`, when you did not mean to change anything

`ci` installs exactly what the lockfile says and fails if `package.json` and the lockfile disagree.
`install` quietly resolves something newer.
