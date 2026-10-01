.PHONY: lint test check

lint:
	python -m yamllint k8s

test:
	pytest -q

check: lint test
