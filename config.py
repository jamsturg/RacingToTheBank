import os

class Config:
    PUNTING_FORM_API_KEY = '7552b21e-851b-4803-b230-d1637a74f05c'
    DB_CONFIG = {
        'host': os.environ.get('PGHOST'),
        'database': os.environ.get('PGDATABASE'),
        'user': os.environ.get('PGUSER'),
        'password': os.environ.get('PGPASSWORD'),
        'port': os.environ.get('PGPORT')
    }
