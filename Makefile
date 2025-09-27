# Supply Chain Risk Analysis Makefile

.PHONY: setup run export test clean help

# Default target
help:
	@echo "Supply Chain Risk Analysis - Available commands:"
	@echo ""
	@echo "  setup     - Install dependencies and create directories"
	@echo "  run       - Run complete pipeline"
	@echo "  export    - Export features CSV only"
	@echo "  test      - Run tests"
	@echo "  clean     - Clean output files"
	@echo "  help      - Show this help message"
	@echo ""

# Setup environment
setup:
	@echo "Setting up supply chain risk analysis environment..."
	pip install -r requirements.txt
	@echo "Creating directories..."
	mkdir -p data/inputs data/outputs cache logs
	@echo "Copying environment file..."
	@if [ ! -f .env ]; then cp env.example .env; echo "Created .env file from template"; fi
	@echo "Setup completed!"

# Run complete pipeline
run:
	@echo "Running complete supply chain risk analysis pipeline..."
	python -m orchestrator.cli run-all

# Export CSV only
export:
	@echo "Exporting features CSV..."
	python -m orchestrator.cli export-csv

# Regenerate registry
regen-registry:
	@echo "Regenerating supplier registry..."
	python -m orchestrator.cli regen-registry

# Run tests
test:
	@echo "Running tests..."
	pytest tests/ -v

# Check setup
check:
	@echo "Checking system setup..."
	python -m orchestrator.cli check-setup

# Test individual agents
test-agents:
	@echo "Testing individual agents..."
	python -m orchestrator.cli test-agents

# Clean output files
clean:
	@echo "Cleaning output files..."
	rm -f data/outputs/*.parquet data/outputs/*.csv data/outputs/*.json
	rm -f cache/*.json cache/*.db
	rm -f logs/*.log
	@echo "Clean completed!"

# Serve flows with Prefect
serve:
	@echo "Starting Prefect server..."
	python -m orchestrator.cli serve-flows

# Development setup
dev-setup: setup
	@echo "Setting up development environment..."
	pip install black flake8 mypy pytest
	@echo "Development setup completed!"

# Format code
format:
	@echo "Formatting code..."
	black agents/ core/ orchestrator/ tests/
	@echo "Code formatting completed!"

# Lint code
lint:
	@echo "Linting code..."
	flake8 agents/ core/ orchestrator/ tests/
	mypy agents/ core/ orchestrator/
	@echo "Linting completed!"

# Full development workflow
dev: format lint test
	@echo "Development workflow completed!"

# Docker commands
docker-build:
	@echo "Building Docker image..."
	docker build -t supply-chain-risk-analysis .

docker-run:
	@echo "Running Docker container..."
	docker run -it --rm -v $(PWD)/data:/app/data supply-chain-risk-analysis

# Production deployment
deploy:
	@echo "Deploying to production..."
	@echo "This would typically involve:"
	@echo "1. Building Docker image"
	@echo "2. Pushing to registry"
	@echo "3. Deploying to cloud platform"
	@echo "4. Setting up monitoring and alerts"
