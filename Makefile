.PHONY: test

test:
	uv run --with pytest python -m pytest
