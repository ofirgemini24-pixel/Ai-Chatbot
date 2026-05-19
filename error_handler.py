import logging

# רישום שגיאות לקובץ
logging.basicConfig(level=logging.INFO, filename='bot_errors.log')

BANNED_WORDS = ["קללה1", "מילה_בוטה", "זבל"] # תוסיף כאן מילים נוספות

def is_safe(text):
    """בודק אם הטקסט נקי מתכנים בוטים"""
    for word in BANNED_WORDS:
        if word in text:
            return False
    return True

def log_error(e):
    logging.error(f"Error occurred: {e}")
    return "אופס! קרתה שגיאה קטנה במערכת שלי."
