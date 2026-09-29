import os


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-only-change-me')
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'instance/wheel_deal.sqlite3')