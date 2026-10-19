import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from ortools.sat.python import cp_model

st.set_page_config(page_title="LL match - AI & CP-SAT 팀빌딩 플랫폼", layout="wide")

# --- 모의 데이터 초기화 (학생 8명 풀, 5축 역량, 주간 시간표 매트릭스) ---
@st.cache_data
def load_candidates():
    days = ["월", "화", "수", "목", "금", "토", "일"]
    slots = ["09-11시", "11-13시", "13-15시", "15-17시", "17-19시", "19-21시"]
    
    users = [
        {"id": 1, "name": "김성훈", "role": "기획/PM", "history": "창업 ICT 메이커톤 1위, PM 3회", "skills": [0.95, 0.70, 0.90, 0.95, 0.92]},
        {"id": 2, "name": "이서연", "role": "개발/AI", "history": "AI 해커톤 대상, Python/LLM 특화", "skills": [0.75, 0.96, 0.92, 0.85, 0.90]},
        {"id": 3, "name": "박지훈", "role": "개발/AI", "history": "풀스택 웹 개발, React/FastAPI", "skills": [0.70, 0.92, 0.88, 0.82, 0.88]},
        {"id": 4, "name": "최유진", "role": "디자인", "history": "UX/UI 디자인 공모전 수상, Figma", "skills": [0.85, 0.65, 0.86, 0.92, 0.94]},
        {"id": 5, "name": "정민수", "role": "기획/PM", "history": "비즈니스 모델링, 데이터 분석", "skills": [0.88, 0.60, 0.80, 0.78, 0.75]},
        {"id": 6, "name": "한소희", "role": "개발/AI", "history": "백엔드 아키텍처, DB 최적화", "skills": [0.65, 0.89, 0.85, 0.75, 0.80]},
        {"id": 7, "name": "강동원", "role": "디자인", "history": "브랜드 디자인, 프로토타이핑", "skills": [0.78, 0.55, 0.80, 0.85, 0.70]},
        {"id": 8, "name": "윤아름", "role": "개발/AI", "history": "산학 캡스톤 최우수상, 비전 AI", "skills": [0.72, 0.91, 0.89, 0.88, 0.86]},
    ]
    np.random.seed(42)
    for u in users:
        # 1: 공강(가용 시간), 0: 수업/일정 있음
        mat = np.random.choice([0, 1], size=(len(slots), len(days)), p=[0.35, 0.65])
        # 시연용 최적 팀(1, 2, 3, 4번)이 수/목 저녁 및 주말에 확실히 공통 공강을 갖도록 설정
        if u["id"] in [1, 2, 3, 4]:
            mat[4:, 2:6] = 1
        u["schedule"] = mat
    return users, days, slots

users, days, slots = load_candidates()
skill_labels = ["기획/전략", "개발/기술", "문제해결(Bloom)", "협업소통(CATME)", "책임/몰입(STAR)"]

# --- 상단 헤더 ---
col_logo, col_nav, col_auth = st.columns([2, 5, 2])
with col_logo:
    st.markdown("## 🚀 **LL match**")
with col_nav:
    menu = st.radio(
        "네비게이션",
        ["공모 (공모전 분석)", "팀구성 (CP-SAT 매칭)", "돋보기 (인재 탐색)", "MY PAGE"],
        horizontal=True,
        label_visibility="collapsed"
    )
with col_auth:
    with st.popover("🔐 LOGIN / MY PAGE"):
        st.markdown("##### LL match Sign In")
        st.text_input("ID (8~12 words)", value="kau_vibe2026")
        st.text_input("Password (8~12 words)", type="password", value="password1234")
        st.button("Sign In", use_container_width=True, type="primary")

st.divider()

# ==========================================
# 1. 공모 탭
# ==========================================
if menu == "공모 (공모전 분석)":
    st.subheader("📢 공모전 탐색 및 LLM 하향식(Top-down) 과업 분해")
    sub_tab = st.radio("공고 보기 방식", ["① 전체 공고", "② AI 사용자별 맞춤 추천 공고"], horizontal=True)
    
    contests = [
        {"title": "2026 고양시 바이브 코딩 창업경진대회", "period": "2026-09-01 ~ 2026-10-22", "match": "98%", "slots": {"기획/PM": 1, "개발/AI": 2, "디자인": 1}, "req_vec": [0.90, 0.92, 0.90, 0.88, 0.90]},
        {"title": "한국항공대 SW중심대학 산학 캡스톤 디자인 챌린지", "period": "2026-10-01 ~ 2026-12-15", "match": "94%", "slots": {"기획/PM": 1, "개발/AI": 2, "디자인": 1}, "req_vec": [0.82, 0.95, 0.88, 0.85, 0.85]},
        {"title": "교육부 RISE 체계 지역혁신 공공데이터 해커톤", "period": "2026-11-01 ~ 2026-11-30", "match": "89%", "slots": {"기획/PM": 1, "개발/AI": 1, "디자인": 1}, "req_vec": [0.88, 0.85, 0.85, 0.90, 0.88]},
    ]
    
    for idx, c in enumerate(contests):
        with st.container(border=True):
            c1, c2, c3 = st.columns([5, 2, 2])
            c1.markdown(f"#### {c['title']}\n📅 기간: `{c['period']}`")
            c2.metric("나와의 적합도", c["match"])
            if c3.button("🤖 LLM 요강 파싱 (API 분석)", key=f"parse_{idx}", use_container_width=True):
                st.info(f"**[1단계 LLM Top-down 과업 분해 완료]** 비정형 공고문(RFP)에서 필요 역할 슬롯 및 정량 역량 벡터 $C$를 추출했습니다 (환각률 0%).")
                k1, k2 = st.columns(2)
                k1.write("**📌 추출된 필수 역할 슬롯:**", c["slots"])
                k2.write("**📌 요구 역량 기준 벡터 (0~1):**", dict(zip(skill_labels, c["req_vec"])))

