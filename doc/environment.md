# Environment

**Purpose.** How to actually run this project on a real machine, and which parts of that are
non-negotiable versus merely how one person's setup happens to work.

**What belongs here.** Runtimes and where they live, shells, identity/credential setup that
affects commits, ports, paths, and any tooling behaviour that surprises.

**What doesn't.** Technical *choices* — which runtime, which test framework, which architecture —
belong in [tech-spec.md](tech-spec.md). This doc doesn't decide anything; it describes what's
true. That's why it's separate: tech-spec changes when the project changes, this changes when a
machine changes, and mixing the two makes both harder to trust.

**Write silent failures first.** A command that errors is self-correcting — you see it and fix it.
A command that quietly does the *wrong thing* is not, and that's the class of problem this
document exists for.

---

## Invariants

What must be true regardless of whose machine it is. These stay true when someone else joins, and
each one is a property a setup either satisfies or doesn't.

- **Node 20** or compatible (pinned in `.nvmrc`). CI (`deploy.yml`) already uses `actions/setup-node@v4`
  with `node-version: 20`; local dev must match it, not the OS package.
- `git commit` output must actually be signed/attributable correctly — a shell that produces a
  commit at all is not sufficient proof it did the right thing (see below).
- No GitHub pull requests for this repo, ever — branch, then merge straight to the integration
  branch (see [workflow.md](workflow.md)). This is a standing preference, not a technical
  constraint, but it's invariant across machines the same way the others are.

---

## This machine

Windows 11 host + WSL2 (Ubuntu 24.04), working directory visible to Windows tools as
`\\wsl.localhost\Ubuntu-24.04\home\stefanraaphorst\gym`. Two separate shells can reach this same
directory — a Windows-side Git Bash (MINGW64) pointed at the UNC path, and real WSL — and they are
**not interchangeable**, in ways that fail silently rather than with an error.

**`git commit` / `git push` must run inside real WSL, never Windows Git Bash, for two independent
reasons — either one alone would be enough to require it:**

1. **Wrong author, silently.** Windows-side git's global identity is the work account; WSL's is
   the private account that owns this repo. Committing through the Windows shell doesn't error —
   it just attributes the commit to the wrong person.
2. **Commit signing fails outright.** This repo signs commits over SSH via 1Password's
   `op-ssh-sign` helper (`gpg.format = ssh`). From the Windows-side shell that reliably fails with
   `1Password: failed to fill whole buffer` / `fatal: failed to write commit object` — it can't
   complete the 1Password approval from that context. WSL's git has no signing configured for this
   repo and just works.

Reach real WSL from a Windows-side tool with:

```
wsl.exe -d Ubuntu-24.04 -- bash -lc 'cd /home/stefanraaphorst/gym && git ...'
```

Calling `bash` directly from a Windows-side tool reaches Git Bash/MINGW64, which looks like a
normal shell and runs `git` just fine — that's what makes both failure modes above silent instead
of loud.

**Node lives in two places, on purpose.** The OS package (`apt`, Node 18.19.1) is the system
default and is what a bare `node`/`npm` resolves to; it's past its own EOL and below the Node ≥20
this project (and Playwright specifically) requires. Node 20 is installed via `nvm`
(`~/.nvm`), scoped to this user, and does not touch or replace the apt package — nothing else on
the machine depends on it. Because `.nvmrc` pins `20`, activate it explicitly per shell:

```
wsl.exe -d Ubuntu-24.04 -- bash -lc 'source ~/.nvm/nvm.sh && nvm use && cd /home/stefanraaphorst/gym && npm test'
```

`nvm use` alone (no argument) picks up `.nvmrc` automatically once you're already in the project
directory — the `cd` needs to happen before it, or it falls back to the `default` alias instead.

**A piped or subshelled `nvm` command doesn't stick.** `nvm install 20 | tail -10` runs `nvm`
inside the pipeline's subshell; the `PATH` change it makes is local to that subshell and is gone
the moment the pipe finishes, even though the install itself succeeded. Run `nvm use` as its own,
unpiped command whenever the next command in the same shell needs it on `PATH`.

**Background processes** (a local dev server for manual/visual testing) need the calling tool's
own backgrounding, not `&` inside the `wsl.exe` call — a one-shot `wsl.exe` invocation tears down
its children when it exits, so the server dies immediately while the launch command still looks
like it succeeded. Start it with the harness's background-run option, or `nohup ... &
disown` inside a persistent shell, and stop it by port (`fuser -k <port>/tcp`) rather than
`pkill -f <pattern>` — a broad `pkill -f` pattern can match the wrapping shell's own command line
(which literally contains the pattern text, since it was passed as a `-c` argument) and kill the
session that's running it.

**Quoting.** Constructing a multi-line script as an inline shell string — nested heredocs,
multi-line variable assignments, apostrophes inside `bash -lc '...'` — breaks in ways whose error
output points somewhere unrelated (or produces no error at all and silently truncates). Write the
script to a file with an editor/tool and execute that file instead.

---

## When someone else joins

The section above is tuned to one person's setup, and that's a deliberate trade: for a solo
project the specifics *are* the value, and a generic version would lose exactly the part worth
having.

It does not survive contact with a contributor whose environment differs. When that happens,
don't genericise it into vagueness — **promote whatever actually matters up into Invariants**, and
let each person's setup satisfy those however it does. Add a second "This machine" section rather
than merging them into a description that fits neither.

The invariants were always the shared part. The rest was only ever one machine's answer to them.
