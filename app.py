import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ==============================================================================
# 1. PAGE CONFIGURATION & CUSTOM CSS (DARK INDUSTRIAL THEME)
# ==============================================================================
st.set_page_config(
    page_title="Industrial IoT Monitor (Ver50.2) TAC SIAM CORP LTD.",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="collapsed"
)

SPREADSHEET_ID = "15AUScYWn0LNjaBD11wCdZb9pQFMQuDVOn--_pJVoXEQ"
SHEET_NAME = "Sheet1"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid=0"
GVIZ_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

STANDARD_COLUMNS = [
    "Timestamp", "Count A", "Count B", "Count C", "Current",
    "Stroke Threshold", "C_Run", "Voltage", "PF", "Power",
    "KWH 220", "KWH 380", "Time High", "Time Low", "Machine Status",
    "Calc D20", "T2", "T3", "T4", "T5",
    "Manual Defect", "Manual Pcs/Min", "Manual Counter",
    "Calc Avail", "Calc Perf", "Calc Qual", "Calc OEE"
]

# ==============================================================================
# 2. DATA LOADING (DIRECT DATETIME ROW DETECTION - ROW 4 = LATEST / MAX)
# ==============================================================================
@st.cache_data(ttl=15)
def load_sheet_data():
    raw_df = None
    for url in [CSV_URL, GVIZ_CSV_URL]:
        try:
            temp_df = pd.read_csv(url, header=None, dtype=str)
            if temp_df is not None and not temp_df.empty:
                raw_df = temp_df
                break
        except Exception:
            continue

    if raw_df is None or raw_df.empty:
        raise ValueError("ไม่สามารถโหลดข้อมูล CSV จาก Google Sheets ได้ กรุณาตรวจสอบสิทธิ์การแชร์ไฟล์")

    # Find the very first row where column 0 (Timestamp) is a valid date/time (Row 4 in Sheet1)
    data_start_idx = None
    for i in range(min(20, len(raw_df))):
        val = str(raw_df.iloc[i, 0]).strip()
        if not val or val.lower() == "nan":
            continue
        parsed = pd.to_datetime(val, format="%m/%d/%Y %H:%M:%S", errors="coerce")
        if pd.isna(parsed):
            parsed = pd.to_datetime(val, errors="coerce")
        if pd.notna(parsed):
            data_start_idx = i
            break

    if data_start_idx is None:
        raise ValueError("ไม่พบข้อมูลวันที่/เวลาในคอลัมน์ A ของ Sheet1")

    df = raw_df.iloc[data_start_idx:].copy()
    num_cols_present = min(len(df.columns), len(STANDARD_COLUMNS))
    df = df.iloc[:, :num_cols_present]
    df.columns = STANDARD_COLUMNS[:num_cols_present]
    df = df.reset_index(drop=True)

    # Remove Count B and T2-T5 columns per specification
    cols_to_drop = [c for c in ["Count B", "T2", "T3", "T4", "T5"] if c in df.columns]
    df = df.drop(columns=cols_to_drop)

    # Drop empty timestamp rows
    df = df.dropna(subset=["Timestamp"]).copy()

    # Parse Timestamp (mm/dd/yyyy HH:MM:SS format in Google Sheets)
    df["Parsed_DT"] = pd.to_datetime(df["Timestamp"].str.strip(), format="%m/%d/%Y %H:%M:%S", errors="coerce")
    mask_na = df["Parsed_DT"].isna()
    if mask_na.any():
        df.loc[mask_na, "Parsed_DT"] = pd.to_datetime(df.loc[mask_na, "Timestamp"].str.strip(), errors="coerce")

    df = df.dropna(subset=["Parsed_DT"]).copy()
    df["Date_Only"] = df["Parsed_DT"].dt.date

    # Convert numeric columns
    num_cols = [
        "Count A", "Count C", "Current", "Stroke Threshold", "C_Run",
        "Voltage", "PF", "Power", "KWH 220", "KWH 380",
        "Time High", "Time Low", "Calc D20",
        "Manual Defect", "Manual Pcs/Min", "Manual Counter",
        "Calc Avail", "Calc Perf", "Calc Qual", "Calc OEE"
    ]
    for col in num_cols:
        if col in df.columns:
            cleaned = df[col].astype(str).str.replace(",", "", regex=False).str.strip()
            df[col] = pd.to_numeric(cleaned, errors="coerce").fillna(0)

    return df

# ==============================================================================
# 3. GAUGE CHART HELPER (OEE, AVAILABILITY, PERFORMANCE, QUALITY)
# ==============================================================================
def make_gauge(title, value):
    val = max(0.0, min(100.0, float(value)))
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=val,
        number={"suffix": "%", "font": {"size": 24, "color": "#FFFFFF", "family": "sans-serif"}},
        title={"text": title, "font": {"size": 15, "color": "#E2E8F0"}},
        gauge={
            "axis": {
                "range": [0, 100],
                "tickvals": [0, 40, 65, 85, 100],
                "ticktext": ["0%", "40%", "65%", "85%", "100%"],
                "tickfont": {"size": 10, "color": "#94A3B8"}
            },
            "bar": {"color": "rgba(255,255,255,0.85)", "thickness": 0.18},
            "bgcolor": "#1E293B",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 40], "color": "#EF4444"},
                {"range": [40, 65], "color": "#F97316"},
                {"range": [65, 85], "color": "#EAB308"},
                {"range": [85, 100], "color": "#22C55E"}
            ],
        }
    ))
    fig.update_layout(
        height=175,
        margin=dict(l=18, r=18, t=38, b=10),
        paper_bgcolor="#161B26",
        font={"color": "#FFFFFF"}
    )
    return fig

# ==============================================================================
# 4. AREA CHART HELPER (COUNT A & CURRENT)
# ==============================================================================
def make_area_chart(x_dt, y_val, line_color, fill_rgba, y_unit=""):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_dt,
        y=y_val,
        mode="lines",
        line=dict(color=line_color, width=2.5),
        fill="tozeroy",
        fillcolor=fill_rgba,
        hovertemplate="%{x|%H:%M:%S}<br><b>%{y:,.2f}</b> " + y_unit + "<extra></extra>"
    ))
    fig.update_layout(
        height=185,
        margin=dict(l=10, r=10, t=10, b=25),
        paper_bgcolor="#161B26",
        plot_bgcolor="#161B26",
        xaxis=dict(
            showgrid=False,
            tickformat="%H:%M:%S",
            tickfont=dict(size=10, color="#94A3B8"),
            nticks=5
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(148,163,184,0.12)",
            tickfont=dict(size=10, color="#94A3B8"),
            zeroline=False
        ),
        showlegend=False
    )
    return fig

# ==============================================================================
# 5. MAIN DASHBOARD UI
# ==============================================================================
try:
    df = load_sheet_data()
except Exception as e:
    st.error(f"ไม่สามารถดึงข้อมูลจาก Google Sheets ได้: {e}")
    st.stop()

if df.empty:
    st.warning("ไม่พบข้อมูลใน Sheet1")
    st.stop()

# Index 0 corresponds to Row 4 in Sheet1 (Latest / MAX record)
latest_row4 = df.iloc[0]
latest_date = latest_row4["Date_Only"]

