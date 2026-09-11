# Playwright — learnings

**Read this when the project’s Tech specification names Playwright.** Nothing here is a choice.

## `--with-deps` depends on the environment; WSL and CI can require opposite choices

`npx playwright install --with-deps chromium` shells out to `sudo apt-get`. In a WSL shell there is
no stdin for the password prompt, so it **hangs rather than failing**, and nothing says what is being
waited for. Use the plain form:

```bash
npx playwright install chromium
```

**Observed under WSL:** the plain Chromium install can download and launch without adding system packages or invoking `sudo`. Verify this on the target development environment rather than assuming it holds everywhere.

**On typical hosted Linux CI runners, the opposite is often correct.** When passwordless sudo is available and the image lacks browser system libraries, `--with-deps` is appropriate. Verify the runner image/permissions rather than treating “local” and “CI” as universal environment classes.

## The web server must bind the address the tests poll

A dev or preview server left to itself binds `localhost`, which resolves to `::1` on some machines
and `127.0.0.1` on others — while a `webServer.url` written as literal IPv4 is polled as IPv4. When
the two disagree the server **starts healthily on an address nothing is watching**, and Playwright
waits out its whole timeout before reporting *"Timed out waiting 120000ms from config.webServer"*.
That names the symptom and hides every cause.

**It cannot reproduce locally**, where both names lead to the same place, which is what makes it
expensive: it only ever fails in CI.

Bind and poll the same literal address, and set `stdout: 'pipe'` and `stderr: 'pipe'` on the
`webServer`. Swallowed, the server's own output is the thing that would have said which address it
took.

## A CI-only failure needs a reporter that leaves evidence

Job logs and run artifacts both need repository admin rights through the API, so a CI-only failure is
diagnosable by exactly one person, in a browser. **Annotations are readable on a public repository
without credentials**, and Playwright's `github` reporter emits one per failure.

```ts
reporter: process.env['CI'] ? [['github'], ['list'], ['html', { open: 'never' }]] : [['list']]
```

Add `trace: 'retain-on-failure'` and `screenshot: 'only-on-failure'` too. All three cost nothing on a
passing run, and without them a failure that cannot be reproduced locally leaves nothing to look at.

## Proving an assertion can fail costs one environment variable

Where a test asserts something a build stamped, `GIT_DIR` pointing at nothing makes `git rev-parse`
fail while everything else proceeds normally:

```bash
GIT_DIR=/nonexistent npx playwright test    # the identifier test must FAIL here
```

It needs no source change, so there is nothing to remember to put back.
