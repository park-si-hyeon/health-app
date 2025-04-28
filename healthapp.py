import streamlit as st
import pandas as pd
import sqlite3
import requests

# 데이터베이스 초기화
conn = sqlite3.connect('workout.db', check_same_thread=False)
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS workouts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        muscle TEXT,
        exercise TEXT,
        set_number INTEGER,
        reps INTEGER,
        weight REAL
    )
''')
conn.commit()

st.title("Workout Logger 🚀")

# 날짜 선택
date = st.date_input("운동 날짜를 선택하세요")

# Wger API로부터 부위 목록 가져오기
@st.cache_data
async def get_muscles():
    url = "https://wger.de/api/v2/muscle/?language=2"
    data = requests.get(url).json()
    return {m['name']: m['id'] for m in data['results']}

muscles = st.selectbox("운동 부위를 선택하세요", list(scr := get_muscles().items()), format_func=lambda x: x[0])
muscle_name, muscle_id = muscles

# 선택한 부위의 운동 가져오기
@st.cache_data
async def get_exercises(muscle_id):
    url = f"https://wger.de/api/v2/exercise?language=2&muscles={muscle_id}"
    data = requests.get(url).json()
    return data['results']

exercises = get_exercises(muscle_id)
ex_name = st.selectbox("운동 종류를 선택하세요", [e['name'] for e in exercises])

# 운동 이미지 표시
ex_id = next(e['id'] for e in exercises if e['name'] == ex_name)
img_data = requests.get(f"https://wger.de/api/v2/exerciseimage/?exercise={ex_id}").json()
if img_data['results']:
    st.image(img_data['results'][0]['image'], caption=ex_name)
else:
    st.write("이미지 없음")

# 세트 입력
num_sets = st.number_input("세트 수", min_value=1, max_value=10, value=3)
sets = []
for i in range(1, num_sets + 1):
    st.write(f"### 세트 {i}")
    reps = st.number_input(f"횟수 (세트 {i})", min_value=0, value=10, key=f"reps_{i}")
    weight = st.number_input(f"무게 (kg, 세트 {i})", min_value=0.0, value=20.0, key=f"weight_{i}")
    sets.append((i, reps, weight))

# 기록 저장 버튼
if st.button("기록 저장"):    
    for set_num, reps, weight in sets:
        c.execute(
            'INSERT INTO workouts (date, muscle, exercise, set_number, reps, weight) VALUES (?, ?, ?, ?, ?, ?)',
            (date.isoformat(), muscle_name, ex_name, set_num, reps, weight)
        )
    conn.commit()
    st.success("저장 완료!")

# 기록 추이 시각화
st.header("운동 기록 추이")
df = pd.read_sql('SELECT * FROM workouts', conn)
if not df.empty:
    df['date'] = pd.to_datetime(df['date'])
    exercise_list = df['exercise'].unique().tolist()
    ex_plot = st.selectbox("그래프로 볼 운동을 선택하세요", exercise_list)
    df_plot = df[df['exercise'] == ex_plot]
    agg = df_plot.groupby('date')['weight'].max().reset_index().sort_values('date')
    agg = agg.set_index('date')
    st.line_chart(agg['weight'])
else:
    st.write("저장된 기록이 없습니다.")

# 실행 안내
st.write("---")
st.write("이 앱을 실행하려면 터미널에서: `streamlit run app.py`")
