"""Render a stats card SVG: contributions past year + total stars."""
import json, os, subprocess, sys

USER = os.environ.get("GH_PROFILE_USER") or sys.exit("GH_PROFILE_USER not set")

QUERY = """
query($u:String!, $after:String){
  user(login:$u){
    contributionsCollection{ contributionCalendar{ totalContributions } }
    repositories(first:100, after:$after, ownerAffiliations:OWNER, isFork:false){
      pageInfo{ hasNextPage endCursor }
      nodes{ stargazerCount }
    }
  }
}
"""

def gql(after=None):
    cmd = ["gh", "api", "graphql", "-f", f"query={QUERY}", "-f", f"u={USER}"]
    if after:
        cmd += ["-f", f"after={after}"]
    return json.loads(subprocess.run(cmd, capture_output=True, text=True, check=True).stdout)

stars, after, contributions = 0, None, None
while True:
    d = gql(after)["data"]["user"]
    stars += sum(n["stargazerCount"] for n in d["repositories"]["nodes"])
    if contributions is None:
        contributions = d["contributionsCollection"]["contributionCalendar"]["totalContributions"]
    page = d["repositories"]["pageInfo"]
    if not page["hasNextPage"]:
        break
    after = page["endCursor"]

FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
num = str(contributions)
stars_s = str(stars)

# One horizontal row: contributions on the left, stars beside it.
# Widths are measured from digit counts so the card stays tight as numbers grow.
PAD, H = 18, 64
num_w = len(num) * 22                      # 36px bold digits
label_w = 150                              # "contributions past year" at 14px
GAP, SEP, ICON, ICON_GAP = 12, 22, 17, 7
stars_w = len(stars_s) * 12                # 20px bold digits
W = PAD + num_w + GAP + label_w + SEP + ICON + ICON_GAP + stars_w + PAD

x = PAD
num_x = x
label_x = x + num_w + GAP
sep_x = label_x + label_w + SEP / 2
icon_x = label_x + label_w + SEP
count_x = icon_x + ICON + ICON_GAP

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{num} contributions past year, {stars} stars">
  <rect width="{W}" height="{H}" rx="10" fill="#0d1117"/>
  <text x="{num_x}" y="41" font-family="{FONT}" font-size="34" font-weight="800" fill="#f2c55c">{num}</text>
  <text x="{label_x}" y="39" font-family="{FONT}" font-size="14" font-weight="500" fill="#9aa4b2">contributions past year</text>
  <line x1="{sep_x}" y1="20" x2="{sep_x}" y2="44" stroke="#30363d" stroke-width="1"/>
  <path transform="translate({icon_x}, 22) scale(0.53)" d="M16 2l4.2 8.5 9.4 1.4-6.8 6.6 1.6 9.3L16 23.4 7.6 27.8l1.6-9.3-6.8-6.6 9.4-1.4z"
        fill="none" stroke="#9aa4b2" stroke-width="2.8" stroke-linejoin="round"/>
  <text x="{count_x}" y="39" font-family="{FONT}" font-size="20" font-weight="700" fill="#e6edf3">{stars_s}</text>
</svg>'''

os.makedirs("dist", exist_ok=True)
with open("dist/stats.svg", "w") as f:
    f.write(svg)
print(f"contributions={contributions} stars={stars}")