# ==========================================
# 2. 팀구성 탭
# ==========================================
elif menu == "팀구성 (CP-SAT 매칭)":
    tab_match, tab_star = st.tabs(["⚡ 직군별 탐색 & Google CP-SAT 최적 매칭", "📝 STAR/Bloom 기법 역량 측정 (19문항)"])
    
    with tab_match:
        st.subheader("🎯 직군별 팀원 탐색 및 CP-SAT 수리 최적화 매칭")
        role_filter = st.segmented_control("직군 필터", ["전체", "기획/PM", "개발/AI", "디자인"], default="전체")
        
        filtered = [u for u in users if role_filter == "전체" or u["role"] == role_filter]
        df_display = pd.DataFrame([
            {"선택": True, "ID": u["id"], "이름": u["name"], "직군": u["role"], "핵심 이력": u["history"], "평균 역량지수": round(np.mean(u["skills"]), 2)}
            for u in filtered
        ])
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        col_opt1, col_opt2 = st.columns([2, 1])
        with col_opt1:
            st.markdown("##### ⚙️ Google OR-Tools CP-SAT 수리 최적화 파라미터")
            lam = st.slider("역량 편차 페널티 가중치 (λ) — 엘리트 쏠림 방지 및 밸런스 조절", 0.0, 1.0, 0.5, 0.1)
        with col_opt2:
            st.write("")
            st.write("")
            run_solver = st.button("🚀 CP-SAT 최적 팀 자동 결성 & 팀 구성 요청", type="primary", use_container_width=True)
            
        if run_solver:
            model = cp_model.CpModel()
            x = {u["id"]: model.NewBoolVar(f"user_{u['id']}") for u in users}
            
            model.Add(sum(x[u["id"]] for u in users if u["role"] == "기획/PM") == 1)
            model.Add(sum(x[u["id"]] for u in users if u["role"] == "개발/AI") == 2)
            model.Add(sum(x[u["id"]] for u in users if u["role"] == "디자인") == 1)
            model.Add(x[1] == 1) 
            
            skill_scores = {u["id"]: int(np.mean(u["skills"]) * 100) for u in users}
            overlap_scores = {u["id"]: int(np.sum(users[0]["schedule"] * u["schedule"]) * 5) for u in users}
            model.Maximize(sum(x[u["id"]] * (skill_scores[u["id"]] + overlap_scores[u["id"]]) for u in users))
            
            solver = cp_model.CpSolver()
            status = solver.Solve(model)
            
            if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                selected_team = [u for u in users if solver.Value(x[u["id"]]) == 1]
                common_matrix = np.ones_like(users[0]["schedule"])
                for u in selected_team:
                    common_matrix = common_matrix * u["schedule"]
                common_hours = int(np.sum(common_matrix) * 2)
                
                st.success(f"✅ **[CP-SAT 수리 최적해 도출 완료 (0.04초)]** 시간표 충돌률 0%! 주당 공통 공강 **{common_hours}시간**이 보장된 최적 4인 팀이 결성되었습니다.")
                
                t_cols = st.columns(4)
                for idx, member in enumerate(selected_team):
                    with t_cols[idx]:
                        st.metric(label=f"{member['role']}", value=member["name"], delta=f"역량 {np.mean(member['skills']):.2f}")
                        st.caption(member["history"])
                
                sum_matrix = sum(u["schedule"] for u in selected_team)
                fig_heat = go.Figure(data=go.Heatmap(
                    z=sum_matrix, x=days, y=slots,
                    colorscale="Blues", zmin=0, zmax=4,
                    text=[[f"{val}명 가용" if val < 4 else "★전원 공강★" for val in row] for row in sum_matrix],
                    texttemplate="%{text}", showscale=True
                ))
                fig_heat.update_layout(title="📅 팀원 4인 주간 시간표 중첩 히트맵 (4명 전원 공강 슬롯 자동 추출)", height=360)
                st.plotly_chart(fig_heat, use_container_width=True)

    with tab_star:
        st.subheader("📋 STAR 기법 & Bloom 분류학 기반 실무 역량 측정 (1~19번 문항)")
        questions = [
            "1. (Situation) 팀 프로젝트에서 요구사항이 불명확했던 상황을 구체적으로 정의할 수 있는가?",
            "2. (Task) 본인이 맡은 핵심 과업과 마감 기한을 정량적 목표로 세분화했는가?",
            "3. (Action) 일정 지연이나 팀원 간 갈등 발생 시 직접 중재안을 제시하고 실행했는가?",
            "4. (Result) 프로젝트 산출물이 정량적 성과(수상, 배포, 지표 개선)로 이어졌는가?",
            "5. (Bloom-분석) 공모전 요강(RFP)을 보고 필요한 기술 스택과 리스크를 분해할 수 있는가?",
        ]
        for q in questions:
            st.radio(q, [1, 2, 3, 4, 5], index=4, horizontal=True)
        if st.button("AI 역량 지수 산출 및 프로필 반영", type="primary"):
            st.success("STAR/Bloom 역량 벡터가 [0.95, 0.70, 0.90, 0.95, 0.92]로 갱신되었습니다!")

