build:
	python3 setup.py sdist bdist_wheel

clean:
	rm -rf build dist remarkable_cli.egg-info

upload:
	twine upload dist/*

test:
	python3 -m unittest discover
