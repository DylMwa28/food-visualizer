import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import random

@st.cache_data
def load_data():
    return pd.read_csv("data.csv")

df = load_data()

st.set_page_config(page_title="Food Portion Visualizer", page_icon="🍓", layout="centered")
st.title("🍓 Food Portion Visualizer")
st.write("See exactly what your food looks like before you pour it.")

food_options = df["food"].tolist()
col1, col2 = st.columns(2)
with col1:
    selected_food = st.selectbox("Choose a food", food_options)
with col2:
    grams = st.number_input("Amount in grams", min_value=1, max_value=2000, value=100, step=5)

bowl_sizes = {
    "Small bowl (300ml)":  300,
    "Medium bowl (500ml)": 500,
    "Large bowl (750ml)":  750,
    "Dinner bowl (1L)":    1000,
}
st.divider()
bowl_choice = st.radio("Bowl size", list(bowl_sizes.keys()), horizontal=True)
bowl_volume  = bowl_sizes[bowl_choice]

food_row     = df[df["food"] == selected_food].iloc[0]
density      = food_row["density_g_per_cm3"]
packing      = food_row["packing_factor"]
food_color   = food_row["color"]
category     = food_row["category"]

volume_cm3   = (grams / density) / packing
volume_ml    = volume_cm3
volume_cups  = volume_cm3 / 236.6
fill_percent = min((volume_cm3 / bowl_volume) * 100, 100)
overflowing  = volume_cm3 > bowl_volume

def draw_bowl(fill_pct, food_col, food_name, cat):
    random.seed(42)

    def darken(hex_color, factor=0.72):
        h = hex_color.lstrip('#')
        r,g,b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
        return f"#{int(r*factor):02x}{int(g*factor):02x}{int(b*factor):02x}"

    dark_col = darken(food_col)

    # Bowl is drawn using an HTML/CSS approach inside the SVG foreignObject
    # so we get a real rounded bowl shape
    fill_h_pct = fill_pct  # percentage height of food

    # Generate dots as SVG circles positioned within a 300x180 area
    dots_svg = ""
    if cat in ["berry","nut","fruit","grain","vegetable"] and fill_pct > 8:
        num_dots = min(int(fill_pct * 1.2), 80)
        for _ in range(num_dots):
            # Place dots in lower portion matching fill
            dx = random.uniform(8, 292)
            # dots go from bottom up to fill level
            dy_min = 180 - (180 * fill_pct / 100) + 6
            dy = random.uniform(dy_min, 174)
            r  = random.uniform(3, 7)
            op = random.uniform(0.3, 0.75)
            dots_svg += f'<circle cx="{dx:.1f}" cy="{dy:.1f}" r="{r:.1f}" fill="{dark_col}" opacity="{op:.2f}"/>'

    overflow_text = "⚠ Overflows this bowl" if fill_pct >= 100 else ""

    html = f"""
    <div style="display:flex; flex-direction:column; align-items:center; padding:20px 0; font-family:sans-serif;">

      {"<p style='color:#ff5555; font-size:13px; margin:0 0 8px;'>⚠ Overflows this bowl</p>" if fill_pct >= 100 else ""}

      <div style="position:relative; width:320px; height:200px;">

        <!-- Bowl shell using CSS clip and border-radius -->
        <div style="
          position:absolute;
          bottom:0; left:0; right:0;
          width:320px;
          height:190px;
          border: 3px solid #888;
          border-top: none;
          border-radius: 0 0 160px 160px / 0 0 80px 80px;
          overflow:hidden;
          box-sizing:border-box;
          background: transparent;
        ">
          <!-- Food fill inside bowl -->
          <div style="
            position:absolute;
            bottom:0; left:0; right:0;
            height:{fill_pct:.1f}%;
            background:{food_col};
            opacity:0.92;
            display:flex;
            align-items:center;
            justify-content:center;
            overflow:hidden;
          ">
            <!-- Dots as inline SVG -->
            <svg style="position:absolute;top:0;left:0;width:100%;height:100%"
                 xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none"
                 viewBox="0 0 300 180">
              {dots_svg}
            </svg>
            {"<span style='color:white;font-weight:600;font-size:13px;position:relative;z-index:1;text-shadow:0 1px 3px rgba(0,0,0,0.6)'>" + food_name + "</span>" if fill_pct > 15 else ""}
          </div>
        </div>

        <!-- Percent label -->
        <div style="
          position:absolute;
          right:-44px;
          bottom:{fill_pct * 1.7:.0f}px;
          font-size:12px;
          color:#aaa;
        ">{fill_pct:.0f}%</div>

      </div>

      <!-- Rim drawn separately on top so it looks clean -->
      <div style="
        position:absolute;
        top:10px; left:0; right:0;
        width:320px;
        height:6px;
        background:#cccccc;
        border-radius:3px;
      "></div>

      <!-- Shadow -->
      <div style="
        width:200px; height:10px;
        background:radial-gradient(ellipse, rgba(0,0,0,0.35) 0%, transparent 70%);
        margin-top:4px;
      "></div>

    </div>
    """
    return html

st.divider()
st.subheader(f"{grams}g of {selected_food}")

m1, m2, m3 = st.columns(3)
with m1:
    st.metric("Volume", f"{volume_ml:.0f} ml")
with m2:
    st.metric("Approx. cups", f"{volume_cups:.2f}")
with m3:
    if overflowing:
        st.metric("Bowl fill", "Overflows! 🚨")
    else:
        st.metric("Bowl fill", f"{fill_percent:.1f}%")

if overflowing:
    st.warning(f"⚠️ {grams}g of {selected_food} exceeds your {bowl_choice}. Try a larger bowl.")

bowl_html = draw_bowl(fill_percent, food_color, selected_food, category)
components.html(bowl_html, height=280)

with st.expander("How this is calculated"):
    st.write(f"""
    - **Density:** {density} g/cm³  
    - **Packing factor:** {packing} (accounts for air gaps between pieces)  
    - **Formula:** ({grams}g ÷ {density}) ÷ {packing} = **{volume_cm3:.1f} cm³**  
    - 1 cm³ = 1 ml, so this is **{volume_ml:.0f} ml** of space in your bowl
    """)

st.caption("⚠️ Visual is approximate. Actual appearance may vary by food shape and how it's arranged.")