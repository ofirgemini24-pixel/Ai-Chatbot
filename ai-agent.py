import os
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from google import genai
import error_handler as eh

# אתחול שרת ה-Flask עם תמיכה בתיקיית ה-templates
app = Flask(__name__)
CORS(app)

# אתחול הלקוח של גוגל - מושך את ה-GEMINI_API_KEY באופן מאובטח מהגדרות הסביבה ב-Render
try:
    client = genai.Client()
except Exception as e:
    print("Warning: Could not initialize Gemini Client. Check Render Environment Variables.")
    client = None

# זיכרון השיחות של המשתמשים
users_db = {}

# --- נתיב הבית: מציג את ממשק הצ'אטבוט (interface.html) ישירות בקישור של Render ---
@app.route('/', methods=['GET'])
def home():
    return render_template('interface.html')

# --- נתיב הצ'אט: מקבל הודעות מהממשק ושולח אותן ל-Gemini ---
@app.route('/chat', methods=['POST'])
def chat():
    if not client:
        return jsonify({"reply": "שגיאת מערכת: מפתח ה-API של Gemini לא מוגדר בשרת הרחוק."})

    data = request.json or {}
    user_id = data.get("user_id", "default_user")
    user_input = data.get("message", "")

    # 1. חסימת תוכן בוטה או מילים אסורות
    if not eh.is_safe(user_input):
        return jsonify({"reply": "אני לא יכול לענות על זה, בוא נשמור על שיחה מכבדת."})

    # 2. ניהול זיכרון והיסטוריית שיחה
    if user_id not in users_db:
        users_db[user_id] = {
            "history": [],
            "first_time": True,
            "images": 0
        }

    user_session = users_db[user_id]
    
    # 3. הודעת היכרות מותאמת אישית בשיחה הראשונה
    prefix = ""
    if user_session["first_time"]:
        prefix = "שלום! אני העוזר האישי שלך. נעים להכיר! אני מחובר ליומן ולמערכת הלימודים שלך. "
        user_session["first_time"] = False

    # 4. שליחת ההודעה ל-Gemini 2.5 Flash (הדגם המעודכן והמהיר)
    try:
        # בניית מבנה הודעות עם ההיסטוריה הקודמת
        messages = user_session["history"] + [{"role": "user", "parts": [user_input]}]
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=messages
        )
        
        reply_text = prefix + response.text
        
        # שמירת ההודעות הנוכחיות בזיכרון השיחה
        user_session["history"].append({"role": "user", "parts": [user_input]})
        user_session["history"].append({"role": "model", "parts": [response.text]})

        # לוגיקת זיהוי פקודות בסיסית
        if "תזכורת" in user_input:
            reply_text += "\n\n(רשמתי לעצמי ליצור תזכורת ביומן ובואטסאפ)"
        if "בוחן" in user_input:
            reply_text += "\n\n(מכין לך בוחן חזרה על החומר...)"

        return jsonify({"reply": reply_text})
    except Exception as e:
        return jsonify({"reply": eh.log_error(e)})

# --- נתיב העלאת תמונות: בדיקת מגבלת כמות ---
@app.route('/upload', methods=['POST'])
def upload():
    user_id = "default_user"
    if user_id not in users_db:
        users_db[user_id] = {"images": 0}
        
    if users_db.get(user_id, {}).get("images", 0) >= 5:
        return jsonify({"reply": "מצטער, הגעת למגבלה של 5 תמונות."})
    
    users_db[user_id]["images"] = users_db.get(user_id, {}).get("images", 0) + 1
    return jsonify({"reply": f"התמונה התקבלה! זו תמונה מספר {users_db[user_id]['images']} מתוך 5."})

if __name__ == '__main__':
    app.run(port=5000, debug=True)
