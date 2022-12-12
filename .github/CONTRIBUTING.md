## Contributing to Mystbin!

First off, thanks for taking the time to contribute. It makes the service substantially better. :+1:

The following is a set of guidelines for contributing to the repository. These are guidelines, not hard rules.

## Good Bug Reports

Please be aware of the following things when filing bug reports.

1. Don't open duplicate issues. Please search your issue to see if it has been asked already. Duplicate issues will be closed.
2. When filing a bug about exceptions or tracebacks, please include the *complete* traceback. Without the complete traceback the issue might be **unsolvable** and you will be asked to provide more information.
3. Make sure to provide enough information to make the issue workable. The issue template will generally walk you through the process, but they are enumerated here as well:
    - A **summary** of your bug report. This is generally a quick sentence or two to describe the issue in human terms.
    - Guidance on **how to reproduce the issue**. Ideally, this should have a paste ID that allows us to run and see the issue for ourselves to debug. **Please make sure any of your tokens are not displayed**. If you cannot provide a paste ID, then let us know what the steps were, how often it happens, etc.
    - Tell us **what you expected to happen**. That way we can meet that expectation.
    - Tell us **what actually happens**. What ends up happening in reality? It's not helpful to say "it fails" or "it doesn't work". Say *how* it failed, do you get an error? Does it hang? How are the expectations different from reality?
    - Tell us **information about your environment**. What web browser(s) does this occur on, etc?

If the bug report is missing this information then it'll take us longer to fix the issue. We will probably ask for clarification, and barring that if no response was given then the issue will be closed.

## Submitting a Pull Request

Submitting a pull request is fairly simple, just make sure it focuses on a single aspect and doesn't manage to have scope creep, and it's probably good to go. It would be incredibly lovely if the style is consistent to that found in the project. This project follows PEP-8 guidelines (mostly) with a column limit of 125.
There are provided tool rules in `pyproject.toml` for `isort`, `black` and `pyright` when working on the backend side of things.
There are rules provided for prettier when working on the frontend  side of things.

There are actions that run on new PRs and if those checks fail then the PR will not be accepted.

NOTE: We do not provide `black` and `isort` in the requirements files for the backend. Feel free to install these yourself.

### Git Commit Guidelines

- Use present tense (e.g. "Add feature" not "Added feature")
- Limit all lines to 72 characters or fewer.
- Reference issues or pull requests outside the first line.
    - Please use the shorthand `#123` and not the full URL.

If you do not meet any of these guidelines, don't fret. Chances are they will be fixed upon rebasing but please do try to meet them to remove some workload.
