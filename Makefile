install:
	pip install -r requirements.txt

clear-deps:
	pip freeze > to-uninstall.txt
	pip uninstall -y -r to-uninstall.txt
	rm to-uninstall.txt

freeze:
	pip freeze > requirements.txt

start:
	python src/app.py

lint:
	python -m pylint src
	python -m pylint tests

lint-fix:
	autopep8 --in-place --aggressive --aggressive */**/*.pypytho