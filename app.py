import streamlit as st
import pandas as pd

# ── Load data ──────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    return pd.read_csv("data.csv")

df = load_data()

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Food Portion Visualizer", page_icon="🍓")
st.title("🍓 Food Portion Visualizer")
st.write("See exactly what your food looks like before you pour it.")

# ── Inputs ─────────────────────────────────────────────────────────────────────
food_options = df["food"].tolist()

col1, col2 = st.columns(2)

with col1:
    selected_food = st.selectbox("Choose a food", food_options)

with col2:
    grams = st.number_input("Amount in grams", min_value=1, max_value=2000, value=100, step=5)

# ── Calculation ────────────────────────────────────────────────────────────────
food_row = df[df["food"] == selected_food].iloc[0]

density        = food_row["density_g_per_cm3"]
packing        = food_row["packing_factor"]
food_color     = food_row["color"]
category       = food_row["category"]

volume_cm3     = (grams / density) / packing
volume_ml      = volume_cm3  # 1 cm³ = 1 ml, useful reference
volume_cups    = volume_cm3 / 236.6

# ── Bowl sizes (volume in cm³) ─────────────────────────────────────────────────
bowl_sizes = {
    "Small bowl (300ml)":  300,
    "Medium bowl (500ml)": 500,
    "Large bowl (750ml)":  750,
    "Dinner bowl (1L)":    1000,
}

st.divider()

bowl_choice = st.radio("Bowl size", list(bowl_sizes.keys()), horizontal=True)
bowl_volume = bowl_sizes[bowl_choice]

fill_percent = min((volume_cm3 / bowl_volume) * 100, 100)
overflowing  = volume_cm3 > bowl_volume

# ── Results ────────────────────────────────────────────────────────────────────
st.divider()

st.subheader(f"{grams}g of {selected_food}")

metric1, metric2, metric3 = st.columns(3)

with metric1:
    st.metric("Volume", f"{volume_ml:.0f} ml")

with metric2:
    st.metric("Approx. cups", f"{volume_cups:.2f}")

with metric3:
    if overflowing:
        st.metric("Bowl fill", "Overflows! 🚨")
    else:
        st.metric("Bowl fill", f"{fill_percent:.1f}%")

if overflowing:
    st.warning(f"⚠️ {grams}g of {selected_food} is more than your {bowl_choice} can hold. Try a larger bowl or reduce the amount.")

# ── Progress bar as simple visual placeholder ──────────────────────────────────
st.write("**Bowl fill level:**")
st.progress(int(fill_percent))

st.caption("Visual bowl illustration coming next — this is the live calculation.")

# ── Food info ──────────────────────────────────────────────────────────────────
with st.expander("How this is calculated"):
    st.write(f"""
    - **Density:** {density} g/cm³  
    - **Packing factor:** {packing} (accounts for air gaps between pieces)  
    - **Formula:** ({grams}g ÷ {density}) ÷ {packing} = **{volume_cm3:.1f} cm³**  
    - 1 cm³ = 1 ml, so this is **{volume_ml:.0f} ml** of space in your bowl
    """)