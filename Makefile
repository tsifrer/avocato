test:
	py.test -v -s -x $(ARGS)

cov:
	py.test --cov=./

cov-html:
	py.test --cov=./ --cov-report html

remove-pyc:
	find . -name "*.pyc" -delete

bm-simple:
	python -m benchmark.bm_simple