import streamlit as st
import pandas as pd

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
bowl_volume = bowl_sizes[bowl_choice]

# ── Calculation ────────────────────────────────────────────────────────────────
food_row       = df[df["food"] == selected_food].iloc[0]
density        = food_row["density_g_per_cm3"]
packing        = food_row["packing_factor"]
food_color     = food_row["color"]
category       = food_row["category"]

volume_cm3     = (grams / density) / packing
volume_ml      = volume_cm3
volume_cups    = volume_cm3 / 236.6
fill_percent   = min((volume_cm3 / bowl_volume) * 100, 100)
overflowing    = volume_cm3 > bowl_volume

# ── Bowl SVG visualization ─────────────────────────────────────────────────────
def draw_bowl(fill_pct, food_col, food_name, category):
    # Bowl dimensions
    bx      = 80       # left edge of bowl top
    by      = 40       # top of bowl rim
    bw      = 340      # width at top
    bh      = 200      # total bowl depth
    cx      = bx + bw / 2   # center x

    # Bowl narrows at the bottom — bottom width is 120px
    bottom_w = 120
    bottom_x = cx - bottom_w / 2

    # How high the food fills (from the bottom up)
    fill_ratio   = fill_pct / 100
    fill_height  = bh * fill_ratio
    fill_y_bottom = by + bh           # bottom of bowl interior
    fill_y_top    = fill_y_bottom - fill_height

    # The bowl is a trapezoid shape — at any height, calculate the width
    # At top (y=by): width = bw. At bottom (y=by+bh): width = bottom_w
    def bowl_width_at(y):
        t = (y - by) / bh   # 0 at top, 1 at bottom
        return bw - t * (bw - bottom_w)

    def bowl_left_at(y):
        w = bowl_width_at(y)
        return cx - w / 2

    # Food fill top width
    fill_top_w = bowl_width_at(fill_y_top)
    fill_top_x = cx - fill_top_w / 2

    # Darker shade for food texture detail
    def darken(hex_color, factor=0.75):
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2],16), int(hex_color[2:4],16), int(hex_color[4:6],16)
        r, g, b = int(r*factor), int(g*factor), int(b*factor)
        return f"#{r:02x}{g:02x}{b:02x}"

    dark_color = darken(food_col)

    # Draw texture dots for non-liquid foods
    dots = ""
    if category in ["berry", "nut", "fruit", "grain", "vegetable"] and fill_height > 20:
        import random
        random.seed(42)
        for _ in range(min(int(fill_height * 2.5), 80)):
            t    = random.uniform(0.05, 0.95)
            dot_y = fill_y_top + (fill_height * t) + random.uniform(-4, 4)
            dot_y = max(fill_y_top + 4, min(fill_y_bottom - 4, dot_y))
            max_x_range = bowl_width_at(dot_y) * 0.85
            dot_x = cx + random.uniform(-max_x_range/2, max_x_range/2)
            r_size = random.uniform(3, 7)
            opacity = random.uniform(0.4, 0.85)
            dots += f'<circle cx="{dot_x:.1f}" cy="{dot_y:.1f}" r="{r_size:.1f}" fill="{dark_color}" opacity="{opacity:.2f}"/>'

    # Overflow indicator
    overflow_svg = ""
    if fill_pct >= 100:
        overflow_svg = f'''
        <text x="{cx}" y="{by - 10}" text-anchor="middle"
              font-family="sans-serif" font-size="13" fill="#ff4444">
          ⚠ Overflows this bowl
        </text>'''

    svg = f'''
    <svg width="500" height="320" xmlns="http://www.w3.org/2000/svg">

      <!-- Background -->
      <rect width="500" height="320" fill="transparent"/>

      <!-- Bowl shadow -->
      <ellipse cx="{cx}" cy="{by + bh + 12}" rx="{bottom_w/2 + 10}" ry="8"
               fill="#00000022"/>

      <!-- Food fill (trapezoid shape matching bowl) -->
      {"" if fill_height < 2 else f'''
      <polygon points="
        {fill_top_x:.1f},{fill_y_top:.1f}
        {fill_top_x + fill_top_w:.1f},{fill_y_top:.1f}
        {bottom_x + bottom_w:.1f},{fill_y_bottom:.1f}
        {bottom_x:.1f},{fill_y_bottom:.1f}"
        fill="{food_col}" opacity="0.92"/>
      '''}

      <!-- Texture dots -->
      {dots}

      <!-- Bowl outline (trapezoid) -->
      <polygon points="
        {bx:.1f},{by:.1f}
        {bx + bw:.1f},{by:.1f}
        {bottom_x + bottom_w:.1f},{by + bh:.1f}
        {bottom_x:.1f},{by + bh:.1f}"
        fill="none" stroke="#888888" stroke-width="2.5" stroke-linejoin="round"/>

      <!-- Bowl rim highlight -->
      <line x1="{bx}" y1="{by}" x2="{bx + bw}" y2="{by}"
            stroke="#aaaaaa" stroke-width="4" stroke-linecap="round"/>

      <!-- Bowl base -->
      <line x1="{bottom_x}" y1="{by + bh}" x2="{bottom_x + bottom_w}" y2="{by + bh}"
            stroke="#888888" stroke-width="3" stroke-linecap="round"/>

      <!-- Fill line indicator -->
      {"" if fill_height < 8 else f'''
      <line x1="{fill_top_x:.1f}" y1="{fill_y_top:.1f}"
            x2="{fill_top_x + fill_top_w:.1f}" y2="{fill_y_top:.1f}"
            stroke="{dark_color}" stroke-width="1.5" stroke-dasharray="4,3" opacity="0.6"/>
      '''}

      <!-- Food label inside bowl -->
      {"" if fill_height < 30 else f'''
      <text x="{cx}" y="{fill_y_top + fill_height/2 + 5:.1f}"
            text-anchor="middle" font-family="sans-serif"
            font-size="13" fill="white" font-weight="600"
            style="text-shadow: 0 1px 3px rgba(0,0,0,0.8)">
        {food_name}
      </text>
      '''}

      <!-- Fill % label on right side -->
      <text x="{bx + bw + 14}" y="{fill_y_top + 5:.1f}"
            font-family="sans-serif" font-size="12" fill="#aaaaaa">
        {fill_pct:.0f}%
      </text>

      {overflow_svg}

    </svg>
    '''
    return svg

# ── Display ────────────────────────────────────────────────────────────────────
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
    st.warning(f"⚠️ {grams}g of {selected_food} exceeds your {bowl_choice}. Try a larger bowl.")

# Draw the bowl
bowl_svg = draw_bowl(fill_percent, food_color, selected_food, category)
st.write(bowl_svg, unsafe_allow_html=True)

# ── Food info expander ─────────────────────────────────────────────────────────
with st.expander("How this is calculated"):
    st.write(f"""
    - **Density:** {density} g/cm³  
    - **Packing factor:** {packing} (accounts for air gaps between pieces)  
    - **Formula:** ({grams}g ÷ {density}) ÷ {packing} = **{volume_cm3:.1f} cm³**  
    - 1 cm³ = 1 ml, so this is **{volume_ml:.0f} ml** of space in your bowl
    """)

st.caption("⚠️ Visual is approximate. Actual appearance may vary by food shape and how it's arranged.")