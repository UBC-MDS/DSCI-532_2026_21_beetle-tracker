# Contributing to DSCI-532_2026_21_beetle-tracker

Thank you for your interest in contributing to the Japanese Beetle — Invasive Species Tracker project. This guide outlines how to propose changes to the project. For questions about the contribution process, please open an issue or contact a core group member.

## Fixing Typos

Small typos or grammatical errors in documentation may be edited directly using the GitHub web interface, so long as the changes are made in the source file.

- YES: you edit documentation in `.md` files or docstrings in `.py` files
- NO: you edit generated output files

## Prerequisites

Before you make a substantial pull request, you should always file an issue and make sure someone from the team agrees that it's a problem or desired feature. If you've found a bug, create an associated issue and describe:

- Steps to reproduce the bug
- Expected behavior
- Actual behavior
- Screenshots (if applicable)

## Pull Request Process

- We recommend that you create a Git branch for each pull request (PR)
- New code should follow the [PEP 8 style guide](https://peps.python.org/pep-0008/)
- Use descriptive commit messages
- We use docstrings for documentation - please include them for new functions
- Contributions with test cases are easier to accept
- Update `README.md` or relevant documentation if your changes affect how users interact with the dashboard
- In your pull request description, clearly explain what changes you've made and why

## Code Standards

- Follow PEP 8 for Python code formatting
- Write clear, descriptive variable and function names
- Include comments for complex logic
- Test your changes locally before submitting

## Code of Conduct

Please note that this project follows a [Code of Conduct](CODE_OF_CONDUCT.md) and by contributing to or otherwise participating in this project you agree to abide by its terms.


## M3 Retrospective & M4 Collaboration Norms

Based on feedback from the teaching team and LLM-assisted code review, we identified opportunities to improve team collaboration going into Milestone 4. One key area was work distribution. In M3, contributions were uneven, so for M4 we made a deliberate effort to ensure every team member had equal opportunity to contribute to the codebase. We also received feedback that some PRs were being merged without sufficient review, so in M4 we adopted a norm of requiring at least one other team member to review a PR before it is merged.

To better document our process, we shifted toward more atomic issues and PRs, making it easier to track individual contributions and decisions. We also recognized that our changelogs needed improvement, and for M4 we committed to writing more thorough and detailed changelogs with each release.

## Attribution
These contributing guidelines were adapted from the [dplyr contributing guidelines](https://github.com/tidyverse/dplyr/blob/main/.github/CONTRIBUTING.md).
