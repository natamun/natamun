#!/usr/bin/env python3
"""Generate a static 42-profile badge SVG from the 42 API and write it to badges/42-badge.svg."""

import base64
import os
import sys
from xml.sax.saxutils import escape

import requests

INTRA_LOGIN = "nmunari"
CURSUS_NAME = "42cursus"
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "badges", "42-badge.svg")

BG_COLOR = "#081d30"
ACCENT_COLOR = "#278BAE"
TRACK_COLOR = "#384857"
STUDENT_BADGE_BG = "#1E5D75"
BORDER_COLOR = "#278BAE"
CARD_RADIUS = "7px"  # matches border_radius=7 on the sibling Top Languages card

# Mirrors the markup produced by badge.mediaplus.ma: an outer <svg> hosting a
# <foreignObject> full of styled HTML, plus an inline "42" logo SVG. Dynamic
# values are swapped in via plain string tokens (not str.format) because the
# embedded CSS already uses '{' '}' for its keyframes.
TEMPLATE = """<svg viewBox="0 0 450 275" width="450" height="275" xmlns="http://www.w3.org/2000/svg"><foreignObject width="100%" height="100%"><style>.slideUp{animation-duration:1s;animation-name:slideUp}.slideDown{animation-duration:1s;animation-name:slideDown}.flipInX{animation-duration:1s;animation-name:flipInX}@keyframes slideUp{from{opacity:0;transform:translateY(20px)}25%{opacity:0}to{opacity:1;transform:translateY(0)}}@keyframes slideDown{from{opacity:0;transform:translateY(-20px)}25%{opacity:0}to{opacity:1;transform:translateY(0)}}@keyframes flipInX{from{transform:perspective(400px) rotate3d(1,0,0,90deg);animation-timing-function:ease-in;opacity:0}40%{transform:perspective(400px) rotate3d(1,0,0,-20deg);animation-timing-function:ease-in}60%{transform:perspective(400px) rotate3d(1,0,0,10deg);opacity:1}80%{transform:perspective(400px) rotate3d(1,0,0,-5deg)}to{transform:perspective(400px)}}</style><svg xmlns="http://www.w3.org/1999/xhtml"><div style="font-family:sans-serif;font-weight:bold;color:#ffffff;box-sizing:border-box;padding:20px;width:450px;height:275px;border-radius:@@CARD_RADIUS@@;border:1px solid @@BORDER_COLOR@@;background-color:@@BG_COLOR@@;">
<div style="margin-bottom:20px"><h2 class="slideDown" style="margin:0;font-size:18px"><span>@@LOGIN@@</span>&#x27;s Profile</h2></div>
<div class="slideDown" style="margin-bottom:20px;display:flex;align-items:center"><div style="margin-right:20px;height:75px;width:75px;border-radius:10px;background:#f0f0f0;@@AVATAR_STYLE@@"></div><table style="font-size:16px"><tr><td style="padding-right:10px">name:</td><td style="color:@@ACCENT_COLOR@@">@@FULL_NAME@@</td></tr><tr><td style="padding-right:10px">email:</td><td style="color:@@ACCENT_COLOR@@">@@EMAIL@@</td></tr><tr><td style="padding-right:10px">cursus:</td><td style="color:@@ACCENT_COLOR@@">@@CURSUS@@</td></tr><tr><td style="padding-right:10px">grade:</td><td style="color:@@ACCENT_COLOR@@">@@GRADE@@</td></tr></table></div>
<div class="flipInX" style="margin-bottom:20px;height:40px;border-radius:10px;background:@@TRACK_COLOR@@;box-shadow:0 0 20px 5px rgba(0,0,0,.1)"><div style="height:40px;width:@@PERCENT@@%;border-radius:10px;background:@@ACCENT_COLOR@@"></div><div style="margin:0;margin-top:-40px;height:40px;display:flex;justify-content:center;align-items:center"><p style="text-shadow:0 0 10px #000000">level @@LEVEL@@ - @@PERCENT@@%</p></div></div>
<div class="slideUp" style="display:flex;justify-content:space-between;align-items:center"><div style="font-size:14px;padding:4px 6px;border-radius:5px;background:@@STUDENT_BADGE_BG@@;color:#ffffff">STUDENT</div><div style="display:flex;align-items:center"><svg style="margin-left:20px" xmlns="http://www.w3.org/2000/svg" width="91" height="15" fill="#ffffff"><path d="M11.813 0H7.874L0 7.875v3.188h7.875V15h3.938V7.875H3.936L11.814 0zM13.5 3.938L17.438 0H13.5v3.938z"></path><path d="M21.375 3.938V0h-3.938v3.938L13.5 7.874v3.938h3.938V7.874l3.937-3.938z"></path><path d="M21.375 7.875l-3.938 3.938h3.938V7.874zm8.063 2.588l1.05-8.438h1.687l3.9 5.475.675-5.475h1.95l-1.2 8.438h-1.538l-3.75-5.513-.825 5.513h-1.95zM45 3.75h-2.775v1.612h2.663l-.225 1.65H42l-.225 1.875h2.813v1.65h-5.063l1.05-8.512h4.65L45 3.75zm4.688 0l-.938 6.713H46.8l.938-6.713H45.9l.225-1.725h5.625l-.225 1.725h-1.837zm4.2-1.725L55.013 7.5l2.474-5.475h1.35L60 7.5l2.438-5.475H64.5l-3.75 8.438h-1.688l-1.124-5.138-2.4 5.138h-1.65L51.9 2.024h1.988zm18.712.9a4.05 4.05 0 011.2 3 5.025 5.025 0 01-1.313 3.45A4.651 4.651 0 0169 10.688a4.314 4.314 0 01-3.225-1.238 4.087 4.087 0 01-1.2-2.925 4.65 4.65 0 011.388-3.413 4.839 4.839 0 013.487-1.275 4.425 4.425 0 013.15 1.088zm-5.25 1.5a2.887 2.887 0 00-.75 1.95 2.476 2.476 0 00.675 1.8 2.437 2.437 0 001.837.675 2.513 2.513 0 001.913-.713c.518-.56.8-1.299.787-2.062a2.437 2.437 0 00-.562-1.8 2.513 2.513 0 00-1.875-.525 2.737 2.737 0 00-1.875.675h-.15zm11.062-2.4a2.812 2.812 0 012.25.75 2.4 2.4 0 01.6 1.725 2.7 2.7 0 01-.674 1.875 3.069 3.069 0 01-1.35.675l2.174 3.413h-2.287L77.1 7.125l-.412 3.338h-1.95l1.05-8.438h2.624zm-1.162 3.75h.487c.398.022.792-.083 1.126-.3a1.2 1.2 0 00.45-.975.937.937 0 00-.563-.75 1.875 1.875 0 00-1.088-.225H77.4l-.15 2.25zm7.763-.225l3.075-3.525h2.325l-3.75 4.088L90 10.463h-2.475l-2.55-3.75-.487 3.75H82.5l.975-8.438h1.95l-.412 3.525z"></path></svg></div></div>
</div></svg></foreignObject></svg>
"""


