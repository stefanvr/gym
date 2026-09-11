# SvelteKit — learnings

**Read this when the project’s Tech specification names SvelteKit.** Nothing here is a choice.

## The generator overwrites your files, and the flag that stops the prompt does not stop the write

`sv create --no-dir-check` suppresses the *prompt*, not the *overwrite*. Observed on an earlier
project: it would have replaced that project's `README.md` with the template's, and its `.gitignore`
had to be appended to rather than swapped in.

**Scaffold into a temporary directory, then copy in what you want.** That is the general habit; this
is the tool that made it necessary.

## A generator's omissions are not decisions either

The template ships no `@types/node`, so anything importing a `node:` builtin — the test runner, and
the build configuration itself — runs correctly and fails `svelte-check`.

**A green test suite says nothing about this.** Only the type check does, which is the argument for
running one at all.

## Its `prepare` path can hide a failed config load inside a successful install

The generic npm/lifecycle warning lives in `node.md`. The SvelteKit-specific failure observed on a fresh scaffold was:

- `npm install` invoked the project's SvelteKit prepare/sync path
- loading the Svelte configuration raised `ERR_MODULE_NOT_FOUND` for the adapter
- SvelteKit reported that no usable Svelte config was found and continued with its default configuration
- the enclosing install still completed successfully

**Do not use the install exit code as evidence that the Svelte configuration loaded. Read the SvelteKit output and re-run the sync/prepare step after the configuration's imported dependencies exist.**
