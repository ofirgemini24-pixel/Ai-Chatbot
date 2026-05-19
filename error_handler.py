import logging

# הגדרת רישום שגיאות לקובץ לוג פנימי בשרת
logging.basicConfig(level=logging.INFO, filename='bot_errors.log')

# רשימת המילים החסומות בצ'אט
BANNED_WORDS = ["קללה1", "מילה_בוטה", "זבל"] 

def is_safe(text):
    """בודק אם הטקסט שנשלח על ידי המשתמש נקי מקללות או תוכן בוטה"""
    for word in BANNED_WORDS:
        if word in text:
            return False
    return True

def log_error(e):
    """רושם את השגיאה האמיתית בשרת ומחזיר הודעה ידידותית למשתמש"""
    logging.error(f"Error occurred: {e}")
    return "אופס! קרתה שגיאה קטנה במערכת שלי."
