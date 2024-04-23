install:
	pip install discord
	pip install spotipy
	pip install datetime

run:
	python3 bot.py

clean:
	rm -rf __pycache__

.PHONY:
