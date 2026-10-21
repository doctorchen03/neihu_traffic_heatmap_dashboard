import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# 1. 頁面基本設定
st.set_page_config(
    page_title="內湖晨尖峰車流熱力與 ESG 減碳協商儀表板",
    page_icon="🚘",
    layout="wide"
)

st.title("🚘 內湖平日晨尖峰內科車流熱力與 ESG 減碳協商儀表板")
st.caption("數據驅動政企協商工具｜整合高快速道路與聯外橋樑 VD 流量，精準算演分批上班之交通與 ESG Scope 3 減碳效益")

# 2. 側邊欄控制面板
st.sidebar.header("⚙️ 協商與企業參數設定區")

# 企業規模與彈性工時設定
total_emp = st.sidebar.number_input("🏢 企業/園區總員工人數", min_value=100, max_value=50000, value=10000, step=100)
flex_ratio = st.sidebar.slider(
    "📊 彈性工時參與率 (%)",
    min_value=0, max_value=50, value=30, step=5,
    help="設定推動「核心工時 10:00-16:00 ✕ 三梯次分流到勤」的人數涵蓋率"
) / 100.0

st.sidebar.subheader("🌱 ESG 通勤運具與盤查參數")
car_ratio = st.sidebar.slider("🚗 汽車通勤比例 (%)", 0, 100, 40, step=5) / 100.0
scooter_ratio = st.sidebar.slider("🛵 機車通勤比例 (%)", 0, 100, 60, step=5) / 100.0

# [1] 預估每人每日平均省時（依據彈性工時參與率動態估算，替代手動 Slider）
time_saved = (flex_ratio * 18.5 / 0.30) if flex_ratio > 0 else 0.0
st.sidebar.info(f"⏱️ 預估每人每日平均省時：**{time_saved:.1f}** 分鐘")

# [2] 焦點廊道選擇器
corridors = ["民權大橋", "成美橋", "堤頂大道", "瑞光路", "基湖路"]
selected_corridor = st.sidebar.selectbox("🌉 焦點橋樑/幹道檢視", corridors)

# 3. 數據與計算引擎
time_slots = ["07:00", "07:15", "07:30", "07:45", "08:00", "08:15", "08:30", "08:45", "09:00", "09:15", "09:30"]

# (A) 五大廊道模擬數據模型
corridor_data_map = {
    "民權大橋": {
        "capacity": 6500,
        "base_vc": [0.62, 0.75, 0.92, 1.15, 1.28, 1.35, 1.22, 1.05, 0.82, 0.65, 0.52]
    },
    "成美橋": {
        "capacity": 5500,
        "base_vc": [0.58, 0.71, 0.88, 1.10, 1.24, 1.28, 1.18, 0.98, 0.78, 0.60, 0.48]
    },
    "堤頂大道": {
        "capacity": 7000,
        "base_vc": [0.65, 0.78, 0.95, 1.18, 1.29, 1.32, 1.20, 1.02, 0.80, 0.62, 0.50]
    },
    "瑞光路": {
        "capacity": 4800,
        "base_vc": [0.50, 0.62, 0.78, 0.95, 1.10, 1.15, 1.05, 0.88, 0.70, 0.55, 0.42]
    },
    "基湖路": {
        "capacity": 4000,
        "base_vc": [0.48, 0.59, 0.74, 0.90, 1.05, 1.10, 1.00, 0.82, 0.66, 0.50, 0.38]
    }
}

# 取得目前所選廊道之數據
current_corridor_info = corridor_data_map[selected_corridor]
capacity = current_corridor_info["capacity"]
base_vc_arr = np.array(current_corridor_info["base_vc"])
base_volume = np.round(base_vc_arr * capacity).astype(int)

# 模擬車流轉移：將 08:00–08:45 的尖峰車流拉平轉移至 07:30 與 09:30
shifted_volume = base_volume.copy().astype(float)
peak_indices = [4, 5, 6, 7]  # 08:00 - 08:45
reduction = shifted_volume[peak_indices] * (flex_ratio * 0.65)
shifted_volume[peak_indices] -= reduction
shifted_volume[2] += np.sum(reduction) * 0.5  # 移至 07:30
shifted_volume[8] += np.sum(reduction) * 0.5  # 移至 09:30

max_vc_before = np.max(base_volume) / capacity
max_vc_after = np.max(shifted_volume) / capacity
vc_reduction = (max_vc_before - max_vc_after) / max_vc_before * 100 if max_vc_before > 0 else 0.0

# (B) ESG Scope 3 減碳計算引擎
part_emp = int(total_emp * flex_ratio)
car_users = int(part_emp * car_ratio)
scooter_users = int(part_emp * scooter_ratio)

CAR_IDLING_EF = 0.025      # kg CO2 / min
SCOOTER_IDLING_EF = 0.008  # kg CO2 / min
CAR_SPEED_EF_DIFF = 0.055  # kg CO2 / km
SCOOTER_SPEED_EF_DIFF = 0.017 # kg CO2 / km
avg_km = 20.0

daily_car_co2 = (car_users * time_saved * CAR_IDLING_EF) + (car_users * avg_km * CAR_SPEED_EF_DIFF)
daily_scooter_co2 = (scooter_users * time_saved * SCOOTER_IDLING_EF) + (scooter_users * avg_km * SCOOTER_SPEED_EF_DIFF)
daily_total_co2_kg = daily_car_co2 + daily_scooter_co2
annual_co2_tons = (daily_total_co2_kg * 250) / 1000.0
equivalent_trees = int((daily_total_co2_kg * 250) / 12.0)

