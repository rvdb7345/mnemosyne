.EXPORT_ALL_VARIABLES:

.DEFAULT_GOAL := help
PYTHON_VERSION := 3.10
POETRY := poetry
VENV_PATH = .venv
LOCAL_PRE_COMMIT = $(VENV_PATH)/bin/pre-commit

# Check if 'python3.8' is installed
ifeq (, $(shell which python$(PYTHON_VERSION)))
  $(error 'python$(PYTHON_VERSION)' not found in PATH, please install it first)
endif

# Check if 'poetry' is installed
ifeq (, $(shell which $(POETRY)))
  $(error '$(POETRY)' not found in PATH, please install it first)
endif

.PHONY: help
help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  setup      Set up the virtual environment and install dependencies"
	@echo "  venv       Create the virtual environment"
	@echo "  pre-commit       Set up pre-commit"
	@echo "  install    Install project dependencies"
	@echo "  clean      Clean up the virtual environment and generated files"
	@echo "  uninstall  Uninstall the virtual environment and dependencies"
	@echo "  help       Show this help message"

.PHONY: setup
setup: venv install pre-commit

.PHONY: setup
venv:
	@echo "Current directory: $(PWD)"
	@echo "Creating virtual environment..."
	@python$(PYTHON_VERSION) -m venv $(VENV_PATH) || (echo "Failed to create virtual environment"; exit 1)
	@echo "Virtual environment created."

.PHONY: install
install:
	@echo "PIP3 installing Poetry..."
	# @pip3 install $(POETRY)
	@echo "Using the virtual environment..."
	@$(POETRY) env use $(VENV_PATH)/bin/python$(PYTHON_VERSION)
	@echo "Installing dependencies..."
	@$(POETRY) install --no-root
	@echo "Dependencies installed."


# prompt_example> make test PY=py36 OPTIONS="-- -s"
.PHONY: test
test:
	@echo "Running Tests using Tox..."
	@tox -e py310

.PHONY: clean
clean:
	@rm -rf $(VENV_PATH)
	@rm -f poetry.lock

# .PHONY: uninstall
# uninstall:
# 	@echo "Uninstalling the virtual environment and dependencies..."
# 	@$(POETRY) env remove $(VENV_PATH)
# 	@echo "Uninstallation complete."
