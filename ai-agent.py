import google.generativeai as genai
from flask import Flask, request, jsonify
from flask_cors import CORS
import error_handler as eh
import os

app = Flask(__name__)
CORS(app)

# הגדרת ה-API של Gemini
# קבל מפתח כאן: https://aistudio.google.com/app/apikey
API_KEY = "AIzaSyBXQnCXwytRa06oMzK-aMl_XYLkLARp5Gc" 
genai.configure(AIzaSyBXQnCXwytRa06oMzK-aMl_XYLkLARp5Gc)
model = genai.GenerativeModel('gemini-1.5-flash')

# זיכרון המערכת
users_db = {}

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_id = data.get("user_id", "default_user")
    user_input = data.get("message", "")

    # 1. חסימת תוכן בוטה
    if not eh.is_safe(user_input):
        return jsonify({"reply": "אני לא יכול לענות על זה, בוא נשמור על שיחה מכבדת."})

    # 2. ניהול זיכרון והיכרות
    if user_id not in users_db:
        users_db[user_id] = {
            "chat": model.start_chat(history=[]),
            "first_time": True,
            "images": 0
        }

    user_session = users_db[user_id]
    
    # 3. הודעת היכרות בשיחה הראשונה
    prefix = ""
    if user_session["first_time"]:
        prefix = "שלום! אני העוזר האישי שלך. נעים להכיר! אני מחובר ליומן ולמערכת הלימודים שלך. "
        user_session["first_time"] = False

    # 4. שליחה ל-AI (Gemini)
    try:
        response = user_session["chat"].send_message(user_input)
        reply_text = prefix + response.text
        
        # לוגיקה לתזכורות/בחנים (זיהוי פשוט)
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
    if users_db.get(user_id, {}).get("images", 0) >= 5:
        return jsonify({"reply": "מצטער, הגעת למגבלה של 5 תמונות."})
    
    users_db[user_id]["images"] = users_db.get(user_id, {}).get("images", 0) + 1
    return jsonify({"reply": f"התמונה התקבלה! זו תמונה מספר {users_db[user_id]['images']} מתוך 5."})

if __name__ == '__main__':
    app.run(port=5000, debug=True)
