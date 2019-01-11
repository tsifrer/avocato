.PHONY: docs
test:
	py.test -v -s -x $(ARGS)

cov:
	py.test --cov=./

cov-html:
	py.test --cov=./ --cov-report html

remove-pyc:
	find . -name "*.pyc" -delete

publish:
	pip install 'twine>=1.12.1'
	python setup.py sdist bdist_wheel
	twine upload dist/*
	rm -rf build dist .egg avocato.egg-info

docs:
	cd docs && make html
	@echo "\033[95m\n\nBuild successful! View the docs homepage at docs/_build/html/index.html.\n\033[0m"