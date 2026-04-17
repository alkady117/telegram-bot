import requests
import random
import string
import uuid
import time
from datetime import datetime
import os
import re

BOT_TOKEN = "8793025912:AAGjwWlk0ayj1CU9scBh8mxt9v8hu94OTsk"

karbo_api = f"https://api.telegram.org/bot{BOT_TOKEN}"

user_states = {}

state_karbo = {
    "ar": {
        "welcome": "- هلا حب اختار شتريد :",
        "btn_reset": "ارسال ريست",
        "btn_change": "تغيير باسورد",
        "ask_user": "ارسل الايميل او اليوزر:",
        "ask_link": "- ارسل رابط الريست :",
        "ask_pass": "- ارسل كلمة السر الجديدة:",
        "success_reset": "- تم ارسال الريست\n{}",
        "fail_reset": "- فشل الارسال\n{}",
        "success_pass": "- تم تغيير الباسورد بنجاح\nالباسورد الجديد : {}",
        "fail_pass": "- فشل تغيير الباسورد\n{}",
        "choose_lang": "- اختر اللغة / Choose Language :",
        "btn_ar": "العربية",
        "btn_en": "English",
    },
    "en": {
        "welcome": "- Hello my love choose :",
        "btn_reset": "Send Reset",
        "btn_change": "Change Password",
        "ask_user": "- Send your Email or Username :",
        "ask_link": "- Send the Reset Link :",
        "ask_pass": "- Send the new password :",
        "success_reset": "- Reset sent successfully\n{}",
        "fail_reset": "- Failed to send reset\n{}",
        "success_pass": "- Password changed successfully\nNew password: {}",
        "fail_pass": "- Failed to change password\n{}",
        "choose_lang": "- اختر اللغة / Choose Language :",
        "btn_ar": "العربية",
        "btn_en": "English",
    }
}

def t(chat_id, key):
    lang = user_states.get(chat_id, {}).get("lang", "ar")
    return state_karbo[lang][key]

