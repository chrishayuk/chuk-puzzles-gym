.PHONY: help install dev-install run run-docker build test test-cov check lint format security clean clean-build clean-all docker-build docker-run docker-stop docker-clean build publish publish-manual publish-test fly-deploy fly-logs fly-status example-telnet example-telnet-interactive example-telnet-sudoku example-telnet-kenken example-ws example-ws-interactive example-ws-sudoku example-ws-binary example-ws-tour example-ws-solve eval eval-sudoku eval-all eval-json list-games

# Variables
PYTHON := python3
PIP := $(PYTHON) -m pip
PYTEST := $(PYTHON) -m pytest
RUFF := ruff
MYPY := mypy
DOCKER_IMAGE := puzzle-arcade-server
DOCKER_TAG := latest
FLY_APP := puzzle-arcade-server

# Directories
SRC_DIR := src
TEST_DIR := tests
EXAMPLES_DIR := examples

# Default target
help:
	@echo "Puzzle Arcade Server - Available Commands"
	@echo "=========================================="
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install          - Install production dependencies"
	@echo "  make dev-install      - Install development dependencies"
	@echo ""
	@echo "Running:"
	@echo "  make run              - Run the server locally"
	@echo "  make run-docker       - Run the server in Docker"
	@echo ""
	@echo "Testing:"
	@echo "  make test             - Run tests"
	@echo "  make test-cov         - Run tests with coverage report"
	@echo "  make test-watch       - Run tests in watch mode"
	@echo "  make serve-coverage   - Serve HTML coverage report on localhost:8000"
	@echo ""
	@echo "Code Quality:"
	@echo "  make check            - Run all checks (lint + type check + test)"
	@echo "  make lint             - Run linter (ruff)"
	@echo "  make format           - Format code with ruff"
	@echo "  make format-check     - Check code formatting"
	@echo "  make typecheck        - Run type checker (mypy)"
	@echo "  make security         - Run security checks (bandit)"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build     - Build Docker image"
	@echo "  make docker-run       - Run Docker container"
	@echo "  make docker-stop      - Stop Docker container"
	@echo "  make docker-clean     - Remove Docker container and image"
	@echo "  make docker-shell     - Open shell in running container"
	@echo "  make docker-logs      - Show Docker container logs"
	@echo ""
	@echo "Build & Publishing:"
	@echo "  make build            - Build distribution packages"
	@echo "  make publish          - Build and publish to PyPI (via GitHub trusted publishing)"
	@echo "  make publish-manual   - Build and publish to PyPI (manual with twine)"
	@echo "  make publish-test     - Build and publish to TestPyPI"
	@echo ""
	@echo "Deployment:"
	@echo "  make fly-deploy       - Deploy to Fly.io"
	@echo "  make fly-logs         - View Fly.io logs"
	@echo "  make fly-status       - Check Fly.io status"
	@echo "  make fly-open         - Open app in browser"
	@echo "  make fly-ssh          - Open SSH session on Fly.io"
	@echo ""
	@echo "Examples:"
	@echo "  make example-telnet              - Run telnet client (browse mode)"
	@echo "  make example-telnet-interactive  - Run telnet client (interactive)"
	@echo "  make example-telnet-sudoku       - Run telnet client (Sudoku demo)"
	@echo "  make example-telnet-kenken       - Run telnet client (KenKen demo)"
	@echo "  make example-ws                  - Run WebSocket client (tour mode)"
	@echo "  make example-ws-interactive      - Run WebSocket client (interactive)"
	@echo "  make example-ws-sudoku           - Run WebSocket client (Sudoku demo)"
	@echo "  make example-ws-binary           - Run WebSocket client (Binary demo)"
	@echo "  make example-ws-tour             - Run WebSocket client (game tour)"
	@echo "  make example-ws-solve            - Run WebSocket client (solve mode)"
	@echo ""
	@echo "Evaluation:"
	@echo "  make eval             - Run evaluation harness (all games, 5 episodes)"
	@echo "  make eval-sudoku      - Evaluate Sudoku (10 episodes)"
	@echo "  make eval-all         - Evaluate all games (10 episodes each)"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean            - Remove generated files"
	@echo "  make clean-all        - Remove all generated files and caches"