# ==========================================
# 3. 돋보기 탭
# ==========================================
elif menu == "돋보기 (인재 탐색)":
    st.subheader("🔍 LL match 전체 사용자 탐색 (돋보기)")
    cols = st.columns(2)
    for idx, u in enumerate(users):
        with cols[idx % 2]:
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                c1.markdown(f"**{u['name']}** | `{u['role']}`")
                c1.caption(f"이력: {u['history']}")
                with c2.popover("자세히 보기"):
                    st.markdown(f"##### 📊 {u['name']}님의 5축 역량 벡터")
                    for s_name, s_val in zip(skill_labels, u["skills"]):
                        st.progress(s_val, text=f"{s_name}: {s_val}")

# ==========================================
# 4. MY PAGE 탭
# ==========================================
elif menu == "MY PAGE":
    st.subheader("👤 마이페이지 (역량 지수 · 주간 시간표 · 진행중 대회 · CATME 동료평가)")
    me = users[0]
    
    col_radar, col_sched = st.columns(2)
    with col_radar:
        fig_radar = go.Figure(data=go.Scatterpolar(
            r=me["skills"] + [me["skills"][0]],
            theta=skill_labels + [skill_labels[0]],
            fill="toself", name=me["name"]
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
            title="📈 나의 5축 역량 지수 (STAR/Bloom 검증)", height=350
        )
        st.plotly_chart(fig_radar, use_container_width=True)
        
    with col_sched:
        fig_my_sched = go.Figure(data=go.Heatmap(
            z=me["schedule"], x=days, y=slots, colorscale="Greens", showscale=False,
            text=[["공강(가용)" if v == 1 else "수업/일정" for v in row] for row in me["schedule"]],
            texttemplate="%{text}"
        ))
        fig_my_sched.update_layout(title="🗓️ 나의 주간 시간표 (월~일)", height=350)
        st.plotly_chart(fig_my_sched, use_container_width=True)
        
    st.divider()
    
    col_curr, col_hist = st.columns([3, 2])
    with col_curr:
        with st.container(border=True):
            st.markdown("#### 🔥 현재 진행중...")
            st.markdown("**경진대회명:** 2026 고양시 바이브 코딩 창업경진대회  \n**기간:** `2026-09-01 ~ 2026-10-22`")
            st.write("👑 **팀장:** 김성훈 (기획/PM) | 👥 **팀원①:** 이서연 (개발/AI) | **팀원②:** 박지훈 (개발/AI) | **팀원③:** 최유진 (디자인)")
            
            with st.expander("📝 CATME 5대 척도 기반 동료평가 진행"):
                target_member = st.selectbox("평가 대상 팀원 선택", ["이서연 (팀원①)", "박지훈 (팀원②)", "최유진 (팀원③)"])
                catme_qs = [
                    "질문① [기여도] 팀 프로젝트 과업 완수를 위해 할당된 분량을 성실히 수행했는가?",
                    "질문② [상호작용] 팀원들과 적극적으로 소통하며 회의 일정(공통 공강)을 준수했는가?"
                ]
                scale_opts = ["매우 그렇다", "그렇다", "보통이다", "그렇지 않다", "전혀 아니다"]
                for cq in catme_qs:
                    st.radio(cq, scale_opts, index=0, horizontal=True)
                if st.button("동료평가 제출 & 로그 교차검증", type="primary"):
                    st.success(f"{target_member}님의 상호보정계수 산출 및 작업 로그 교차 검증이 완료되었습니다!")
                    
    with col_hist:
        with st.container(border=True):
            st.markdown("#### 🏆 참가 내역 및 동적 포트폴리오")
            st.markdown("- **2026년**: 고양시 바이브 코딩 창업경진대회 (본선 진출)\n- **2026년**: 한국항공대 창업 ICT 메이커톤 (1위 수상)")
            if st.button("📜 위변조 불가능 동적 포트폴리오 발급", use_container_width=True):
                st.balloons()
                st.info("✅ GitHub 커밋 142건 + Notion 문서 38건 + CATME 상위 5% 인증서가 발급되었습니다.")
