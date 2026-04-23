from flask import Flask, jsonify, request
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

BASE_URL = "https://allmanga.to"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    )
}


# =========================================
# HELPERS
# =========================================


def fetch(url):
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=20
    )

    response.raise_for_status()

    return response.text


# =========================================
# HOME
# =========================================

@app.route("/")
def home():
    return jsonify({
        "success": True,
        "site": "allmanga.to",
        "routes": {
            "/anime-list?lang=sub": "Get anime page",
            "/search?q=naruto&lang=sub": "Search anime",
            "/anime/<anime_id>": "Get anime info",
            "/episodes/<anime_id>?lang=sub": "Get episodes",
            "/watch/<anime_id>/<episode>?lang=sub": "Get streams"
        }
    })


# =========================================
# ANIME LIST
# =========================================

@app.route("/anime-list")
def anime_list():
    try:
        lang = request.args.get("lang", "sub")

        url = (
            f"{BASE_URL}/search-anime?"
            f"tr={lang}&cty=ALL"
        )

        html = fetch(url)

        anime_links = re.findall(
            r'/bangumi/([A-Za-z0-9_-]+)',
            html
        )

        unique = list(set(anime_links))

        return jsonify({
            "success": True,
            "language": lang,
            "count": len(unique),
            "anime_ids": unique
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# =========================================
# SEARCH
# =========================================

@app.route("/search")
def search():
    try:
        query = request.args.get("q")
        lang = request.args.get("lang", "sub")

        if not query:
            return jsonify({
                "success": False,
                "error": "Missing ?q="
            }), 400

        url = (
            f"{BASE_URL}/search-anime?"
            f"tr={lang}&cty=ALL"
        )

        html = fetch(url)

        pattern = re.compile(
            r'/bangumi/([A-Za-z0-9_-]+)'
        )

        ids = list(set(pattern.findall(html)))

        results = []

        for anime_id in ids:
            clean_name = anime_id.replace("-", " ")

            if query.lower() in clean_name.lower():
                results.append({
                    "id": anime_id,
                    "title": clean_name.title(),
                    "url": (
                        f"{BASE_URL}/bangumi/{anime_id}"
                    )
                })

        return jsonify({
            "success": True,
            "count": len(results),
            "results": results[:50]
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# =========================================
# ANIME INFO
# =========================================

@app.route("/anime/<anime_id>")
def anime_info(anime_id):
    try:
        url = f"{BASE_URL}/bangumi/{anime_id}"

        html = fetch(url)

        soup = BeautifulSoup(html, "html.parser")

        title = anime_id.replace("-", " ").title()

        # attempt image extraction
        image = None

        img = soup.find("img")

        if img:
            image = img.get("src")

        return jsonify({
            "success": True,
            "anime": {
                "id": anime_id,
                "title": title,
                "url": url,
                "image": image
            }
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# =========================================
# EPISODES
# =========================================

@app.route("/episodes/<anime_id>")
def episodes(anime_id):
    try:
        lang = request.args.get("lang", "sub")

        url = (
            f"{BASE_URL}/bangumi/"
            f"{anime_id}"
        )

        html = fetch(url)

        episode_matches = re.findall(
            r'/p-([0-9.]+)-(sub|dub)',
            html
        )

        eps = []

        for ep, ep_lang in episode_matches:
            if ep_lang == lang:
                eps.append(float(ep))

        eps = sorted(list(set(eps)))

        return jsonify({
            "success": True,
            "anime_id": anime_id,
            "language": lang,
            "episodes": eps
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# =========================================
# WATCH / STREAMS
# =========================================

@app.route("/watch/<anime_id>/<episode>")
def watch(anime_id, episode):
    try:
        lang = request.args.get("lang", "sub")

        episode_url = (
            f"{BASE_URL}/bangumi/"
            f"{anime_id}/p-{episode}-{lang}"
        )

        html = fetch(episode_url)

        stream_types = [
            "default",
            "ak",
            "yt",
            "luf-mp4",
            "vg",
            "fm-hls",
            "vid-mp4",
            "mp4",
            "ok",
            "sl-mp4",
            "uv-mp4"
        ]

        found_streams = []

        for stream_type in stream_types:
            if stream_type in html:
                found_streams.append({
                    "server": stream_type
                })

        # extract possible m3u8/mp4 links
        video_links = re.findall(
            r'https?:\\/\\/[^\"\']+?(?:m3u8|mp4)',
            html
        )

        cleaned_links = []

        for link in video_links:
            cleaned_links.append(
                link.replace("\\/", "/")
            )

        cleaned_links = list(set(cleaned_links))

        return jsonify({
            "success": True,
            "anime_id": anime_id,
            "episode": episode,
            "language": lang,
            "page_url": episode_url,
            "servers": found_streams,
            "video_links": cleaned_links
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