def send_message(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        requests.post(f"{karbo_api}/sendMessage", json=payload, timeout=10)
    except:
        pass

def answer_callback(callback_id, text=""):
    try:
        requests.post(f"{karbo_api}/answerCallbackQuery", json={"callback_query_id": callback_id, "text": text}, timeout=10)
    except:
        pass

def lang_menu(chat_id):
    markup = {
        "inline_keyboard": [
            [
                {"text": state_karbo["ar"]["btn_ar"], "callback_data": "lang_ar"},
                {"text": state_karbo["ar"]["btn_en"], "callback_data": "lang_en"}
            ]
        ]
    }
    send_message(chat_id, state_karbo["ar"]["choose_lang"], markup)

def main_menu(chat_id):
    markup = {
        "inline_keyboard": [
            [{"text": t(chat_id, "btn_reset"), "callback_data": "send_reset"}],
            [{"text": t(chat_id, "btn_change"), "callback_data": "change_pass"}]
        ]
    }
    send_message(chat_id, t(chat_id, "welcome"), markup)

def get_updates(offset=None):
    params = {"timeout": 30, "allowed_updates": ["message", "callback_query"]}
    if offset:
        params["offset"] = offset
    try:
        r = requests.get(f"{karbo_api}/getUpdates", params=params, timeout=35)
        return r.json().get("result", [])
    except:
        return []

def send_reset_request(user):
    try:
        headers = {
            "user-agent": "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36",
            "x-ig-app-id": "936619743392459",
            "x-requested-with": "XMLHttpRequest",
            "x-csrftoken": "missing",
            "origin": "https://www.instagram.com",
            "referer": "https://www.instagram.com/accounts/password/reset/",
            "content-type": "application/x-www-form-urlencoded"
        }
        r = requests.post(
            "https://www.instagram.com/api/v1/web/accounts/account_recovery_send_ajax/",
            headers=headers,
            data={"email_or_username": user},
            timeout=20
        )
        if r.status_code == 200:
            response = r.json()
            contact = response.get('contact_point', 'Not found')
            return {"success": True, "contact": contact}
        else:
            return {"success": False, "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def change_password(link, new_password):
    try:
        try:
            uidb36 = link.split("uidb36=")[1].split("&token=")[0]
            token = link.split("&token=")[1].split(":")[0]
        except:
            return {"success": False, "error": "رابط غير صالح"}
        device_id = f"android-{''.join(random.choices(string.hexdigits.lower(), k=16))}"
        ts = int(datetime.now().timestamp())
        url = "https://i.instagram.com/api/v1/accounts/password_reset/"
        data = {
            "source": "one_click_login_email",
            "uidb36": uidb36,
            "device_id": device_id,
            "token": token,
            "waterfall_id": str(uuid.uuid4())
        }
        headers = {
            "User-Agent": "Instagram 394.0.0.46.81 Android",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        }
        r = requests.post(url, headers=headers, data=data)
        if "user_id" in r.text:
            return {"success": True, "password": new_password}
        else:
            return {"success": False, "error": "فشل تغيير الباسورد"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def handle_message(message):
    chat_id = message["chat"]["id"]
    text = message.get("text", "")
    if chat_id not in user_states:
        user_states[chat_id] = {"state": "idle", "lang": "ar"}
    if text == "/start":
        user_states[chat_id] = {"state": "choosing_lang", "lang": "ar"}
        lang_menu(chat_id)
        return
    state_data = user_states.get(chat_id, {"state": "idle", "lang": "ar"})
    state = state_data.get("state", "idle")
    if state == "waiting_user_reset":
        result = send_reset_request(text.strip())
        if result.get("success"):
            send_message(chat_id, t(chat_id, "success_reset").format(result["contact"]))
        else:
            send_message(chat_id, t(chat_id, "fail_reset").format(result.get("error", "")))
        user_states[chat_id]["state"] = "idle"
        main_menu(chat_id)
    elif state == "waiting_reset_link":
        user_states[chat_id]["state"] = "waiting_new_pass"
        user_states[chat_id]["data"] = {"link": text.strip()}
        send_message(chat_id, t(chat_id, "ask_pass"))
    elif state == "waiting_new_pass":
        link = state_data.get("data", {}).get("link", "")
        new_pass = text.strip()
        result = change_password(link, new_pass)
        if result.get("success"):
            send_message(chat_id, t(chat_id, "success_pass").format(f"<code>{result['password']}</code>"))
        else:
            send_message(chat_id, t(chat_id, "fail_pass").format(result.get("error", "")))
        user_states[chat_id]["state"] = "idle"
        main_menu(chat_id)
    else:
        main_menu(chat_id)

def handle_callback(callback):
    chat_id = callback["message"]["chat"]["id"]
    data = callback.get("data", "")
    callback_id = callback["id"]
    answer_callback(callback_id)
    if chat_id not in user_states:
        user_states[chat_id] = {"state": "idle", "lang": "ar"}
    if data == "lang_ar":
        user_states[chat_id] = {"state": "idle", "lang": "ar"}
        main_menu(chat_id)
    elif data == "lang_en":
        user_states[chat_id] = {"state": "idle", "lang": "en"}
        main_menu(chat_id)
    elif data == "send_reset":
        user_states[chat_id]["state"] = "waiting_user_reset"
        send_message(chat_id, t(chat_id, "ask_user"))
    elif data == "change_pass":
        user_states[chat_id]["state"] = "waiting_reset_link"
        send_message(chat_id, t(chat_id, "ask_link"))

def run():
    print("✅ Bot started!")
    offset = None
    while True:
        try:
            updates = get_updates(offset)
            for update in updates:
                offset = update["update_id"] + 1
                if "message" in update:
                    handle_message(update["message"])
                elif "callback_query" in update:
                    handle_callback(update["callback_query"])
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(1)

if __name__ == "__main__":
    run()
