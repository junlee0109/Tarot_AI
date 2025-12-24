import os
import json
import random
import streamlit as st
from dotenv import load_dotenv
from typing import Dict, List

from groq import Groq

load_dotenv()

st.set_page_config(
    page_title="Tarot AI (Groq)",
    page_icon="🃏",
    layout="wide"
)

# =========================
# 타로 카드 (Major Arcana)
# =========================
MAJOR_ARCANA = [
    {"ko": "바보", "name": "The Fool", "keywords": ["시작", "자유", "모험"], "light": "새로운 시작"},
    {"ko": "마법사", "name": "The Magician", "keywords": ["의지", "기술", "실현"], "light": "현실로 만드는 힘"},
    {"ko": "여사제", "name": "The High Priestess", "keywords": ["직감", "내면"], "light": "직감을 믿어라"},
    {"ko": "여황제", "name": "The Empress", "keywords": ["풍요", "성장"], "light": "안정과 성장"},
    {"ko": "황제", "name": "The Emperor", "keywords": ["질서", "책임"], "light": "기반을 다져라"},
    {"ko": "연인", "name": "The Lovers", "keywords": ["선택", "관계"], "light": "중요한 선택"},
    {"ko": "전차", "name": "The Chariot", "keywords": ["전진", "의지"], "light": "돌파의 시기"},
    {"ko": "힘", "name": "Strength", "keywords": ["인내", "자제"], "light": "부드러운 강함"},
    {"ko": "은둔자", "name": "The Hermit", "keywords": ["성찰", "고독"], "light": "내면을 보라"},
    {"ko": "운명의 수레바퀴", "name": "Wheel of Fortune", "keywords": ["변화", "기회"], "light": "흐름이 바뀐다"},
    {"ko": "정의", "name": "Justice", "keywords": ["균형", "판단"], "light": "공정한 선택"},
    {"ko": "죽음", "name": "Death", "keywords": ["끝", "변화"], "light": "새출발"},
    {"ko": "별", "name": "The Star", "keywords": ["희망", "치유"], "light": "회복의 신호"},
    {"ko": "달", "name": "The Moon", "keywords": ["불안", "착각"], "light": "감정 점검"},
    {"ko": "태양", "name": "The Sun", "keywords": ["성공", "행복"], "light": "긍정적 결과"},
    {"ko": "세계", "name": "The World", "keywords": ["완성", "성취"], "light": "마무리"},
]

CATEGORIES = ["총운", "연애운", "금전운", "건강운"]

# =========================
# 상태
# =========================
if "deck" not in st.session_state:
    st.session_state.deck = []
if "picked" not in st.session_state:
    st.session_state.picked = []
if "result" not in st.session_state:
    st.session_state.result = None

# =========================
# 유틸
# =========================
def shuffle_deck():
    cards = MAJOR_ARCANA.copy()
    random.shuffle(cards)
    deck = []
    for i, c in enumerate(cards):
        upright = random.choice([True, False])
        deck.append({
            "slot": i,
            "ko": c["ko"],
            "name": c["name"],
            "keywords": c["keywords"],
            "meaning": c["light"],
            "upright": upright
        })
    return deck

def reset():
    st.session_state.deck = shuffle_deck()
    st.session_state.picked = []
    st.session_state.result = None

def selected_cards():
    return [st.session_state.deck[i] for i in st.session_state.picked]

def cards_for_prompt(cards: List[Dict]) -> str:
    lines = []
    for i, c in enumerate(cards, 1):
        pos = "정방향" if c["upright"] else "역방향"
        lines.append(
            f"{i}. {c['name']}({c['ko']}) - {pos}\n"
            f"키워드: {', '.join(c['keywords'])}\n"
            f"의미: {c['meaning']}"
        )
    return "\n".join(lines)

# =========================
# Groq AI 해석 (안정 모델)
# =========================
def groq_fortune(cards: List[Dict]) -> Dict[str, str]:
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    prompt_cards = cards_for_prompt(cards)

    prompt = f"""
선택된 타로 카드 3장:
{prompt_cards}

규칙:
- 카드 키워드와 의미에 근거해서만 해석
- 상상으로 내용 추가 금지
- 각 운세에 카드 이름 또는 키워드 언급

운세 종류:
- 총운
- 연애운
- 금전운
- 건강운

출력은 반드시 JSON:
{{
  "총운": "...",
  "연애운": "...",
  "금전운": "...",
  "건강운": "..."
}}
"""

    res = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        temperature=0.8,
        messages=[
            {"role": "system", "content": "너는 카드 근거로만 판단하는 현실적인 타로 해석가다."},
            {"role": "user", "content": prompt},
        ],
    )

    text = res.choices[0].message.content
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("AI 응답에서 JSON을 찾을 수 없음")

    return json.loads(text[start:end + 1])

# =========================
# UI
# =========================
st.title("🃏 Tarot AI (Groq)")
st.caption("Groq LLaMA · 카드 기반 판단")

if not st.session_state.deck:
    reset()

if st.button("🔁 새로 섞기"):
    reset()
    st.rerun()

st.subheader("카드 선택 (3장)")
cols = st.columns(6)
for i, c in enumerate(st.session_state.deck):
    col = cols[i % 6]
    label = "🂠" if i not in st.session_state.picked else "✅ 🂠"
    disabled = i not in st.session_state.picked and len(st.session_state.picked) >= 3
    if col.button(label, key=f"card_{i}", disabled=disabled):
        if i in st.session_state.picked:
            st.session_state.picked.remove(i)
        else:
            st.session_state.picked.append(i)
        st.session_state.result = None
        st.rerun()

if st.button("🔮 운세 보기", type="primary"):
    if len(st.session_state.picked) != 3:
        st.warning("카드를 정확히 3장 선택하세요.")
    else:
        with st.spinner("Groq AI 해석 중..."):
            st.session_state.result = groq_fortune(selected_cards())

if st.session_state.result:
    st.subheader("✨ 결과")
    tabs = st.tabs(CATEGORIES)
    for t, k in zip(tabs, CATEGORIES):
        with t:
            st.markdown(st.session_state.result[k])
