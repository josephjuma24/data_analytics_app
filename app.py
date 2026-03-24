import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import io

matplotlib.use("Agg")

st.set_page_config(page_title="Data Analyzer", page_icon="📊", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
    h1, h2, h3 { font-family: 'IBM Plex Mono', monospace; }
    .main { background-color: #0f1117; }
    .block-container { padding-top: 2rem; }
    .insight-box {
        background: linear-gradient(135deg, #1a1f2e 0%, #16213e 100%);
        border-left: 3px solid #00d4aa;
        border-radius: 4px;
        padding: 0.75rem 1rem;
        margin: 0.4rem 0;
        font-size: 0.9rem;
        color: #e0e0e0;
    }
    .metric-card {
        background: #1a1f2e;
        border: 1px solid #2a2f3e;
        border-radius: 6px;
        padding: 1rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

st.title("📊 Data Analyzer")
st.caption("Upload a CSV or XLSX file for instant automated analysis.")

uploaded = st.file_uploader("Drop your file here", type=["csv", "xlsx"])

if uploaded is None:
    st.info("Awaiting file upload — supports CSV and XLSX.")
    st.stop()

# ── Load ──────────────────────────────────────────────────────────────────────
@st.cache_data
def load(file):
    name = file.name.lower()
    if name.endswith(".xlsx"):
        return pd.read_excel(file, engine="openpyxl")
    return pd.read_csv(file)

try:
    df = load(uploaded)
except Exception as e:
    st.error(f"Could not read file: {e}")
    st.stop()

# ── Overview ──────────────────────────────────────────────────────────────────
st.subheader("01 · Overview")
c1, c2, c3, c4 = st.columns(4)
missing_pct = (df.isnull().sum().sum() / df.size * 100)
num_cols = df.select_dtypes(include="number").columns.tolist()
c1.metric("Rows", f"{df.shape[0]:,}")
c2.metric("Columns", df.shape[1])
c3.metric("Numeric cols", len(num_cols))
c4.metric("Missing values", f"{missing_pct:.1f}%")

with st.expander("Column types & missing values"):
    info = pd.DataFrame({
        "dtype": df.dtypes.astype(str),
        "missing": df.isnull().sum(),
        "missing_%": (df.isnull().mean() * 100).round(2),
        "unique": df.nunique(),
    })
    st.dataframe(info, use_container_width=True)

# ── Descriptive stats ─────────────────────────────────────────────────────────
if num_cols:
    st.subheader("02 · Descriptive Statistics")
    st.dataframe(df[num_cols].describe().T.style.format("{:.3g}"), use_container_width=True)

# ── Correlation heatmap ───────────────────────────────────────────────────────
if len(num_cols) >= 2:
    st.subheader("03 · Correlation Heatmap")
    corr = df[num_cols].corr()
    fig, ax = plt.subplots(figsize=(min(len(num_cols), 12), min(len(num_cols), 10)))
    fig.patch.set_facecolor("#0f1117")
    ax.set_facecolor("#0f1117")
    im = ax.imshow(corr.values, cmap="RdYlGn", vmin=-1, vmax=1, aspect="auto")
    ax.set_xticks(range(len(corr.columns)))
    ax.set_yticks(range(len(corr.columns)))
    ax.set_xticklabels(corr.columns, rotation=45, ha="right", color="#aaaaaa", fontsize=9)
    ax.set_yticklabels(corr.columns, color="#aaaaaa", fontsize=9)
    for i in range(len(corr)):
        for j in range(len(corr)):
            val = corr.values[i, j]
            ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                    fontsize=8, color="white" if abs(val) > 0.5 else "#cccccc")
    plt.colorbar(im, ax=ax)
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

# ── Auto insights ─────────────────────────────────────────────────────────────
st.subheader("04 · Auto Insights")
insights = []

# Missing values
high_missing = df.isnull().mean()
for col, pct in high_missing.items():
    if pct > 0.1:
        insights.append(f"⚠️  **{col}** has **{pct*100:.1f}%** missing values — consider imputation or removal.")

# Correlation pairs
if len(num_cols) >= 2:
    corr = df[num_cols].corr().abs()
    np.fill_diagonal(corr.values, 0)
    idx = np.unravel_index(corr.values.argmax(), corr.shape)
    r = df[num_cols].corr().values[idx]
    insights.append(
        f"🔗  Strongest correlation: **{num_cols[idx[0]]}** ↔ **{num_cols[idx[1]]}** "
        f"(r = {r:.2f}), suggesting a {'positive' if r > 0 else 'negative'} relationship."
    )

# Skewed columns
for col in num_cols[:8]:
    sk = df[col].dropna().skew()
    if abs(sk) > 1.5:
        direction = "right (positive)" if sk > 0 else "left (negative)"
        insights.append(f"📈  **{col}** is strongly skewed {direction} (skewness = {sk:.2f}).")

# High-cardinality categoricals
cat_cols = df.select_dtypes(include=["object", "category"]).columns
for col in cat_cols:
    card = df[col].nunique()
    if card / len(df) > 0.9:
        insights.append(f"🔑  **{col}** looks like an ID column ({card} unique values out of {len(df)} rows).")
    elif card <= 10:
        top = df[col].value_counts().index[0]
        top_pct = df[col].value_counts(normalize=True).iloc[0] * 100
        insights.append(f"🏷️  Most common value in **{col}**: **'{top}'** ({top_pct:.1f}% of rows).")

if not insights:
    insights.append("✅  No obvious data quality issues detected. Dataset looks clean!")

for ins in insights[:6]:
    st.markdown(f'<div class="insight-box">{ins}</div>', unsafe_allow_html=True)

# ── Interactive charts ────────────────────────────────────────────────────────
if num_cols:
    st.subheader("05 · Interactive Charts")
    tab1, tab2, tab3 = st.tabs(["Line", "Bar", "Scatter"])

    with tab1:
        col = st.selectbox("Y-axis (line)", num_cols, key="line_y")
        st.line_chart(df[col].dropna().reset_index(drop=True), height=300)

    with tab2:
        col = st.selectbox("Column (bar)", num_cols, key="bar_col")
        cat = [c for c in cat_cols if df[c].nunique() <= 30]
        if cat:
            grp = st.selectbox("Group by", cat, key="bar_grp")
            chart_data = df.groupby(grp)[col].mean().dropna()
        else:
            chart_data = df[col].dropna().head(50)
        st.bar_chart(chart_data, height=300)

    with tab3:
        if len(num_cols) >= 2:
            x_col = st.selectbox("X", num_cols, index=0, key="sc_x")
            y_col = st.selectbox("Y", num_cols, index=1, key="sc_y")
            scatter_df = df[[x_col, y_col]].dropna().sample(min(500, len(df)), random_state=42)
            st.scatter_chart(scatter_df, x=x_col, y=y_col, height=300)
        else:
            st.info("Need at least 2 numeric columns for scatter plot.")

# ── Raw data preview ──────────────────────────────────────────────────────────
with st.expander("Raw data preview (first 100 rows)"):
    st.dataframe(df.head(100), use_container_width=True)
