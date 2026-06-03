import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

# ── Load data ──────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    return pd.read_csv("data.csv")

df = load_data()

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Food Portion Visualizer", page_icon="🍓", layout="centered")
st.title("🍓 Food Portion Visualizer")
st.write("See exactly what your food looks like before you pour it.")

# ── Inputs ─────────────────────────────────────────────────────────────────────
food_options = df["food"].tolist()
col1, col2 = st.columns(2)
with col1:
    selected_food = st.selectbox("Choose a food", food_options)
with col2:
    grams = st.number_input("Amount in grams", min_value=1, max_value=2000, value=100, step=5)

# ── Bowl size selector ─────────────────────────────────────────────────────────
bowl_sizes = {
    "Small bowl (300ml)":  300,
    "Medium bowl (500ml)": 500,
    "Large bowl (750ml)":  750,
    "Dinner bowl (1L)":    1000,
}
st.divider()
bowl_choice = st.radio("Bowl size", list(bowl_sizes.keys()), horizontal=True)
bowl_volume  = bowl_sizes[bowl_choice]

# ── Calculation ────────────────────────────────────────────────────────────────
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

# ── Bowl SVG ───────────────────────────────────────────────────────────────────
def draw_bowl(fill_pct, food_col, food_name, category):
    import random
    random.seed(42)

    # Canvas
    W, H = 500, 300

    # Bowl shape — wide at top, narrower flat base
    top_y    = 40
    base_y   = 240
    top_left = 60
    top_right= 440
    base_left= 160
    base_right=340
    cx       = W / 2

    bowl_h   = base_y - top_y        # 200px total interior height
    fill_h   = bowl_h * (fill_pct / 100)
    fill_y   = base_y - fill_h       # top of the food fill

    # At any y between top_y and base_y, interpolate the left/right edges
    def left_edge(y):
        t = (y - top_y) / bowl_h
        return top_left + t * (base_left - top_left)

    def right_edge(y):
        t = (y - top_y) / bowl_h
        return top_right + t * (base_right - top_right)

    fill_left  = left_edge(fill_y)
    fill_right = right_edge(fill_y)

    def darken(hex_color, factor=0.72):
        h = hex_color.lstrip('#')
        r,g,b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
        return f"#{int(r*factor):02x}{int(g*factor):02x}{int(b*factor):02x}"

    dark_col = darken(food_col)

    # Texture dots scattered inside the food fill region
    dots = ""
    if category in ["berry","nut","fruit","grain","vegetable"] and fill_h > 15:
        for _ in range(min(int(fill_h * 2.2), 90)):
            dy     = random.uniform(fill_y + 4, base_y - 4)
            lx     = left_edge(dy) + 6
            rx     = right_edge(dy) - 6
            if rx <= lx:
                continue
            dx     = random.uniform(lx, rx)
            radius = random.uniform(3, 7)
            op     = random.uniform(0.35, 0.8)
            dots  += f'<circle cx="{dx:.1f}" cy="{dy:.1f}" r="{radius:.1f}" fill="{dark_col}" opacity="{op:.2f}"/>'

    # Food fill polygon
    food_poly = ""
    if fill_h > 2:
        food_poly = f'''
        <polygon points="
          {fill_left:.1f},{fill_y:.1f}
          {fill_right:.1f},{fill_y:.1f}
          {base_right},{base_y}
          {base_left},{base_y}"
          fill="{food_col}" opacity="0.93"/>'''

    # Dashed fill line at top of food
    fill_line = ""
    if fill_h > 8:
        fill_line = f'<line x1="{fill_left:.1f}" y1="{fill_y:.1f}" x2="{fill_right:.1f}" y2="{fill_y:.1f}" stroke="{dark_col}" stroke-width="1.5" stroke-dasharray="5,3" opacity="0.55"/>'

    # Label inside food if enough room
    label = ""
    label_y = fill_y + fill_h / 2 + 5
    if fill_h > 28:
        label = f'<text x="{cx}" y="{label_y:.1f}" text-anchor="middle" font-family="sans-serif" font-size="13" font-weight="600" fill="white" opacity="0.9">{food_name}</text>'

    # Percent label to the right
    pct_label = f'<text x="{fill_right + 10:.1f}" y="{fill_y + 4:.1f}" font-family="sans-serif" font-size="12" fill="#aaaaaa">{fill_pct:.0f}%</text>'

    # Overflow warning
    overflow_txt = ""
    if fill_pct >= 100:
        overflow_txt = f'<text x="{cx}" y="28" text-anchor="middle" font-family="sans-serif" font-size="13" fill="#ff5555">⚠ Overflows this bowl</text>'

    # Bowl outline — trapezoid wide-top correct orientation
    bowl_outline = f'''
      <polygon points="
        {top_left},{top_y}
        {top_right},{top_y}
        {base_right},{base_y}
        {base_left},{base_y}"
        fill="none" stroke="#999999" stroke-width="2.5" stroke-linejoin="round"/>'''

    # Rim highlight
    rim = f'<line x1="{top_left}" y1="{top_y}" x2="{top_right}" y2="{top_y}" stroke="#cccccc" stroke-width="4" stroke-linecap="round"/>'

    # Base line
    base = f'<line x1="{base_left}" y1="{base_y}" x2="{base_right}" y2="{base_y}" stroke="#999999" stroke-width="3" stroke-linecap="round"/>'

    # Inner bowl sheen (subtle highlight on left wall)
    sheen = f'<line x1="{top_left + 18}" y1="{top_y + 10}" x2="{base_left + 8}" y2="{base_y - 5}" stroke="white" stroke-width="1.5" opacity="0.12" stroke-linecap="round"/>'

    # Shadow under bowl
    shadow = f'<ellipse cx="{cx}" cy="{base_y + 14}" rx="95" ry="7" fill="#00000033"/>'

    svg = f'''<svg width="{W}" height="{H}" xmlns="http://www.w3.org/2000/svg">
      <rect width="{W}" height="{H}" fill="transparent"/>
      {shadow}
      {food_poly}
      {dots}
      {fill_line}
      {label}
      {bowl_outline}
      {rim}
      {base}
      {sheen}
      {pct_label}
      {overflow_txt}
    </svg>'''

    return svg

# ── Display ────────────────────────────────────────────────────────────────────
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

bowl_svg = draw_bowl(fill_percent, food_color, selected_food, category)
components.html(bowl_svg, height=300)

with st.expander("How this is calculated"):
    st.write(f"""
    - **Density:** {density} g/cm³  
    - **Packing factor:** {packing} (accounts for air gaps between pieces)  
    - **Formula:** ({grams}g ÷ {density}) ÷ {packing} = **{volume_cm3:.1f} cm³**  
    - 1 cm³ = 1 ml, so this is **{volume_ml:.0f} ml** of space in your bowl
    """)

st.caption("⚠️ Visual is approximate. Actual appearance may vary by food shape and how it's arranged.")