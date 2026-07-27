# CONTRIBUTING.md

## How to Contribute to ThriftLLM

Thank you for considering contributing to ThriftLLM! This project aims to be a high-quality, production-ready open-source library. We value correctness, maintainability, documentation, and measurable improvements.

### Development Philosophy

- Research before designing.
- Design before implementing.
- Benchmark before claiming wins.
- Document everything.
- Keep changes focused (one logical change per PR).
- Update `ROADMAP.md` at the end of every session.
- Never let documentation go out of sync.

### Getting Started

1. Fork the repo.
2. Create a feature branch (`git checkout -b feature/amazing-optimization`).
3. Make your changes.
4. Add/update tests and documentation.
5. Ensure all tests pass (`pytest`).
6. Submit a Pull Request.

### Pull Request Guidelines

- Title should be clear and imperative ("Add semantic cache with Redis backend").
- Include detailed description of changes, motivation, and any benchmarks.
- Link to any related issues or research papers.
- Update relevant documentation (README, ARCHITECTURE, ROADMAP).
- Add yourself to CONTRIBUTORS.md if desired.

### Code Standards

- Python 3.9+, type hints everywhere.
- Black + ruff for formatting/linting.
- Comprehensive docstrings (Google style).
- 90%+ test coverage for new code.
- All public APIs must have usage examples.

### Research & Benchmarks

Any new optimization must include:
- References to supporting research/papers.
- Before/after benchmarks (cost, latency, quality).
- Quality measurement methodology.

See `BENCHMARKS.md` for current results.

### Questions?

Open an issue with the `question` label or join discussions.

This project is maintained with the rigor of a systems engineer who despises technical debt.

Last updated: July 27, 2026
