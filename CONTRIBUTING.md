# Contributing to prompt-ctx

Thank you for your interest in contributing! This document outlines the process and expectations.

## Apache 2.0 Contributor License Agreement

By contributing to this project, you agree that your contributions will be licensed under the Apache License, Version 2.0, the same license that covers the project.

All contributions are subject to the Developer Certificate of Origin (DCO). By submitting a pull request, you certify that:

1. The contribution was created in whole or in part by you and you have the right to submit it under the Apache 2.0 license; or
2. The contribution is based upon previous work that, to the best of your knowledge, is covered under an appropriate open source license and you have the right under that license to submit that work with modifications; or
3. The contribution was provided directly to you by some other person who certified (1) or (2) and you have not modified it.

## Development Setup

```bash
# Clone and set up
git clone https://github.com/zzszmyf/prompt-ctx.git
cd prompt-ctx
uv sync

# Run tests
uv run pytest

# Run a specific test file
uv run pytest tests/test_section.py -v
```

## Code Style

- Follow [PEP 8](https://peps.python.org/pep-0008/)
- Use type hints for all public APIs
- Keep functions small and focused
- Write docstrings for public modules, classes, and functions

## Pull Request Process

1. **Open an issue first** for significant changes to discuss the approach
2. **Fork the repository** and create a feature branch
3. **Add tests** for new functionality
4. **Ensure all tests pass** (`uv run pytest`)
5. **Update documentation** if adding or changing public APIs
6. **Sign off your commits** with `Signed-off-by: Your Name <you@example.com>`

## Commit Conventions

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add Anthropic adapter support
fix: handle empty context providers gracefully
docs: update README with new examples
test: add tests for conditional section matching
refactor: extract tokenizer to separate module
```

## Community

- Be respectful and inclusive
- Follow the [Code of Conduct](CODE_OF_CONDUCT.md)
- Help others learn and grow

## Questions?

Open a [GitHub Discussion](https://github.com/zzszmyf/prompt-ctx/discussions) or an issue.
