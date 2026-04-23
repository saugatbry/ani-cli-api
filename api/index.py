from flask import Flask, jsonify, request

from anipy_api.provider import (
    get_provider,
    LanguageTypeEnum,
)

from anipy_api.anime import Anime

app = Flask(__name__)

# =========================================
# PROVIDER
# =========================================

# allanime = allmanga.to
provider = get_provider("allanime")


# =========================================
# HELPERS
# =========================================

def find_anime(query):
    """
    Search anime safely
    """

    results = provider.get_search(query)

    if not results:
        return None

    return results[0]


def get_language():
    lang = request.args.get("lang", "sub").lower()

    return (
        LanguageTypeEnum.DUB
        if lang == "dub"
        else LanguageTypeEnum.SUB
    )


# =========================================
# HOME
# =========================================

@app.route("/")
def home():

    return jsonify({

        "success": True,

        "provider": "allanime",

        "site": "allmanga.to",

        "routes": {

            "/search?q=naruto":
                "Search anime",

            "/anime?q=naruto":
                "Anime info",

            "/episodes?q=naruto":
                "Episode list",

            "/watch?q=naruto&episode=1":
                "Get streams"

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

        result = find_anime(query)

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

                "id": result.identifier,

                "image": info.image,

                "genres": info.genres,

                "synopsis": info.synopsis,

                "languages": [
                    str(x)
                    for x in result.languages
                ]

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

        result = find_anime(query)

        if not result:

            return jsonify({

                "success": False,

                "error": "Anime not found"

            }), 404

        anime = Anime.from_search_result(
            provider,
            result
        )

        language = get_language()

        eps = anime.get_episodes(
            lang=language
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

        result = find_anime(query)

        if not result:

            return jsonify({

                "success": False,

                "error": "Anime not found"

            }), 404

        anime = Anime.from_search_result(
            provider,
            result
        )

        language = get_language()

        # safer than get_video()
        streams = anime.get_videos(
            episode=float(episode),
            lang=language
        )

        if not streams:

            return jsonify({

                "success": False,

                "error": "No streams found"

            }), 404

        parsed_streams = []

        for s in streams:

            try:

                parsed_streams.append({

                    "url":
                        getattr(s, "url", None),

                    "quality":
                        getattr(
                            s,
                            "resolution",
                            "unknown"
                        ),

                    "episode":
                        getattr(
                            s,
                            "episode",
                            episode
                        )

                })

            except Exception:
                pass

        return jsonify({

            "success": True,

            "anime": result.name,

            "episode": episode,

            "streams": parsed_streams

        })

    except Exception as e:

        return jsonify({

            "success": False,

            "error_type":
                type(e).__name__,

            "error": str(e)

        }), 500


# =========================================
# IMPORTANT
# =========================================
# DO NOT USE app.run() ON VERCEL
