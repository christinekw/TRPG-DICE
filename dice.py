import streamlit as st
import random
from datetime import datetime

st.set_page_config(page_title="TRPG 技能擲骰器", layout="centered")
st.title("🎲 TRPG 技能擲骰器（含擲骰紀錄）")

# 初始化擲骰紀錄
if "roll_history" not in st.session_state:
    st.session_state.roll_history = []

# --- 技能輸入區 ---
st.header("📝 角色技能設定")

with st.form("skill_input_form"):
    skill_names = st.text_area("請輸入角色技能（每行一項，格式：技能名稱: 數值）", 
        "偵查: 60\n圖書館使用: 50\n說服: 40")
    submitted = st.form_submit_button("更新技能")

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

skills = parse_skills(skill_names)

# --- 判定結果 ---
def get_result(roll, skill_val):
    if roll == 1:
        return "🎯 極限大成功"
    elif roll <= skill_val / 5:
        return "🔥 極限成功"
    elif roll <= skill_val / 2:
        return "💪 困難成功"
    elif roll <= skill_val:
        return "✅ 一般成功"
    elif roll >= 96 and skill_val < 50:
        return "💀 大失敗"
    else:
        return "❌ 失敗"

# --- 擲骰區 ---
st.header("🎯 技能擲骰")

for skill, value in skills.items():
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"**{skill}**（{value}%）")
    with col2:
        if st.button(f"擲 {skill}"):
            roll = random.randint(1, 100)
            result = get_result(roll, value)
            timestamp = datetime.now().strftime("%H:%M:%S")
            st.success(f"{skill} 擲骰結果：{roll} → {result}")
            st.session_state.roll_history.insert(0, {
                "time": timestamp,
                "skill": skill,
                "roll": roll,
                "value": value,
                "result": result
            })

# --- 擲骰紀錄 ---
st.header("📜 擲骰紀錄")

if st.session_state.roll_history:
    for entry in st.session_state.roll_history[:10]:
        st.markdown(
            f"**[{entry['time']}]** `{entry['skill']}` "
            f"（技能值: {entry['value']}%）→ 🎲 **{entry['roll']}** → {entry['result']}"
        )
else:
    st.info("尚無擲骰紀錄。請開始擲骰！")

# 清除紀錄按鈕
if st.button("🗑 清除擲骰紀錄"):
    st.session_state.roll_history.clear()
    st.success("已清除所有紀錄。")