# Setup & Installation
install:
	@echo "Installing production dependencies..."
	@if command -v uv >/dev/null 2>&1; then \
		uv pip install -e .; \
	else \
		$(PIP) install -e .; \
	fi

dev-install:
	@echo "Installing development dependencies..."
	@if command -v uv >/dev/null 2>&1; then \
		uv pip install -e ".[dev]"; \
	else \
		$(PIP) install -e ".[dev]"; \
	fi

# Running
run:
	@echo "Starting Puzzle Arcade Server..."
	@echo "Telnet:    telnet localhost 8023"
	@echo "TCP:       nc localhost 8024"
	@echo "WebSocket: ws://localhost:8025/ws"
	@echo "WS-Telnet: ws://localhost:8026/ws"
	@echo ""
	@if command -v uv >/dev/null 2>&1; then \
		PYTHONPATH=. uv run --with chuk-protocol-server chuk-protocol-server server-launcher -c config.yaml; \
	else \
		PYTHONPATH=. python -m chuk_protocol_server.server_launcher -c config.yaml; \
	fi

run-direct:
	@echo "Starting Puzzle Arcade Server (direct mode)..."
	$(PYTHON) -m chuk_puzzles_gym.server

# Testing
test:
	@echo "Running tests..."
	@if command -v uv >/dev/null 2>&1; then \
		PYTHONPATH=$(SRC_DIR) uv run pytest $(TEST_DIR) -v; \
	else \
		PYTHONPATH=$(SRC_DIR) $(PYTEST) $(TEST_DIR) -v; \
	fi

test-cov coverage:
	@echo "Running tests with coverage..."
	@if command -v uv >/dev/null 2>&1; then \
		PYTHONPATH=$(SRC_DIR) uv run pytest $(TEST_DIR) --cov=$(SRC_DIR)/chuk_puzzles_gym --cov-report=term-missing --cov-report=html; \
	else \
		PYTHONPATH=$(SRC_DIR) $(PYTEST) $(TEST_DIR) --cov=$(SRC_DIR)/chuk_puzzles_gym --cov-report=term-missing --cov-report=html; \
	fi
	@echo ""
	@echo "Coverage report generated in htmlcov/index.html"

test-watch:
	@echo "Running tests in watch mode..."
	@if command -v uv >/dev/null 2>&1; then \
		PYTHONPATH=$(SRC_DIR) uv run pytest-watch $(TEST_DIR); \
	else \
		PYTHONPATH=$(SRC_DIR) $(PYTHON) -m pytest_watch $(TEST_DIR); \
	fi

# Code Quality
check: lint typecheck test
	@echo ""
	@echo "✓ All checks passed!"

lint:
	@echo "Running linter..."
	@if command -v uv >/dev/null 2>&1; then \
		uv run ruff check $(SRC_DIR) $(TEST_DIR); \
		uv run ruff format --check $(SRC_DIR) $(TEST_DIR); \
	elif command -v $(RUFF) >/dev/null 2>&1; then \
		$(RUFF) check $(SRC_DIR) $(TEST_DIR); \
		$(RUFF) format --check $(SRC_DIR) $(TEST_DIR); \
	else \
		echo "Ruff not found. Install with: pip install ruff"; \
		exit 1; \
	fi

format:
	@echo "Formatting code..."
	@if command -v uv >/dev/null 2>&1; then \
		uv run ruff format $(SRC_DIR) $(TEST_DIR); \
		uv run ruff check --fix $(SRC_DIR) $(TEST_DIR); \
	elif command -v $(RUFF) >/dev/null 2>&1; then \
		$(RUFF) format $(SRC_DIR) $(TEST_DIR); \
		$(RUFF) check --fix $(SRC_DIR) $(TEST_DIR); \
	else \
		echo "Ruff not found. Install with: pip install ruff"; \
		exit 1; \
	fi

