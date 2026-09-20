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

W, H = 420, 300
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
num = str(contributions)
# centre the star glyph + count as one unit, so 2- and 3-digit totals both sit centred
ICON, GAP = 36, 12
star_w = len(str(stars)) * 21
group_x = (W - (ICON + GAP + star_w)) / 2

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{num} contributions past year, {stars} stars">
  <rect width="{W}" height="{H}" rx="12" fill="#0d1117"/>
  <text x="{W/2}" y="150" text-anchor="middle" font-family="{FONT}" font-size="104" font-weight="800" fill="#f2c55c">{num}</text>
  <text x="{W/2}" y="192" text-anchor="middle" font-family="{FONT}" font-size="24" font-weight="500" fill="#e6edf3">contributions past year</text>
  <g transform="translate({group_x}, 232)">
    <path d="M18 2.5l4.6 9.3 10.3 1.5-7.45 7.26 1.76 10.25L18 25.97l-9.21 4.84 1.76-10.25L3.1 13.3l10.3-1.5z"
          fill="none" stroke="#e6edf3" stroke-width="2.6" stroke-linejoin="round"/>
    <text x="{ICON + GAP}" y="28" font-family="{FONT}" font-size="36" font-weight="800" fill="#e6edf3">{stars}</text>
  </g>
</svg>'''

os.makedirs("dist", exist_ok=True)
with open("dist/stats.svg", "w") as f:
    f.write(svg)
print(f"contributions={contributions} stars={stars}")
