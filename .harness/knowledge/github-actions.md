# GitHub Actions — learnings

**Read this when the project’s Tech specification names GitHub Actions.** Nothing here is a choice.

## `actions/checkout` gives a real repository, and a clean one

A build that stamps the commit by asking git needs history to ask. `actions/checkout` produces a real
repository, so the build can — **assert that rather than assume it**: the smoke test should run in CI
and fail on `unknown`.

A CI checkout is also **clean by construction**, which is the only clean tree anybody can promise. A
build from a dirty tree stamps a commit that describes the history and not the files, and nothing
marks the difference.

## Run the checks on every branch, not only on the default one

A workflow triggered on the default branch alone means the first CI run of any change happens *after*
it is merged — so the default branch is where CI failures are discovered.

```yaml
on:
  push:
    branches: ['**']
```

Gate the publishing steps and jobs on the default branch instead, with
`if: github.ref_name == github.event.repository.default_branch`. Concurrency wants to be per branch as well, cancelling
superseded branch runs but never a run that is mid-deployment.

## Deploying is not the same as having deployed

Give the workflow a job after the deployment that fetches the published artefact and compares its
identifier to `github.sha`. A green deploy step means the upload succeeded, not that the right thing
is being served.

## Warnings that are not failures

A run can carry annotations about the Node version the *actions themselves* run on — GitHub's own
runtime, unrelated to the project's. Read which step failed before reading the loudest annotation:
the two are usually different, and the deprecation notice is the one that catches the eye.
