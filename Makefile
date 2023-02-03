run:
	@DEVMODE=false python3 src/main.py

dev:
	@DEVMODE=true python3 src/main.py

clean:
	@find . | grep -E '(__pycache__|\.pyc|\.pyo$|\.DS_Store)' | xargs rm -rf

format:
	@black src/

lint:
	@flake8 src/