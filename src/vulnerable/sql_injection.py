import sqlite3

# EXAMPLE ONLY - intentionally vulnerable for Black Duck Code Sight SAST testing
# Vulnerability: SQL Injection (CWE-89) via string concatenation


def get_rover_photo(db_path, sol):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = "SELECT * FROM photos WHERE sol = '" + sol + "'"  # user input concatenated directly
    cursor.execute(query)
    return cursor.fetchall()
