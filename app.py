import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import random
import time
# dice functions
def evaluate_result(roll, skill):
    if roll == 1:
        return "🎯 極限成功"
    elif roll <= skill / 5:
        return "🎯 極限成功"
    elif roll <= skill / 2:
        return "💪 困難成功"
    elif roll <= skill:
        return "✅ 一般成功"
    elif roll >= 96 and skill < 50:
        return "💀 大失敗"
    else:
        return "❌ 失敗"
def parse_dice_setting(dice_setting):
    try:
        num, die = map(int, dice_setting.split('d'))
        return num, die
    except ValueError:
        st.error("骰子設定格式錯誤，請使用 'XdY' 格式，例如 '1d100'")
        return None, None
#skill setting
def parse_skills(text):
        skills = {}
        for line in text.strip().splitlines():
            if ":" in line:
                name, val = line.split(":", 1)
                try:
                    skills[name.strip()] = int(val.strip())
                except ValueError:
                    pass
        return skills
# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate({
        "type": st.secrets.firebase.type,
        "project_id": st.secrets.firebase.project_id,
        "private_key_id": st.secrets.firebase.private_key_id,
        "private_key": st.secrets.firebase.private_key.replace('\\n', '\n'),
        "client_email": st.secrets.firebase.client_email,
        "client_id": st.secrets.firebase.client_id,
        "auth_uri": st.secrets.firebase.auth_uri,
        "token_uri": st.secrets.firebase.token_uri,
        "auth_provider_x509_cert_url": st.secrets.firebase.auth_provider_x509_cert_url,
        "client_x509_cert_url": st.secrets.firebase.client_x509_cert_url,
    })
    firebase_admin.initialize_app(cred, {
        "databaseURL": "https://trpgdice-af12e-default-rtdb.asia-southeast1.firebasedatabase.app/"
    })
    st.session_state.firebase_initialized = True

# Helper: Get room ref
def get_room_ref(room_id):
    return db.reference(f"rooms/{room_id}")

# UI: Room join/create
st.title("TRPG 線上擲骰器")
st.subheader("請輸入房間資訊")

room_id = st.text_input("房間 ID")
room_password = st.text_input("房間密碼", type="password")
mode = st.radio("選擇模式", ["加入房間", "創建房間"])

if st.button("進入房間"):
    if not room_id or not room_password:
        st.error("請輸入房間 ID 與密碼")
    else:
        room_ref = get_room_ref(room_id)
        room_data = room_ref.get()

        if mode == "創建房間":
            if room_data:
                st.error("房間已存在，請選擇加入")
            else:
                room_ref.set({
                    "password": room_password,
                    "history": []
                })
                st.success("房間已建立！")
                st.session_state.in_room = True
                st.session_state.room_id = room_id
        elif mode == "加入房間":
            if not room_data:
                st.error("房間不存在")
            elif room_data.get("password") != room_password:
                st.error("密碼錯誤")
            else:
                st.success("成功進入房間！")
                st.session_state.in_room = True
                st.session_state.room_id = room_id

# Main UI after room join
if st.session_state.get("in_room"):
    st.header(f"🎲 房間：{st.session_state.room_id}")
    # --- Skill Input Section ---
    st.header("📝 Character Skills")

    # Let user define a list of skills
    with st.form("skill_input_form"):
        skill_names = st.text_area("Enter skills (one per line, format: SkillName: Points)", 
            "Spot Hidden: 60\nLibrary Use: 50\nPersuade: 40")
        submitted = st.form_submit_button("Update Skills")
    # Parse skills into dictionary
    

    skills = parse_skills(skill_names)
    st.markdown("### 自定義擲骰區域")
    pc_name = st.text_input("玩家名稱", value="玩家")
    skill_point = st.number_input("請輸入技能點數", min_value=0, max_value=100, value=50)
    skill_name = st.text_input("技能名稱", value="技能")
    dice_setting = st.text_input("骰子設定 (例如：1d100)", value="1d100")
    num,die = parse_dice_setting(dice_setting)
    for skill, value in skills.items():
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"**{skill}** ({value}%)")
        with col2:
            if st.button(f"Roll {skill}"):
                for _ in range(num):
                    roll = random.randint(1, die)
                    result = evaluate_result(roll, value)
                    timestamp = time.strftime("%H:%M:%S", time.localtime())
                    record = {
                    "pc_name": pc_name,
                    "skill":skill_name,
                    "roll": roll,
                    "result": result,
                    "skill_point": skill_point,
                    "timestamp": timestamp
                    }
                    # Append to Firebase history
                    history_ref = get_room_ref(st.session_state.room_id).child("history")
                    history_ref.push(record)
            
    if st.button("擲骰！"):
        for _ in range(num):
            roll = random.randint(1, die)
            result = evaluate_result(roll, skill_point)
            timestamp = int(time.time())
            record = {
                "pc_name": pc_name,
                "skill":skill_name,
                "roll": roll,
                "result": result,
                "skill_point": skill_point,
                "timestamp": timestamp
            }
            # Append to Firebase history
            history_ref = get_room_ref(st.session_state.room_id).child("history")
            history_ref.push(record)

    # Load and display history
    st.markdown("### 擲骰紀錄")
    history_ref = get_room_ref(st.session_state.room_id).child("history")
    history = history_ref.get() or {}

    # Sort by time
    sorted_history = sorted(history.values(), key=lambda x: x['timestamp'], reverse=True)

    for item in sorted_history:
        st.write(f"🎲{item['pc_name']} 進行{item["skill"]}投掷，擲出: {item['roll']}，技能值: {item['skill_point']}，結果: {item['result']}")

    # Auto-refresh every 5 sec
    time.sleep(5)
    st.rerun()

