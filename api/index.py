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

# =========================================
# CONFIG
# =========================================

# safest modern provider
DEFAULT_PROVIDER = "animekai"

# =========================================
# HELPERS
# =========================================


def get_anime_provider(provider_name=None):
    provider_name = provider_name or DEFAULT_PROVIDER
    return get_provider(provider_name)


def build_filters(provider):
    """
    Build optional filters from query params
    """

    year = request.args.get("year")
    season = request.args.get("season")

    if not year or not season:
        return None

    # check provider capabilities
    if not (
        provider.FILTER_CAPS
        & (
            FilterCapabilities.SEASON
            | FilterCapabilities.YEAR
            | FilterCapabilities.NO_QUERY
        )
    ):
        return None

    try:
        return Filters(
            year=int(year),
            season=Season[season.upper()]
        )

    except Exception:
        return None


def create_anime(query, provider_name):
    provider = get_anime_provider(provider_name)

    results = provider.get_search(query)

    if not results:
        return None, None, None

    result = results[0]

    anime = Anime.from_search_result(
        provider,
        result
    )

    return provider, result, anime


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
        "message": "anipy-api Flask API",

        "default_provider": DEFAULT_PROVIDER,

        "routes": {

            "/providers":
                "List providers",

            "/search?q=naruto":
                "Search anime",

            "/search?q=&year=2023&season=FALL":
                "Season search",

            "/anime?q=naruto":
                "Anime info",

            "/episodes?q=naruto":
                "Episode list",

            "/watch?q=naruto&episode=1":
                "Get streams",

        }
    })


# =========================================
# LIST PROVIDERS
# =========================================

@app.route("/providers")
def providers():

    try:
        providers_data = []

        for provider_class in list_providers():

            try:
                provider = provider_class()

                providers_data.append({

                    "name": provider.NAME,

                    "base_url": provider.BASE_URL,

                    "filter_caps":
                        str(provider.FILTER_CAPS)

                })

            except Exception as e:

                providers_data.append({

                    "error": str(e)

                })

        return jsonify({

            "success": True,

            "providers": providers_data

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
        query = request.args.get("q", "")

        provider_name = request.args.get(
            "provider",
            DEFAULT_PROVIDER
        )

        provider = get_anime_provider(
            provider_name
        )

        filters = build_filters(provider)

        results = provider.get_search(
            query,
            filters=filters
        )

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

            "provider": provider_name,

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

    try:
        query = request.args.get("q")

        provider_name = request.args.get(
            "provider",
            DEFAULT_PROVIDER
        )

        if not query:

            return jsonify({

                "success": False,

                "error":
                    "Missing ?q="

            }), 400

        provider, result, anime = create_anime(
            query,
            provider_name
        )

        if not anime:

            return jsonify({

                "success": False,

                "error":
                    "Anime not found"

            }), 404

        info = anime.get_info()

        return jsonify({

            "success": True,

            "provider": provider_name,

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

    try:
        query = request.args.get("q")

        provider_name = request.args.get(
            "provider",
            DEFAULT_PROVIDER
        )

        if not query:

            return jsonify({

                "success": False,

                "error":
                    "Missing ?q="

            }), 400

        provider, result, anime = create_anime(
            query,
            provider_name
        )

        if not anime:

            return jsonify({

                "success": False,

                "error":
                    "Anime not found"

            }), 404

        language = get_language()

        eps = anime.get_episodes(
            lang=language
        )

        return jsonify({

            "success": True,

            "provider": provider_name,

            "anime": result.name,

            "episodes": list(eps)

        })

    except Exception as e:

        return jsonify({

            "success": False,

            "error": str(e)

        }), 500


# =========================================
# WATCH / STREAMS
# =========================================

@app.route("/watch")
def watch():

    try:

        query = request.args.get("q")

        episode = request.args.get("episode")

        provider_name = request.args.get(
            "provider",
            DEFAULT_PROVIDER
        )

        if not query:

            return jsonify({

                "success": False,

                "error":
                    "Missing ?q="

            }), 400

        if not episode:

            return jsonify({

                "success": False,

                "error":
                    "Missing ?episode="

            }), 400

        provider, result, anime = create_anime(
            query,
            provider_name
        )

        if not anime:

            return jsonify({

                "success": False,

                "error":
                    "Anime not found"

            }), 404

        language = get_language()

        try:

            streams = anime.get_videos(
                episode=float(episode),
                lang=language
            )

        except Exception as stream_error:

            return jsonify({

                "success": False,

                "stage":
                    "get_videos",

                "provider":
                    provider_name,

                "anime":
                    result.name,

                "episode":
                    episode,

                "error":
                    str(stream_error)

            }), 500

        if not streams:

            return jsonify({

                "success": False,

                "error":
                    "No streams found"

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

            "provider":
                provider_name,

            "anime":
                result.name,

            "episode":
                episode,

            "streams":
                parsed_streams

        })

    except Exception as e:

        return jsonify({

            "success": False,

            "error_type":
                type(e).__name__,

            "error":
                str(e)

        }), 500
