# GitHub Pages — learnings

**Read this when the project’s Tech specification names GitHub Pages.** Nothing here is a choice.

## The control API reports "not enabled" and "not allowed to ask" identically

`GET /repos/{owner}/{repo}/pages` returns **404 unauthenticated even for a public repository with
Pages live**. Trusting it reports a working deployment as broken, and there is no second reading that
distinguishes the two.

**Verify a deployment by fetching the artefact, not by asking the control API.** Fetch the page and
compare the build identifier it carries against the commit you expect. That is the check that can
only pass when the thing actually works.

**Put the identifier where one request can read it.** In a `<meta>` tag it is one `curl` and one
`grep`; inside the JavaScript bundle it needs a browser, which makes the check heavier than the thing
it is checking.

Three failures the fetch separates and the control API cannot:

| What the page says | What happened |
|---|---|
| no identifier at all | not our page — a 404, or a deployment from before the tag existed |
| `unknown` | built outside a repository, and the build exited 0 |
| a real but different commit | **the deployment did not fail; it served an older build** |

The third is the one worth having. Nothing else notices it.

## A just-published deployment is briefly a 404

Retry the fetch rather than treating the first answer as final — `curl --retry 10 --retry-delay 6
--retry-all-errors` is enough.

## Two settings only a person can change

Both are web-UI actions, and an agent that meets them appears to stall rather than to fail:

- **A private repository needs a paid plan** for Pages to serve it. The alternative is making the
  repository public, which publishes the code, every document and the whole history.
- **Pages must be enabled with its source set to GitHub Actions.** Until it is, `actions/deploy-pages`
  fails in a way that reads like a permissions problem rather than a missing setting.
