import sqlite3
import os

def initialTable():
    database_name = "data/SessionDb.db"
    conn = sqlite3.connect(database_name)
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS SessionTrack1")
    cur.execute("DROP TABLE IF EXISTS SessionTrack2")
    cur.execute("DROP TABLE IF EXISTS SessionTrack3")
    cur.execute("DROP TABLE IF EXISTS SessionTrack4")
    cur.execute("DROP TABLE IF EXISTS SessionNum")
    cur.execute("CREATE TABLE SessionTrack1(Id INTEGER PRIMARY KEY AUTOINCREMENT, Time TEXT, VideoPath TEXT)")
    cur.execute("CREATE TABLE SessionTrack2(Id INTEGER PRIMARY KEY AUTOINCREMENT, Time TEXT, VideoPath TEXT)")
    cur.execute("CREATE TABLE SessionTrack3(Id INTEGER PRIMARY KEY AUTOINCREMENT, Time TEXT, VideoPath TEXT)")
    cur.execute("CREATE TABLE SessionTrack4(Id INTEGER PRIMARY KEY AUTOINCREMENT, Time TEXT, VideoPath TEXT)")
    cur.execute("CREATE TABLE SessionNum(Id INTEGER PRIMARY KEY AUTOINCREMENT, TableName TEXT, SessionDate TEXT)")
initialTable()