from flask import Flask, jsonify, request
from anipy_api.provider import get_provider
from anipy_api.anime import Anime
from anipy_api.provider import LanguageTypeEnum

app = Flask(__name__)

# Use allanime provider (allmanga.to)
provider = get_provider("allanime")


@app.route("/")
def home():
    return jsonify({
        "success": True,
        "api": "AllAnime API",
        "provider": "allmanga.to"
    })


# SEARCH ANIME
@app.route("/search")
def search():
    query = request.args.get("q")

    if not query:
        return jsonify({"error": "Missing query"}), 400

    try:
        results = provider.get_search(query)

        data = []

        for r in results:
            data.append({
                "name": r.name,
                "id": r.identifier,
                "languages": [str(x) for x in r.languages]
            })

        return jsonify({
            "success": True,
            "count": len(data),
            "results": data
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# GET ANIME INFO
@app.route("/anime/<anime_id>")
def anime_info(anime_id):
    try:
        results = provider.get_search("")

        target = None

        for r in results:
            if r.identifier == anime_id:
                target = r
                break

        if not target:
            return jsonify({"error": "Anime not found"}), 404

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
        return jsonify({"error": str(e)}), 500


# GET EPISODES
@app.route("/episodes/<anime_id>")
def episodes(anime_id):
    try:
        results = provider.get_search("")

        target = None

        for r in results:
            if r.identifier == anime_id:
                target = r
                break

        if not target:
            return jsonify({"error": "Anime not found"}), 404

        anime = Anime.from_search_result(provider, target)

        eps = anime.get_episodes(lang=LanguageTypeEnum.SUB)

        return jsonify({
            "success": True,
            "episodes": eps
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# GET VIDEO STREAM
@app.route("/watch/<anime_id>/<episode>")
def watch(anime_id, episode):
    try:
        results = provider.get_search("")

        target = None

        for r in results:
            if r.identifier == anime_id:
                target = r
                break

        if not target:
            return jsonify({"error": "Anime not found"}), 404

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
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