# --- STYLING INJECTION (FIX TOP BAR OVERLAP & HIGHLIGHT CONTROLS) ---
st.markdown(
    """
    <style>
        /* Hide Streamlit default white top header bar that overlaps controls */
        header[data-testid="stHeader"] {
            background-color: #0E1117 !important;
            height: 2.2rem !important;
        }
        div[data-testid="stToolbar"] {
            top: 0.2rem !important;
            right: 0.5rem !important;
        }
        .stApp {
            background-color: #0E1117;
            color: #F8FAFC;
        }
        /* Style radio buttons & date input labels so they are crisp and clearly visible */
        div[data-testid="stRadio"] > label,
        div[data-testid="stDateInput"] > label {
            color: #F8FAFC !important;
            font-size: 14px !important;
            font-weight: 700 !important;
            margin-bottom: 4px !important;
        }
        div[data-testid="stRadio"] div[role="radiogroup"] {
            background-color: #161B26;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 6px 12px;
        }
        div[data-testid="stRadio"] div[role="radiogroup"] label p {
            color: #F8FAFC !important;
            font-weight: 600 !important;
            font-size: 14px !important;
        }
        div[data-testid="stDateInput"] input {
            background-color: #1E293B !important;
            color: #FFFFFF !important;
            border: 1px solid #38BDF8 !important;
            border-radius: 8px !important;
            font-weight: 700 !important;
            font-size: 15px !important;
        }
        .kpi-card {
            background-color: #161B26;
            border: 1px solid #262F40;
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 8px;
        }
        .kpi-label {
            font-size: 12px;
            color: #94A3B8;
            margin-bottom: 4px;
        }
        .kpi-value {
            font-size: 22px;
            font-weight: 700;
            color: #FFFFFF;
        }
        .count-a-hero-card {
            background: linear-gradient(135deg, #162033 0%, #1E293B 100%);
            border: 2px solid #38BDF8;
            border-radius: 10px;
            padding: 12px 16px;
            box-shadow: 0 0 15px rgba(56, 189, 248, 0.2);
        }
        .count-a-hero-label {
            font-size: 14px;
            font-weight: 700;
            color: #7DD3FC;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .count-a-hero-value {
            font-size: 38px;
            font-weight: 900;
            color: #38BDF8;
            line-height: 1.15;
        }
        .chart-header-box {
            background-color: #161B26;
            border: 1px solid #262F40;
            border-bottom: none;
            border-radius: 8px 8px 0 0;
            padding: 12px 16px 4px 16px;
        }
        .max-badge {
            border: 1px solid #F59E0B;
            color: #FBBF24;
            background-color: rgba(245, 158, 11, 0.1);
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 700;
            float: right;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# --- TOP HEADER BAR ---
col_title, col_mode, col_date = st.columns([4.6, 2.6, 2.3])

with col_title:
    st.markdown(
        """
        <div style="padding-top: 14px;">
            <span style="font-size: 23px; font-weight: 800; color: #F8FAFC; letter-spacing: 0.3px;">
                🏭 Industrial IoT Monitor (Ver50.2) TAC SIAM CORP LTD.
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

with col_mode:
    view_mode = st.radio(
        "รูปแบบหน้าจอ",
        ["ปกติ (Normal)", "เต็มจอ (Present A4)"],
        horizontal=True
    )

with col_date:
    available_dates = sorted(df["Date_Only"].unique(), reverse=True)
    selected_date = st.date_input(
        "📅 คลิก เลือกวันที่",
        value=latest_date,
        min_value=min(available_dates),
        max_value=max(available_dates)
    )

# Adjust padding dynamically based on selected view mode
top_pad = "2.2rem"
side_pad = "1.0rem" if view_mode == "เต็มจอ (Present A4)" else "2.0rem"
st.markdown(
    f"""
    <style>
        .block-container {{
            padding-top: {top_pad} !important;
            padding-left: {side_pad} !important;
            padding-right: {side_pad} !important;
            padding-bottom: 1rem !important;
            max-width: 100% !important;
        }}
    </style>
    """,
    unsafe_allow_html=True
)

day_df = df[df["Date_Only"] == selected_date].copy()
if day_df.empty:
    st.info(f"ไม่มีข้อมูลบันทึกในวันที่ {selected_date.strftime('%m/%d/%Y')}")
    st.stop()

current_rec = day_df.iloc[0]
chart_df = day_df.sort_values("Parsed_DT", ascending=True)

# --- MACHINE STATUS BANNER ---
status_str = str(current_rec["Machine Status"]).strip().upper()
ts_str = current_rec["Parsed_DT"].strftime("%m/%d/%Y %H:%M:%S")

if status_str in ["RUN", "STROKE"]:
    dot_color = "#22C55E"
    banner_bg = "#F1F5F9"
    text_color = "#0F172A"
elif status_str == "STANDBY":
    dot_color = "#EAB308"
    banner_bg = "#FEF9C3"
    text_color = "#713F12"
else:
    dot_color = "#EF4444"
    banner_bg = "#FEE2E2"
    text_color = "#7F1D1D"

st.markdown(
    f"""
    <div style="background-color: {banner_bg}; color: {text_color}; padding: 12px 20px; border-radius: 8px;
                margin: 8px 0 14px 0; display: flex; justify-content: space-between; align-items: center;
                font-weight: 800; font-size: 16px; box-shadow: 0 2px 6px rgba(0,0,0,0.3);">
        <div>
            <span style="display:inline-block; width:12px; height:12px; border-radius:50%;
                         background-color:{dot_color}; margin-right:10px;"></span>
            MACHINE STATUS: {status_str}
        </div>
        <div style="font-size: 13px; font-weight: 600; opacity: 0.85;">
            อัปเดตล่าสุด (Row 4): {ts_str}
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# --- ROW 1: OEE KPI CARDS ---
c1, c2, c3, c4 = st.columns(4)
oee_val = float(current_rec["Calc OEE"])
avail_val = float(current_rec["Calc Avail"])
perf_val = float(current_rec["Calc Perf"])
qual_val = float(current_rec["Calc Qual"])

with c1:
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">OEE</div><div class="kpi-value">{oee_val:.1f}%</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">Availability (A)</div><div class="kpi-value">{avail_val:.1f}%</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">Performance (P)</div><div class="kpi-value">{perf_val:.1f}%</div></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">Quality (Q)</div><div class="kpi-value">{qual_val:.1f}%</div></div>', unsafe_allow_html=True)

# --- ROW 2: OEE GAUGE CHARTS ---
g1, g2, g3, g4 = st.columns(4)
with g1:
    st.plotly_chart(make_gauge("OEE", oee_val), use_container_width=True, config={"displayModeBar": False})
with g2:
    st.plotly_chart(make_gauge("Availability", avail_val), use_container_width=True, config={"displayModeBar": False})
with g3:
    st.plotly_chart(make_gauge("Performance", perf_val), use_container_width=True, config={"displayModeBar": False})
with g4:
    st.plotly_chart(make_gauge("Quality", qual_val), use_container_width=True, config={"displayModeBar": False})

# --- ROW 3: TWO AREA CHARTS ---
ch1, ch2 = st.columns(2)

count_a_latest = int(current_rec["Count A"])
count_a_max = int(day_df["Count A"].max())
curr_latest = float(current_rec["Current"])
curr_max = float(day_df["Current"].max())

with ch1:
    st.markdown(
        f"""
        <div class="chart-header-box">
            <span class="max-badge">MAX: {count_a_max:,} pcs</span>
            <div style="font-size: 15px; font-weight: 700; color: #F8FAFC;">Count A Progression</div>
            <div style="font-size: 12px; color: #94A3B8;">ยอดการนับชิ้นงานจากเริ่มต้นจนถึงล่าสุด (+{count_a_latest:,} pcs)</div>
            <div style="font-size: 32px; font-weight: 900; color: #38BDF8; margin-top: 2px;">
                {count_a_latest:,} <span style="font-size: 14px; font-weight: 600; color: #94A3B8;">pcs</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.plotly_chart(
        make_area_chart(chart_df["Parsed_DT"], chart_df["Count A"], "#38BDF8", "rgba(56, 189, 248, 0.22)", "pcs"),
        use_container_width=True,
        config={"displayModeBar": False}
    )

with ch2:
    st.markdown(
        f"""
        <div class="chart-header-box">
            <span class="max-badge">MAX: {curr_max:.2f} A</span>
            <div style="font-size: 15px; font-weight: 700; color: #F8FAFC;">Current Machine On/Off</div>
            <div style="font-size: 12px; color: #94A3B8;">ระดับกระแสไฟฟ้าขณะเปิด-ปิดเครื่อง (C_Run: {current_rec['C_Run']:.2f} A)</div>
            <div style="font-size: 32px; font-weight: 900; color: #22C55E; margin-top: 2px;">
                {curr_latest:.2f} <span style="font-size: 14px; font-weight: 600; color: #94A3B8;">A</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.plotly_chart(
        make_area_chart(chart_df["Parsed_DT"], chart_df["Current"], "#22C55E", "rgba(34, 197, 94, 0.22)", "A"),
        use_container_width=True,
        config={"displayModeBar": False}
    )

# --- ROW 4: BOTTOM SUMMARY CARDS ---
bot_left, bot_right = st.columns([1.15, 1.35])

with bot_left:
    st.markdown('<div style="font-size: 14px; font-weight: 700; color: #E2E8F0; margin: 6px 0;">📦 การผลิต (Production)</div>', unsafe_allow_html=True)
    p1, p2, p3, p4 = st.columns([1.45, 0.85, 0.85, 0.95])
    with p1:
        st.markdown(
            f"""
            <div class="count-a-hero-card">
                <div class="count-a-hero-label">Count A (Pcs)</div>
                <div class="count-a-hero-value">{count_a_latest:,}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with p2:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Stroke (C)</div><div class="kpi-value">{int(current_rec["Count C"]):,}</div></div>', unsafe_allow_html=True)
    with p3:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Defects</div><div class="kpi-value">{int(current_rec["Manual Defect"]):,}</div></div>', unsafe_allow_html=True)
    with p4:
        inv_hz = float(current_rec["Calc D20"]) / 100.0
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Inverter Hz</div><div class="kpi-value">{inv_hz:.2f}</div></div>', unsafe_allow_html=True)

with bot_right:
    st.markdown('<div style="font-size: 14px; font-weight: 700; color: #E2E8F0; margin: 6px 0;">⚡ ระบบไฟฟ้า (Electrical & Energy)</div>', unsafe_allow_html=True)
    e1, e2, e3, e4, e5 = st.columns(5)
    with e1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Volt</div><div class="kpi-value">{float(current_rec["Voltage"]):.1f}V</div></div>', unsafe_allow_html=True)
    with e2:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Amp</div><div class="kpi-value">{curr_latest:.2f}A</div></div>', unsafe_allow_html=True)
    with e3:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Power</div><div class="kpi-value">{float(current_rec["Power"]):.2f}</div></div>', unsafe_allow_html=True)
    with e4:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">PF</div><div class="kpi-value">{float(current_rec["PF"]):.2f}</div></div>', unsafe_allow_html=True)
    with e5:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">kWh 380V</div><div class="kpi-value">{float(current_rec["KWH 380"]):.1f}</div></div>', unsafe_allow_html=True)
