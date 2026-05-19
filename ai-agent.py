import os
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from google import genai
import error_handler as eh

# אתחול השרת עם הגדרה תקינה
app = Flask(__name__)
CORS(app)

# אתחול הלקוח של גוגל - קורא אוטומטית את GEMINI_API_KEY מתוך Render
try:
    client = genai.Client()
except Exception as e:
    print("Warning: Could not initialize Gemini Client. Check Render Environment Variables.")
    client = None

# זיכרון המערכת
users_db = {}

# --- התיקון המרכזי: נתיב הבית שיציג את ממשק הצ'אטבוט ב-Render ---
@app.route('/', methods=['GET'])
def home():
    return render_template('interface.html')

@app.route('/chat', methods=['POST'])
def chat():
    if not client:
        return jsonify({"reply": "שגיאת מערכת: מפתח ה-API של Gemini לא מוגדר בשרת הרחוק."})

    data = request.json or {}
    user_id = data.get("user_id", "default_user")
    user_input = data.get("message", "")

    # 1. חסימת תוכן בוטה
    if not eh.is_safe(user_input):
        return jsonify({"reply": "אני לא יכול לענות על זה, בוא נשמור על שיחה מכבדת."})

    # 2. ניהול זיכרון והיכרות
    if user_id not in users_db:
        users_db[user_id] = {
            "history": [],
            "first_time": True,
            "images": 0
        }

    user_session = users_db[user_id]
    
    # 3. הודעת היכרות בשיחה הראשונה
    prefix = ""
    if user_session["first_time"]:
        prefix = "שלום! אני העוזר האישי שלך. נעים להכיר! אני מחובר ליומן ולמערכת הלימודים שלך. "
        user_session["first_time"] = False

    # 4. שליחה ל-Gemini 2.5 Flash החדש
    try:
        messages = user_session["history"] + [{"role": "user", "parts": [user_input]}]
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=messages
        )
        
        reply_text = prefix + response.text
        
        # שמירת ההיסטוריה לטובת זיכרון מתמשך
        user_session["history"].append({"role": "user", "parts": [user_input]})
        user_session["history"].append({"role": "model", "parts": [response.text]})

        # זיהוי פקודות פשוטות
        if "תזכורת" in user_input:
            reply_text += "\n\n(רשמתי לעצמי ליצור תזכורת ביומן ובואטסאפ)"
        if "בוחן" in user_input:
            reply_text += "\n\n(מכין לך בוחן חזרה על החומר...)"

        return jsonify({"reply": reply_text})
    except Exception as e:
        return jsonify({"reply": eh.log_error(e)})

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
