from flask import Flask, jsonify, request

from anipy_api.provider import (
    get_provider,
    LanguageTypeEnum
)

from anipy_api.anime import Anime

app = Flask(__name__)

# =========================================
# USE ANIMEKAI INSTEAD OF ALLANIME
# =========================================

provider = get_provider("gogoanimes", base_url_override="https://gogoanimes.cv")

# =========================================
# HELPERS
# =========================================

def get_lang():

    lang = request.args.get(
        "lang",
        "sub"
    ).lower()

    return (
        LanguageTypeEnum.DUB
        if lang == "dub"
        else LanguageTypeEnum.SUB
    )


def search_anime(query):

    results = provider.get_search(query)

    if not results:
        return None

    return results[0]


# =========================================
# HOME
# =========================================

@app.route("/")
def home():

    return jsonify({

        "success": True,

        "provider": "animekai",

        "routes": {

            "/search?q=naruto":
                "search anime",

            "/anime?q=naruto":
                "anime info",

            "/episodes?q=naruto":
                "episodes",

            "/watch?q=naruto&episode=1":
                "video streams"

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

        results = provider.get_search(query)

        data = []

        for r in results:

            data.append({

                "title": r.name,

                "id": r.identifier,

                "languages": [
                    str(x)
                    for x in r.languages
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

        result = search_anime(query)

        if not result:

            return jsonify({

                "success": False,

                "error": "Anime not found"

            }), 404

        anime = Anime.from_search_result(
            provider,
            result
        )

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

        result = search_anime(query)

        if not result:

            return jsonify({

                "success": False,

                "error": "Anime not found"

            }), 404

        anime = Anime.from_search_result(
            provider,
            result
        )

        eps = anime.get_episodes(
            lang=get_lang()
        )

        return jsonify({

            "success": True,

            "anime": result.name,

            "episodes": list(eps)

        })

    except Exception as e:

        return jsonify({

            "success": False,

            "error": str(e)

        }), 500


# =========================================
# WATCH
# =========================================

@app.route("/watch")
def watch():

    query = request.args.get("q")
    episode = request.args.get("episode")

    if not query:

        return jsonify({

            "success": False,

            "error": "Missing ?q="

        }), 400

    if not episode:

        return jsonify({

            "success": False,

            "error": "Missing ?episode="

        }), 400

    try:

        result = search_anime(query)

        if not result:

            return jsonify({

                "success": False,

                "error": "Anime not found"

            }), 404

        anime = Anime.from_search_result(
            provider,
            result
        )

        # get all streams
        streams = anime.get_videos(
            episode=float(episode),
            lang=get_lang()
        )

        if not streams:

            return jsonify({

                "success": False,

                "error": "No streams found"

            }), 404

        parsed = []

        for s in streams:

            try:

                parsed.append({

                    "url":
                        getattr(s, "url", None),

                    "resolution":
                        getattr(
                            s,
                            "resolution",
                            "unknown"
                        )

                })

            except Exception:
                continue

        return jsonify({

            "success": True,

            "anime": result.name,

            "episode": episode,

            "streams": parsed

        })

    except Exception as e:

        return jsonify({

            "success": False,

            "error_type":
                type(e).__name__,

            "error": str(e)

        }), 500
