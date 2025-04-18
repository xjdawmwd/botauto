import sqlite3
from cryptography.fernet import Fernet
import datetime
import os

def backup_database():
    conn = sqlite3.connect('accounts.db')
    with open('backup.sql', 'w') as f:
        for line in conn.iterdump():
            f.write(f'{line}\n')
    
    cipher = Fernet(FERNET_KEY)
    with open('backup.sql', 'rb') as f:
        encrypted = cipher.encrypt(f.read())
    
    backup_name = f"backup_{datetime.datetime.now().strftime('%Y%m%d')}.enc"
    with open(backup_name, 'wb') as f:
        f.write(encrypted)
    
    os.remove('backup.sql')
    print(f"Backup {backup_name} created!")

if __name__ == '__main__':
    backup_database()