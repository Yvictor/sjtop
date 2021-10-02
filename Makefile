test:
	pytest --cov-report term-missing --cov=sjtop tests/ -vv

build:
	poetry build

publish:
	poetry publish