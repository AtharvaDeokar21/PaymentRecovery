import os


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/recoverai')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

    RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID', '')
    RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET', '')
    RAZORPAY_MODE = os.getenv('RAZORPAY_MODE', 'simulation')

    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')

    MAX_RETRY_ATTEMPTS = int(os.getenv('MAX_RETRY_ATTEMPTS', '2'))
    MAX_AUTO_RETRY_AMOUNT = int(os.getenv('MAX_AUTO_RETRY_AMOUNT', '10000'))
    MIN_RECOVERY_PROBABILITY = float(os.getenv('MIN_RECOVERY_PROBABILITY', '0.65'))
    APPROVAL_THRESHOLD = int(os.getenv('APPROVAL_THRESHOLD', '10000'))
    COOLDOWN_MINUTES = int(os.getenv('COOLDOWN_MINUTES', '15'))
