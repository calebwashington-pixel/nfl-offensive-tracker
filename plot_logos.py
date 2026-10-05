import requests
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

df = pd.read_csv("offense_season.csv")

# ESPN uses different codes for two teams
ESPN_CODES = {"LA": "lar", "WAS": "wsh"}

def get_logo(team):
    code = ESPN_CODES.get(team, team.lower())
    url = f"https://a.espncdn.com/i/teamlogos/nfl/500/{code}.png"
    r = requests.get(url, timeout=10)
    return plt.imread(BytesIO(r.content), format="png")

fig, ax = plt.subplots(figsize=(15, 11))
ax.scatter(df["pass_epa"], df["rush_epa"], alpha=0)  # invisible, sets the axes

for _, row in df.iterrows():
    x, y = row["pass_epa"], row["rush_epa"]
    try:
        logo = get_logo(row["team"])
        zoom = 30 / max(logo.shape[0], logo.shape[1])
        box = OffsetImage(logo, zoom=zoom)
        ax.add_artist(AnnotationBbox(box, (x, y), frameon=False))
    except Exception:
        ax.text(x, y, row["team"], ha="center")  # fallback: team name

ax.axhline(0, color="gray", linewidth=0.8)
ax.axvline(0, color="gray", linewidth=0.8)
ax.margins(0.08)
ax.set_xlabel("Pass EPA")
ax.set_ylabel("Rush EPA")
ax.set_title("NFL Offenses 2026: Pass vs Rush Efficiency")

plt.savefig("offense_logos.png", dpi=150, bbox_inches="tight")
plt.show()