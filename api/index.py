from flask import Flask, jsonify, request
from anipy_api.provider import (
    get_provider,
    list_providers,
    LanguageTypeEnum,
    Filters,
    FilterCapabilities,
    Season,
)
from anipy_api.anime import Anime

app = Flask(__name__)


# -------------------------
# CONFIG
# -------------------------

DEFAULT_PROVIDER = "allanime"


def get_anime_provider(provider_name=None):
    provider_name = provider_name or DEFAULT_PROVIDER
    return get_provider(provider_name)


# -------------------------
# HOME
# -------------------------

@app.route("/")
def home():
    return jsonify({
        "success": True,
        "message": "anipy-api Flask API",
        "default_provider": DEFAULT_PROVIDER,
        "routes": {
            "/providers": "List available providers",
            "/search?q=naruto": "Search anime",
            "/search?q=&year=2023&season=FALL": "Season search",
            "/anime?q=naruto": "Get anime info",
            "/episodes?q=naruto": "Get episodes",
            "/watch?q=naruto&episode=1": "Get stream"
        }
    })


# -------------------------
# LIST PROVIDERS
# -------------------------

@app.route("/providers")
def providers():
    try:
        data = []

        for provider_class in list_providers():
            try:
                provider = provider_class()

                data.append({
                    "name": provider.NAME,
                    "base_url": provider.BASE_URL,
                    "filter_caps": str(provider.FILTER_CAPS)
                })

            except Exception as e:
                data.append({
                    "name": str(provider_class),
                    "error": str(e)
                })

        return jsonify({
            "success": True,
            "providers": data
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# -------------------------
# SEARCH
# -------------------------

@app.route("/search")
def search():
    try:
        query = request.args.get("q", "")
        provider_name = request.args.get("provider", DEFAULT_PROVIDER)

        provider = get_anime_provider(provider_name)

        filters = None

        year = request.args.get("year")
        season = request.args.get("season")

        # Optional filter support
        if (
            year
            and season
            and provider.FILTER_CAPS & (
                FilterCapabilities.SEASON
                | FilterCapabilities.YEAR
                | FilterCapabilities.NO_QUERY
            )
        ):
            filters = Filters(
                year=int(year),
                season=Season[season.upper()]
            )

        results = provider.get_search(query, filters=filters)

        data = []

        for r in results:
            data.append({
                "title": r.name,
                "id": r.identifier,
                "languages": [str(lang) for lang in r.languages]
            })

        return jsonify({
            "success": True,
            "provider": provider_name,
            "count": len(data),
            "results": data
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# -------------------------
# GET ANIME OBJECT
# -------------------------

def get_anime_from_query(query, provider_name):
    provider = get_anime_provider(provider_name)

    results = provider.get_search(query)

    if not results:
        return None, None, None

    result = results[0]

    anime = Anime.from_search_result(provider, result)

    return provider, result, anime


# -------------------------
# ANIME INFO
# -------------------------

@app.route("/anime")
def anime_info():
    try:
        query = request.args.get("q")
        provider_name = request.args.get("provider", DEFAULT_PROVIDER)

        if not query:
            return jsonify({
                "success": False,
                "error": "Missing ?q="
            }), 400

        provider, result, anime = get_anime_from_query(
            query,
            provider_name
        )

        if not anime:
            return jsonify({
                "success": False,
                "error": "Anime not found"
            }), 404

        info = anime.get_info()

        return jsonify({
            "success": True,
            "provider": provider_name,
            "anime": {
                "title": info.name,
                "id": result.identifier,
                "genres": info.genres,
                "synopsis": info.synopsis,
                "image": info.image,
                "languages": [str(lang) for lang in result.languages]
            }
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# -------------------------
# EPISODES
# -------------------------

@app.route("/episodes")
def episodes():
    try:
        query = request.args.get("q")
        provider_name = request.args.get("provider", DEFAULT_PROVIDER)

        lang = request.args.get("lang", "sub").lower()

        if not query:
            return jsonify({
                "success": False,
                "error": "Missing ?q="
            }), 400

        provider, result, anime = get_anime_from_query(
            query,
            provider_name
        )

        if not anime:
            return jsonify({
                "success": False,
                "error": "Anime not found"
            }), 404

        language = (
            LanguageTypeEnum.DUB
            if lang == "dub"
            else LanguageTypeEnum.SUB
        )

        eps = anime.get_episodes(lang=language)

        return jsonify({
            "success": True,
            "provider": provider_name,
            "language": lang,
            "episodes": list(eps)
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# -------------------------
# WATCH
# -------------------------

@app.route("/watch")
def watch():
    try:
        query = request.args.get("q")
        episode = request.args.get("episode")

        provider_name = request.args.get(
            "provider",
            DEFAULT_PROVIDER
        )

        lang = request.args.get("lang", "sub").lower()

        quality = request.args.get("quality", "1080")

        if not query or not episode:
            return jsonify({
                "success": False,
                "error": "Missing ?q= or ?episode="
            }), 400

        provider, result, anime = get_anime_from_query(
            query,
            provider_name
        )

        if not anime:
            return jsonify({
                "success": False,
                "error": "Anime not found"
            }), 404

        language = (
            LanguageTypeEnum.DUB
            if lang == "dub"
            else LanguageTypeEnum.SUB
        )

        stream = anime.get_video(
            episode=float(episode),
            lang=language,
            preferred_quality=quality
        )

        return jsonify({
            "success": True,
            "provider": provider_name,
            "anime": result.name,
            "episode": episode,
            "language": lang,
            "video": stream.url,
            "quality": stream.resolution
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# IMPORTANT:
# Do NOT use app.run() on Vercel
