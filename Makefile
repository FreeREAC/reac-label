test:
	python3 -m unittest discover tests -v
demo:
	python3 -m reaclabel --sim
.PHONY: test demo