def get_access_token(client_id: str, client_secret: str) -> str:
    response = requests.post(
        "https://api.intra.42.fr/oauth/token",
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=15,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def get_user(token: str, login: str) -> dict:
    response = requests.get(
        f"https://api.intra.42.fr/v2/users/{login}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


def find_cursus(user: dict, cursus_name: str) -> dict:
    for cursus_user in user.get("cursus_users", []):
        if cursus_user.get("cursus", {}).get("name") == cursus_name:
            return cursus_user
    raise ValueError(f"No cursus_user found for cursus '{cursus_name}'")


def get_avatar_data_uri(url: str) -> str:
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    content_type = response.headers.get("Content-Type", "image/jpeg")
    encoded = base64.b64encode(response.content).decode("ascii")
    return f"data:{content_type};base64,{encoded}"


def render_svg(user: dict, cursus_user: dict, avatar_data_uri: str) -> str:
    level = cursus_user.get("level", 0.0)
    whole_level = int(level)
    percent = round((level - whole_level) * 100)
    percent = max(min(percent, 100), 0)

    avatar_style = (
        f"background-image:url({avatar_data_uri});"
        "background-repeat:no-repeat;background-size:cover;background-position:center"
        if avatar_data_uri
        else ""
    )

    tokens = {
        "@@BG_COLOR@@": BG_COLOR,
        "@@ACCENT_COLOR@@": ACCENT_COLOR,
        "@@TRACK_COLOR@@": TRACK_COLOR,
        "@@STUDENT_BADGE_BG@@": STUDENT_BADGE_BG,
        "@@BORDER_COLOR@@": BORDER_COLOR,
        "@@CARD_RADIUS@@": CARD_RADIUS,
        "@@AVATAR_STYLE@@": avatar_style,
        "@@LOGIN@@": escape(user.get("login", INTRA_LOGIN)),
        "@@FULL_NAME@@": escape(user.get("usual_full_name") or user.get("displayname", "")),
        "@@EMAIL@@": escape(user.get("email", "")),
        "@@CURSUS@@": escape(CURSUS_NAME),
        "@@GRADE@@": escape(cursus_user.get("grade") or "N/A"),
        "@@LEVEL@@": str(whole_level),
        "@@PERCENT@@": str(percent),
    }

    svg = TEMPLATE
    for token, value in tokens.items():
        svg = svg.replace(token, value)
    return svg


def main() -> int:
    client_id = os.environ.get("FT_CLIENT_ID")
    client_secret = os.environ.get("FT_CLIENT_SECRET")
    if not client_id or not client_secret:
        print("Missing FT_CLIENT_ID or FT_CLIENT_SECRET environment variables.", file=sys.stderr)
        return 1

    token = get_access_token(client_id, client_secret)
    user = get_user(token, INTRA_LOGIN)
    cursus_user = find_cursus(user, CURSUS_NAME)

    avatar_url = user.get("image", {}).get("versions", {}).get("small") or user.get(
        "image", {}
    ).get("link")
    avatar_data_uri = get_avatar_data_uri(avatar_url) if avatar_url else ""

    svg = render_svg(user, cursus_user, avatar_data_uri)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg)

    print(f"Wrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