# 4. 頂部關鍵 KPI 卡片
col1, col2, col3, col4 = st.columns(4)
col1.metric("晨尖峰最高 V/C 飽和度", f"{max_vc_after:.2f}", f"{-vc_reduction:.1f}%", delta_color="inverse")
col2.metric("道路服務水準 (LOS)", "LOS C/D (順暢)" if max_vc_after >= 1.3 else "LOS E/F (壅塞)")
col3.metric("年度範疇三減碳量", f"{annual_co2_tons:.1f} 公噸 CO₂e", f"每日 -{daily_total_co2_kg:.1f} kg")
col4.metric("等同每年造林效益", f"{equivalent_trees:,} 株樹木", "ESG 永續績效")

st.divider()

# 5. 主圖表分頁
tab1, tab2, tab3, tab4 = st.tabs(["📊 車流削峰填谷對比", "🔥 五大廊道 V/C 熱力圖", "🌿 ESG 減碳量效益盤查", "📄 100 天推動計畫"])

with tab1:
    st.subheader(f"📍 【{selected_corridor}】進城車流：現況集中 vs 三分流模擬對比")
    df_chart = pd.DataFrame({
        "時間區段": time_slots,
        "現況集中車流": base_volume,
        "分流模擬車流": np.round(shifted_volume).astype(int),
        "道路臨界容量上限": [capacity] * len(time_slots)
    })
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=time_slots, y=base_volume, mode='lines+markers', name='現況集中車流 (無分流)', line=dict(color='#E63946', width=3)))
    fig.add_trace(go.Scatter(x=time_slots, y=shifted_volume, mode='lines+markers', name=f'三分流模擬 (參與率 {int(flex_ratio*100)}%)', line=dict(color='#2A9D8F', width=3)))
    fig.add_trace(go.Scatter(x=time_slots, y=[capacity]*len(time_slots), mode='lines', name=f'道路容量臨界線 ({capacity:,} 輛/15min)', line=dict(color='#4A5568', width=2, dash='dash')))
    
    fig.update_layout(xaxis_title="晨尖峰時間區段", yaxis_title="15分鐘車流量 (輛/15min)", hovermode="x unified")
    st.plotly_chart(fig, width='stretch')
    #st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("五大進入內科廊道 15 分鐘 V/C 飽和度動態矩陣")
    
    # 建立動態熱力圖矩陣
    matrix_base_list = [corridor_data_map[c]["base_vc"] for c in corridors]
    matrix_base = np.array(matrix_base_list)
    matrix_sim = matrix_base * (1.0 - flex_ratio * 0.25)
    
    fig_heatmap = px.imshow(
        matrix_sim,
        labels=dict(x="時間區段", y="進城廊道", color="V/C 比值"),
        x=time_slots,
        y=corridors,
        color_continuous_scale="YlOrRd",
        text_auto=".2f"
    )
    st.plotly_chart(fig_heatmap, width='stretch')
    #st.plotly_chart(fig_heatmap, use_container_width=True)
    st.info(f"💡 當前焦點檢視廊道：**{selected_corridor}**（道路容量: {capacity:,} 輛/15min｜現況最高 V/C: {max_vc_before:.2f} ➔ 模擬最高 V/C: {max_vc_after:.2f}）")

with tab3:
    st.subheader("🌱 企業 ESG 範疇三 (Scope 3 - Category 7) 通勤減碳盤查明細")
    
    esg_summary_data = {
        "ESG 盤查指標項目": [
            "企業總員工人數", "彈性工時參與人數", "汽車通勤分流人數", "機車通勤分流人數",
            "預估每人每日平均省時", "每日汽車減碳量 (kg CO₂)", "每日機車減碳量 (kg CO₂)",
            "每日合計減碳量 (kg CO₂)", "年度預估總減碳量 (公噸 CO₂e)", "等同年度造林效益 (株樹木)"
        ],
        "數值與單位": [
            f"{total_emp:,} 人", f"{part_emp:,} 人 ({int(flex_ratio*100)}%)", f"{car_users:,} 人", f"{scooter_users:,} 人",
            f"{time_saved:.1f} 分鐘", f"{daily_car_co2:.2f} kg", f"{daily_scooter_co2:.2f} kg",
            f"{daily_total_co2_kg:.2f} kg", f"{annual_co2_tons:.2f} 公噸", f"{equivalent_trees:,} 株"
        ]
    }
    df_esg = pd.DataFrame(esg_summary_data)
    st.table(df_esg)
    
    # 匯出 CSV 報告按鈕
    csv_bytes = df_esg.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 下載企業 ESG Scope 3 減碳盤查報告 (CSV)",
        data=csv_bytes,
        file_name="esg_scope3_commute_reduction_report.csv",
        mime="text/csv"
    )

with tab4:
    st.subheader("🏛️ 市府 ✕ 內科企業 上任 100 天落地里程碑")
    st.markdown("""
    * **Day 1–30（數據盤點與儀表板上線）**：串接 TDX/VD 數據，啟動內科熱力儀表板；問卷盤查前 100 大企業考勤制度。
    * **Day 31–60（核心工時與示範企業）**：發布公版「10:00–16:00 核心工時」範本；招募首批 20% 標竿企業；開啟幹道動態綠廊 (ITS)。
    * **Day 61–90（大眾運輸與差別費率）**：開通 3 條捷運接駁直達快線專車；試辦公有停車場尖峰動態累進費率及 HOV 優惠。
    * **Day 91–100（成果發布與 ESG 標章）**：召開 100 天治堵成果記者會；頒發市府「ESG 綠色通勤認證標章」。
    """)