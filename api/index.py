from flask import Flask, jsonify, request

from anipy_api.provider import get_provider, LanguageTypeEnum
from anipy_api.anime import Anime

app = Flask(__name__)

# =========================================
# PROVIDER (Gogoanime custom base URL)
# =========================================

provider = get_provider(
    "gogoanime",
    base_url_override="https://gogoanimes.cv/"
)


# =========================================
# HELPERS
# =========================================

def get_lang():
    lang = request.args.get("lang", "sub").lower()
    return (
        LanguageTypeEnum.DUB
        if lang == "dub"
        else LanguageTypeEnum.SUB
    )


def safe_search(query):
    try:
        results = provider.get_search(query)
        return results if results else []
    except Exception:
        return []


# =========================================
# HOME
# =========================================

@app.route("/")
def home():
    return jsonify({
        "success": True,
        "provider": "gogoanime",
        "base_url": "https://gogoanimes.cv/",
        "routes": {
            "/search?q=naruto": "Search anime",
            "/anime?q=naruto": "Anime info",
            "/episodes?q=naruto": "Episode list",
            "/watch?q=naruto&episode=1": "Stream video"
        }
    })


# =========================================
# SEARCH
# =========================================

@app.route("/search")
def search():
    query = request.args.get("q")

    if not query:
        return jsonify({
            "success": False,
            "error": "Missing ?q="
        }), 400

    try:
        results = safe_search(query)

        data = []

        for r in results:
            data.append({
                "title": getattr(r, "name", None),
                "id": getattr(r, "identifier", None),
                "languages": [
                    str(x) for x in getattr(r, "languages", [])
                ]
            })

        return jsonify({
            "success": True,
            "count": len(data),
            "results": data
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# =========================================
# ANIME INFO
# =========================================

@app.route("/anime")
def anime_info():
    query = request.args.get("q")

    if not query:
        return jsonify({
            "success": False,
            "error": "Missing ?q="
        }), 400

    try:
        results = safe_search(query)

        if not results:
            return jsonify({
                "success": False,
                "error": "Anime not found"
            }), 404

        anime_result = results[0]

        anime = Anime.from_search_result(provider, anime_result)
        info = anime.get_info()

        return jsonify({
            "success": True,
            "anime": {
                "title": info.name,
                "image": info.image,
                "genres": info.genres,
                "synopsis": info.synopsis
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

@app.route("/episodes")
def episodes():
    query = request.args.get("q")

    if not query:
        return jsonify({
            "success": False,
            "error": "Missing ?q="
        }), 400

    try:
        results = safe_search(query)

        if not results:
            return jsonify({
                "success": False,
                "error": "Anime not found"
            }), 404

        anime = Anime.from_search_result(provider, results[0])

        eps = anime.get_episodes(lang=get_lang())

        return jsonify({
            "success": True,
            "anime": results[0].name,
            "episodes": list(eps)
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# =========================================
# WATCH (STREAM FIXED + SAFE)
# =========================================

@app.route("/watch")
def watch():
    query = request.args.get("q")
    episode = request.args.get("episode")

    if not query or not episode:
        return jsonify({
            "success": False,
            "error": "Missing ?q or ?episode"
        }), 400

    try:
        results = safe_search(query)

        if not results:
            return jsonify({
                "success": False,
                "error": "Anime not found"
            }), 404

        anime = Anime.from_search_result(provider, results[0])

        streams = anime.get_videos(
            episode=float(episode),
            lang=get_lang()
        )

        if not streams:
            return jsonify({
                "success": False,
                "error": "No streams found"
            }), 404

        output = []

        for s in streams:
            try:
                url = getattr(s, "url", None)
                if not url:
                    continue

                output.append({
                    "url": url,
                    "quality": getattr(s, "resolution", "unknown"),
                    "episode": episode
                })
            except:
                continue

        return jsonify({
            "success": True,
            "anime": results[0].name,
            "episode": episode,
            "streams": output
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error_type": type(e).__name__,
            "error": str(e)
        }), 500


# =========================================
# RUN (ONLY FOR LOCAL TESTING)
# =========================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
