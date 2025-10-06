# db_init.py - initialize DB (optional)
from db import DBSessionManager
import config

if __name__ == '__main__':
    DBSessionManager(config.DB_PATH)
    print('DB initialized at', config.DB_PATH)