format-check:
	@echo "Checking code formatting..."
	@if command -v uv >/dev/null 2>&1; then \
		uv run ruff format --check $(SRC_DIR) $(TEST_DIR); \
	elif command -v $(RUFF) >/dev/null 2>&1; then \
		$(RUFF) format --check $(SRC_DIR) $(TEST_DIR); \
	else \
		echo "Ruff not found. Install with: pip install ruff"; \
		exit 1; \
	fi

typecheck:
	@echo "Running type checker..."
	@if command -v uv >/dev/null 2>&1; then \
		uv run mypy $(SRC_DIR) || echo "Type check found issues (non-blocking)"; \
	elif command -v $(MYPY) >/dev/null 2>&1; then \
		$(MYPY) $(SRC_DIR) || echo "Type check found issues (non-blocking)"; \
	else \
		echo "MyPy not found. Install with: pip install mypy"; \
		exit 1; \
	fi

# Alias for typecheck
type-check: typecheck

# Security
security:
	@echo "Running security checks..."
	@if command -v uv >/dev/null 2>&1; then \
		uv run bandit -r $(SRC_DIR) -f txt || echo "Security issues found (non-blocking)"; \
	elif command -v bandit >/dev/null 2>&1; then \
		bandit -r $(SRC_DIR) -f txt || echo "Security issues found (non-blocking)"; \
	else \
		echo "Bandit not found. Install with: pip install bandit"; \
		exit 1; \
	fi

# Docker
docker-build:
	@echo "Building Docker image..."
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .

docker-run: docker-build
	@echo "Running Docker container..."
	@echo "Telnet:    telnet localhost 8023"
	@echo "TCP:       nc localhost 8024"
	@echo "WebSocket: ws://localhost:8025/ws"
	@echo "WS-Telnet: ws://localhost:8026/ws"
	@echo ""
	docker run -d --name $(DOCKER_IMAGE) \
		-p 8023:8023 \
		-p 8024:8024 \
		-p 8025:8025 \
		-p 8026:8026 \
		$(DOCKER_IMAGE):$(DOCKER_TAG)
	@echo "Container started. Use 'make docker-logs' to view logs."

docker-stop:
	@echo "Stopping Docker container..."
	docker stop $(DOCKER_IMAGE) || true
	docker rm $(DOCKER_IMAGE) || true

docker-logs:
	@echo "Showing Docker container logs..."
	docker logs -f $(DOCKER_IMAGE)

docker-shell:
	@echo "Opening shell in Docker container..."
	docker exec -it $(DOCKER_IMAGE) /bin/bash

docker-clean: docker-stop
	@echo "Removing Docker image..."
	docker rmi $(DOCKER_IMAGE):$(DOCKER_TAG) || true

# Build & Publishing
build: clean-build
	@echo "Building distribution packages..."
	@if command -v uv >/dev/null 2>&1; then \
		uv build; \
	else \
		python3 -m build; \
	fi
	@echo ""
	@echo "Build complete. Distributions are in the 'dist' folder."
	@ls -lh dist/

