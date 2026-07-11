#!/usr/bin/env python3
"""Generate a static 42-profile badge SVG from the 42 API and write it to badges/42-badge.svg."""

import base64
import os
import sys

import requests

INTRA_LOGIN = "nmunari"
CURSUS_NAME = "42cursus"
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "badges", "42-badge.svg")

BG_COLOR = "#081d30"
ACCENT_COLOR = "#278BAE"
TRACK_COLOR = "#384857"
TEXT_COLOR = "#ffffff"
BORDER_COLOR = "#278BAE"

TEMPLATE = """<svg width="450" height="275" viewBox="0 0 450 275" xmlns="http://www.w3.org/2000/svg" font-family="'Segoe UI', Ubuntu, sans-serif">
  <rect x="0.5" y="0.5" width="449" height="274" rx="7.9" fill="{bg}" stroke="{border}" />
  <text x="24" y="40" font-size="18" font-weight="700" fill="{text}">{login}&#x27;s Profile</text>

  <defs>
    <clipPath id="avatarClip">
      <rect x="24" y="68" width="56" height="56" rx="8" />
    </clipPath>
  </defs>
  <rect x="23" y="67" width="58" height="58" rx="9" fill="{track}" />
  <image href="{avatar}" x="24" y="68" width="56" height="56" clip-path="url(#avatarClip)" preserveAspectRatio="xMidYMid slice" />

  <text x="96" y="80" font-size="13" font-weight="700" fill="{text}">name:</text>
  <text x="162" y="80" font-size="13" fill="{accent}">{full_name}</text>
  <text x="96" y="102" font-size="13" font-weight="700" fill="{text}">email:</text>
  <text x="162" y="102" font-size="13" fill="{accent}">{email}</text>
  <text x="96" y="124" font-size="13" font-weight="700" fill="{text}">cursus:</text>
  <text x="162" y="124" font-size="13" fill="{accent}">{cursus}</text>
  <text x="96" y="146" font-size="13" font-weight="700" fill="{text}">grade:</text>
  <text x="162" y="146" font-size="13" fill="{accent}">{grade}</text>

  <rect x="24" y="172" width="402" height="34" rx="17" fill="{track}" />
  <rect x="24" y="172" width="{bar_width}" height="34" rx="17" fill="{accent}" />
  <text x="225" y="194" font-size="14" font-weight="700" fill="{text}" text-anchor="middle">level {level} - {percent}%</text>

  <rect x="24" y="224" width="70" height="24" rx="5" fill="{track}" stroke="{accent}" />
  <text x="59" y="240" font-size="11" font-weight="700" fill="{text}" text-anchor="middle">STUDENT</text>

  <text x="426" y="240" font-size="14" font-weight="700" fill="{text}" text-anchor="end">42 NETWORK</text>
</svg>
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
    bar_width = round(402 * (level - whole_level))

    return TEMPLATE.format(
        bg=BG_COLOR,
        border=BORDER_COLOR,
        text=TEXT_COLOR,
        accent=ACCENT_COLOR,
        track=TRACK_COLOR,
        login=user.get("login", INTRA_LOGIN),
        full_name=user.get("usual_full_name") or user.get("displayname", ""),
        email=user.get("email", ""),
        cursus=CURSUS_NAME,
        grade=cursus_user.get("grade") or "N/A",
        level=whole_level,
        percent=percent,
        bar_width=max(bar_width, 0),
        avatar=avatar_data_uri,
    )


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
