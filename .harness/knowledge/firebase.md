# Firebase and gcloud — learnings

**Read this when the project’s Tech specification names Firebase or Google Cloud.** Nothing here
is a choice.

## Every tool that authenticates does so independently

Observed failure class: `firebase` and `gcloud` can be authenticated as different identities on the same machine. Neither tool reports the other's identity, so a command issued through the wrong identity can look like a project permissions problem rather than an authentication mismatch.

**Check each tool's identity separately, never once for the machine:**

```bash
git config user.email
npx firebase login:list
gcloud auth list
```

## A gcloud configuration is machine-wide, not per-terminal

Where a machine carries two configurations — say a work one and a personal one — only one is live at
a time, for every terminal at once. Leaving the personal one active means work commands silently
target the personal project; leaving the work one active means the personal project's commands are
refused in a way that reads as *"it may not exist"*.

`gcloud config configurations list` shows both and which is live;
`gcloud config configurations activate <name>` switches.

## The error will not tell you which it was

Observed: a `describe` on a resource, run as the wrong account, returned *"Permission … denied on
resource … **(or it may not exist)**"*. Denied and absent are the same message, so the command
answers neither question.

**Establish the identity before running the check, because the check cannot establish it for you.** A
diagnostic run as the wrong identity is not a weak signal; it is no signal.

The corollary is worth more than the check: **before fixing an access problem, ask which identity is being refused.** Where the needed fact can be verified directly from the live service without authentication, that may be cheaper and more reliable than changing machine-wide credentials.
