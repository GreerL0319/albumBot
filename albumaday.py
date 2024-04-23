import sqlite3 
conn=sqlite3.connect("albums.db")
cursor=conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS albums (
                    id INTEGER PRIMARY KEY,
                    title TEXT,
                    artist TEXT,
                    genre TEXT,
                    year INTEGER,
                    recommended TEXT
                )''')
    
conn.commit()
conn.close()

def addAlbum(title,artist,genre,year,recommendation):
    conn=sqlite3.connect('albums.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM albums WHERE title = ? AND artist = ?', (title, artist))
    existing_album = cursor.fetchone()
    if existing_album:
        conn.close()
        return
    cursor.execute('''INSERT INTO albums (title, artist, genre, year, recommended)
                      VALUES (?, ?, ?, ?, ?)''', (title, artist, genre, year, recommendation))
    conn.commit()
    conn.close()

def removeRecommendation(search):
    conn = sqlite3.connect('albums.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM albums WHERE title LIKE ?', (search,))
    conn.commit()
    conn.close()
    if cursor.rowcount > 0:
        return "Successfuly removed item."
    else:
        return"Item does not exist."
        

def listDatabase():
    conn = sqlite3.connect('albums.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM albums')
    albums = cursor.fetchall()
    conn.close()
    print("---- All Albums ----")
    for album in albums:
        print(album)
    print("--------------------")
    
def emptyDatabase():
    conn = sqlite3.connect('albums.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM albums')
    conn.commit()
    conn.close()
    print("Database emptied successfully.")

def format_albums(albums):
    formatted_albums = []
    for album in albums:
        formatted_album = f"{album[1]} -{album[2]} {album[3]} {album[4]} Recommended by: {album[5]}\n"
        formatted_albums.append(formatted_album)
    return formatted_albums

def getDB():
    conn = sqlite3.connect('albums.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM albums')
    all_albums = cursor.fetchall()
    conn.close()
    all_albums=format_albums(all_albums)
    return all_albums

def getRecommendation():
    conn = sqlite3.connect('albums.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM albums')
    count = cursor.fetchone()[0]
    if count > 0: #prevents code from breaking when table is empty
        cursor.execute('SELECT * FROM albums ORDER BY RANDOM() LIMIT 1')
        recommendation = cursor.fetchone()
        cursor.execute('DELETE FROM albums WHERE id LIKE ?', (recommendation[0],))
        conn.commit()
        conn.close()
        return recommendation
    else:
        conn.close()
        return None

def main():
    while True:
        print("")
        print("1. Get Recommendation")
        print("2. Insert Album")
        print("3. Remove album")
        print("4. Clear Table")
        print("5. Print Database")
        print("6. Quit")
        print("")
        opt = int(input())

        if opt == 1:
            recc=getRecommendation()
            print(recc)
        elif opt == 2:
            title = str(input("TITLE: "))
            artist = str(input("ARTIST: "))
            genre = str(input("GENRE: "))
            year = int(input("YEAR: ")) 
            recommended = str(input("WHO RECOMMENDED? "))
            addAlbum(title, artist, genre, year, recommended)
        elif opt == 3:
            search = str(input("Title to remove: "))
            removeRecommendation(search) 
        elif opt == 4:
            confirm = str(input("ARE YOU SURE? This will delete all data. (y/n): "))
            if confirm.lower() in ['y', 'yes']:
                emptyDatabase()
        elif opt == 5:
            listDatabase()
        elif opt == 6:
            break
        else:
            print("INVALID INPUT")

if __name__ == "__main__":
    main()
