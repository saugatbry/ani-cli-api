from flask import Flask, jsonify, request
from anipy_api.provider import get_provider, LanguageTypeEnum
from anipy_api.anime import Anime

app = Flask(__name__)


def get_anime_provider():
    return get_provider("allanime")


@app.route("/")
def home():
    return jsonify({
        "success": True,
        "api": "AllAnime API",
        "provider": "allanime"
    })


# SEARCH ANIME
@app.route("/search")
def search():
    query = request.args.get("q")

    if not query:
        return jsonify({
            "success": False,
            "error": "Missing query parameter ?q="
        }), 400

    try:
        provider = get_anime_provider()

        results = provider.get_search(query)

        data = []

        for r in results:
            data.append({
                "title": r.name,
                "id": r.identifier,
                "languages": [str(lang) for lang in r.languages]
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


# GET ANIME INFO
@app.route("/anime")
def anime_info():
    query = request.args.get("q")

    if not query:
        return jsonify({
            "success": False,
            "error": "Missing query parameter ?q="
        }), 400

    try:
        provider = get_anime_provider()

        results = provider.get_search(query)

        if not results:
            return jsonify({
                "success": False,
                "error": "Anime not found"
            }), 404

        target = results[0]

        anime = Anime.from_search_result(provider, target)

        info = anime.get_info()

        return jsonify({
            "success": True,
            "title": info.name,
            "genres": info.genres,
            "synopsis": info.synopsis,
            "image": info.image
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# GET EPISODES
@app.route("/episodes")
def episodes():
    query = request.args.get("q")

    if not query:
        return jsonify({
            "success": False,
            "error": "Missing query parameter ?q="
        }), 400

    try:
        provider = get_anime_provider()

        results = provider.get_search(query)

        if not results:
            return jsonify({
                "success": False,
                "error": "Anime not found"
            }), 404

        target = results[0]

        anime = Anime.from_search_result(provider, target)

        eps = anime.get_episodes(lang=LanguageTypeEnum.SUB)

        return jsonify({
            "success": True,
            "episodes": list(eps)
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# WATCH EPISODE
@app.route("/watch")
def watch():
    query = request.args.get("q")
    episode = request.args.get("episode")

    if not query or not episode:
        return jsonify({
            "success": False,
            "error": "Missing ?q= or ?episode="
        }), 400

    try:
        provider = get_anime_provider()

        results = provider.get_search(query)

        if not results:
            return jsonify({
                "success": False,
                "error": "Anime not found"
            }), 404

        target = results[0]

        anime = Anime.from_search_result(provider, target)

        stream = anime.get_video(
            episode=float(episode),
            lang=LanguageTypeEnum.SUB,
            preferred_quality=1080
        )

        return jsonify({
            "success": True,
            "episode": episode,
            "video": stream.url,
            "quality": stream.resolution
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# IMPORTANT:
# DO NOT use app.run() on Vercel