publish:
	@echo "Starting automated release process..."
	@echo ""
	@# Get current version
	@version=$$(grep '^version = ' pyproject.toml | cut -d'"' -f2); \
	tag="v$$version"; \
	echo "Version: $$version"; \
	echo "Tag: $$tag"; \
	echo ""; \
	\
	echo "Pre-flight checks:"; \
	echo "=================="; \
	\
	if git diff --quiet && git diff --cached --quiet; then \
		echo "✓ Working directory is clean"; \
	else \
		echo "✗ Working directory has uncommitted changes"; \
		echo ""; \
		git status --short; \
		echo ""; \
		echo "Please commit or stash your changes before releasing."; \
		exit 1; \
	fi; \
	\
	if git tag -l | grep -q "^$$tag$$"; then \
		echo "✗ Tag $$tag already exists"; \
		echo ""; \
		echo "To delete and recreate:"; \
		echo "  git tag -d $$tag"; \
		echo "  git push origin :refs/tags/$$tag"; \
		exit 1; \
	else \
		echo "✓ Tag $$tag does not exist yet"; \
	fi; \
	\
	current_branch=$$(git rev-parse --abbrev-ref HEAD); \
	echo "✓ Current branch: $$current_branch"; \
	echo ""; \
	\
	echo "This will:"; \
	echo "  1. Create and push tag $$tag"; \
	echo "  2. Trigger GitHub Actions to:"; \
	echo "     - Create a GitHub release with changelog"; \
	echo "     - Run tests on all platforms"; \
	echo "     - Build and publish to PyPI"; \
	echo ""; \
	read -p "Continue? (y/N) " -n 1 -r; \
	echo ""; \
	if [[ ! $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "Aborted."; \
		exit 1; \
	fi; \
	\
	echo ""; \
	echo "Creating and pushing tag..."; \
	git tag -a "$$tag" -m "Release $$tag"; \
	git push origin "$$tag"; \
	echo ""; \
	echo "✓ Tag $$tag created and pushed"; \
	echo ""; \
	echo "GitHub Actions will now:"; \
	echo "  - Run tests"; \
	echo "  - Create GitHub release"; \
	echo "  - Publish to PyPI"; \
	echo ""; \
	echo "Monitor progress at:"; \
	echo "  https://github.com/chrishayuk/puzzle-arcade-server/actions"

publish-manual: build
	@echo "Manual PyPI Publishing"
	@echo "======================"
	@echo ""
	@version=$$(grep '^version = ' pyproject.toml | cut -d'"' -f2); \
	tag="v$$version"; \
	echo "Version: $$version"; \
	echo "Tag: $$tag"; \
	echo ""; \
	\
	echo "Pre-flight checks:"; \
	echo "=================="; \
	\
	if git diff --quiet && git diff --cached --quiet; then \
		echo "✓ Working directory is clean"; \
	else \
		echo "✗ Working directory has uncommitted changes"; \
		echo ""; \
		git status --short; \
		echo ""; \
		echo "Please commit or stash your changes before publishing."; \
		exit 1; \
	fi; \
	\
	if git tag -l | grep -q "^$$tag$$"; then \
		echo "✓ Tag $$tag exists"; \
	else \
		echo "⚠ Tag $$tag does not exist yet"; \
		echo ""; \
		read -p "Create tag now? (y/N) " -n 1 -r; \
		echo ""; \
		if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
			git tag -a "$$tag" -m "Release $$tag"; \
			echo "✓ Tag created locally"; \
		else \
			echo "Continuing without creating tag..."; \
		fi; \
	fi; \
	\
	echo ""; \
	echo "This will upload version $$version to PyPI"; \
	echo ""; \
	read -p "Continue? (y/N) " -n 1 -r; \
	echo ""; \
	if [[ ! $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "Aborted."; \
		exit 1; \
	fi; \
	\
	echo ""; \
	echo "Uploading to PyPI..."; \
	if [ -n "$$PYPI_TOKEN" ]; then \
		if command -v uv >/dev/null 2>&1; then \
			uv run twine upload --username __token__ --password "$$PYPI_TOKEN" dist/*; \
		else \
			python3 -m twine upload --username __token__ --password "$$PYPI_TOKEN" dist/*; \
		fi; \
	else \
		if command -v uv >/dev/null 2>&1; then \
			uv run twine upload dist/*; \
		else \
			python3 -m twine upload dist/*; \
		fi; \
	fi

publish-test: build
	@echo "Publishing to TestPyPI..."
	@echo ""
	@if [ -n "$$PYPI_TOKEN" ]; then \
		if command -v uv >/dev/null 2>&1; then \
			uv run twine upload --repository testpypi --username __token__ --password "$$PYPI_TOKEN" dist/*; \
		else \
			python3 -m twine upload --repository testpypi --username __token__ --password "$$PYPI_TOKEN" dist/*; \
		fi; \
	else \
		if command -v uv >/dev/null 2>&1; then \
			uv run twine upload --repository testpypi dist/*; \
		else \
			python3 -m twine upload --repository testpypi dist/*; \
		fi; \
	fi

# Deployment
fly-deploy:
	@echo "Deploying to Fly.io..."
	fly deploy

fly-logs:
	@echo "Showing Fly.io logs..."
	fly logs

fly-status:
	@echo "Checking Fly.io status..."
	fly status

fly-open:
	@echo "Opening Fly.io dashboard..."
	fly open

fly-ssh:
	@echo "Opening SSH session on Fly.io..."
	fly ssh console

# Cleanup
clean:
	@echo "Cleaning generated files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov 2>/dev/null || true

clean-build:
	@echo "Cleaning build artifacts..."
	@rm -rf build/ dist/ *.egg-info $(SRC_DIR)/*.egg-info 2>/dev/null || true
	@rm -rf .eggs/ 2>/dev/null || true
	@find . -name '*.egg' -exec rm -f {} + 2>/dev/null || true

clean-all: clean clean-build docker-clean
	@echo "Cleaning all files including Docker..."
	rm -rf venv env .eggs 2>/dev/null || true
	find . -name '.DS_Store' -delete 2>/dev/null || true
	find . -name '*.log' -delete 2>/dev/null || true

# Examples
example-telnet:
	@echo "Running telnet example client (browse mode)..."
	$(PYTHON) $(EXAMPLES_DIR)/simple_client.py browse

example-telnet-interactive:
	@echo "Running telnet example client (interactive mode)..."
	$(PYTHON) $(EXAMPLES_DIR)/simple_client.py interactive

example-telnet-sudoku:
	@echo "Running telnet example client (Sudoku demo)..."
	$(PYTHON) $(EXAMPLES_DIR)/simple_client.py sudoku

example-telnet-kenken:
	@echo "Running telnet example client (KenKen demo)..."
	$(PYTHON) $(EXAMPLES_DIR)/simple_client.py kenken

example-ws:
	@echo "Running WebSocket example client (tour mode)..."
	$(PYTHON) $(EXAMPLES_DIR)/websocket_client.py tour

example-ws-interactive:
	@echo "Running WebSocket example client (interactive mode)..."
	$(PYTHON) $(EXAMPLES_DIR)/websocket_client.py interactive

example-ws-sudoku:
	@echo "Running WebSocket example client (Sudoku demo)..."
	$(PYTHON) $(EXAMPLES_DIR)/websocket_client.py sudoku

example-ws-binary:
	@echo "Running WebSocket example client (Binary demo)..."
	$(PYTHON) $(EXAMPLES_DIR)/websocket_client.py binary

example-ws-tour:
	@echo "Running WebSocket example client (game tour)..."
	$(PYTHON) $(EXAMPLES_DIR)/websocket_client.py tour

example-ws-solve:
	@echo "Running WebSocket example client (solve mode)..."
	$(PYTHON) $(EXAMPLES_DIR)/websocket_client.py solve

# Evaluation
eval:
	@echo "Running evaluation harness (quick check)..."
	@if command -v uv >/dev/null 2>&1; then \
		PYTHONPATH=$(SRC_DIR) uv run python -m chuk_puzzles_gym.eval --all -d easy -n 3 -v; \
	else \
		PYTHONPATH=$(SRC_DIR) $(PYTHON) -m chuk_puzzles_gym.eval --all -d easy -n 3 -v; \
	fi

eval-sudoku:
	@echo "Evaluating Sudoku (10 episodes)..."
	@if command -v uv >/dev/null 2>&1; then \
		PYTHONPATH=$(SRC_DIR) uv run python -m chuk_puzzles_gym.eval sudoku -d medium -n 10 -v; \
	else \
		PYTHONPATH=$(SRC_DIR) $(PYTHON) -m chuk_puzzles_gym.eval sudoku -d medium -n 10 -v; \
	fi

eval-all:
	@echo "Evaluating all games (10 episodes each)..."
	@if command -v uv >/dev/null 2>&1; then \
		PYTHONPATH=$(SRC_DIR) uv run python -m chuk_puzzles_gym.eval --all -d easy -n 10 -v; \
	else \
		PYTHONPATH=$(SRC_DIR) $(PYTHON) -m chuk_puzzles_gym.eval --all -d easy -n 10 -v; \
	fi

eval-json:
	@echo "Evaluating all games (JSON output)..."
	@if command -v uv >/dev/null 2>&1; then \
		PYTHONPATH=$(SRC_DIR) uv run python -m chuk_puzzles_gym.eval --all -d easy -n 5 -o json; \
	else \
		PYTHONPATH=$(SRC_DIR) $(PYTHON) -m chuk_puzzles_gym.eval --all -d easy -n 5 -o json; \
	fi

# CHUK-R Benchmark
benchmark:
	@echo "Running CHUK-R benchmark (easy, 5 episodes/game)..."
	@if command -v uv >/dev/null 2>&1; then \
		PYTHONPATH=$(SRC_DIR) uv run chuk-puzzles-benchmark -d easy -n 5 -v; \
	else \
		PYTHONPATH=$(SRC_DIR) $(PYTHON) -m chuk_puzzles_gym.benchmark.cli -d easy -n 5 -v; \
	fi

benchmark-full:
	@echo "Running full CHUK-R benchmark (medium, 10 episodes/game)..."
	@if command -v uv >/dev/null 2>&1; then \
		PYTHONPATH=$(SRC_DIR) uv run chuk-puzzles-benchmark -d medium -n 10 -v; \
	else \
		PYTHONPATH=$(SRC_DIR) $(PYTHON) -m chuk_puzzles_gym.benchmark.cli -d medium -n 10 -v; \
	fi

benchmark-json:
	@echo "Running CHUK-R benchmark (JSON output)..."
	@if command -v uv >/dev/null 2>&1; then \
		PYTHONPATH=$(SRC_DIR) uv run chuk-puzzles-benchmark -d easy -n 5 -o json; \
	else \
		PYTHONPATH=$(SRC_DIR) $(PYTHON) -m chuk_puzzles_gym.benchmark.cli -d easy -n 5 -o json; \
	fi

list-games:
	@echo "Available games:"
	@if command -v uv >/dev/null 2>&1; then \
		PYTHONPATH=$(SRC_DIR) uv run python -m chuk_puzzles_gym.eval --list-games; \
	else \
		PYTHONPATH=$(SRC_DIR) $(PYTHON) -m chuk_puzzles_gym.eval --list-games; \
	fi

# Development helpers
serve-coverage:
	@echo "Serving coverage report on http://localhost:8000..."
	cd htmlcov && $(PYTHON) -m http.server 8000

# Quick development workflow
dev: dev-install
	@echo "Development environment ready!"
	@echo "Run 'make run' to start the server"

quick-check: format lint
	@echo "Quick check complete!"

# CI/CD helpers
ci: dev-install check test
	@echo "CI pipeline complete!"

# Version info
version:
	@echo "Python version:"
	@$(PYTHON) --version
	@echo ""
	@echo "Pip version:"
	@$(PIP) --version
	@echo ""
	@echo "Installed packages:"
	@$(PIP) list | grep -E "(chuk-protocol-server|pytest|ruff|mypy|websockets)" || echo "  (none found)"
