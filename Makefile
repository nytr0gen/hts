all: help

deps: .deps
.deps: requirements.txt
	pip install -r $<
	touch $@

run: deps
	python app/app.py

updatedb: deps
	python app/updatedb.py

test: deps
	python -m unittest discover app '*_test.py'

help:
	cat README.md
