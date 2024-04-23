install:
	sudo apt install python3
	pip install discord
	pip install spotipy
	pip install datetime
	pip install sqlite3

run:
	python3 bot.py

clean:
	rm -rf __pycache__

.PHONY:
