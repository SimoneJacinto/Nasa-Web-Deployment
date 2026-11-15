
import base64
import threading
from pathlib import Path

from flask import Flask, request, jsonify

import integration_adapter


# Project folder
BASE_DIR = Path(__file__).resolve().parent

print("Project folder:", BASE_DIR)
print("Public folder exists:", (BASE_DIR / "public").exists())
print("Homepage exists:", (BASE_DIR / "public" / "indexN.html").exists())

# Serve the existing frontend from the public folder
app = Flask(
    __name__,
    static_folder=str(BASE_DIR / "public"),
    static_url_path=""
)

# Vercel request size limit
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024

# Prevent simultaneous image-processing requests
pipeline_lock = threading.Lock()


# HOME PAGE
@app.route("/")
def home():
    return app.send_static_file("indexN.html")


# CHECK BACKEND CONNECTION
@app.route("/api/health")
def health():

    modules = {}

    for module in [
        "integration_adapter",
        "member4_adapter",
        "windspeed_mapper",
        "sonification",
        "nasa2py"
    ]:
        try:
            __import__(module)
            modules[module] = True
        except Exception:
            modules[module] = False

    return jsonify({
        "status": "running",
        "modules": modules
    })


# PROCESS UPLOADED NASA IMAGE
@app.route("/api/process", methods=["POST"])
def process_image():

    if "image" not in request.files:
        return jsonify({
            "error": "Please upload an image."
        }), 400

    image = request.files["image"]

    if image.filename == "":
        return jsonify({
            "error": "No image selected."
        }), 400

    allowed_extensions = {"png", "jpg", "jpeg"}

    extension = image.filename.rsplit(".", 1)[-1].lower()

    if extension not in allowed_extensions:
        return jsonify({
            "error": "Only PNG and JPG images are supported."
        }), 400

    image_bytes = image.read()

    if not image_bytes:
        return jsonify({
            "error": "The uploaded image is empty."
        }), 400

    try:

        # Load the NASA scientific colour legend
        legend_file = BASE_DIR / "nasa_legend.csv"

        # Run the existing team backend
        with pipeline_lock:

            original_dir = integration_adapter.CURRENT_DIR

            try:
                # Vercel allows temporary files in /tmp
                integration_adapter.CURRENT_DIR = Path("/tmp")

                results = integration_adapter.run_full_pipeline(
                    source_type="image",
                    input_data=image_bytes,
                    legend_path=legend_file,
                    include_low_confidence=True,
                    embed_metadata=True
                )

            finally:
                # Restore the original backend directory
                integration_adapter.CURRENT_DIR = original_dir

        # Get processed windspeed records and audio
        records = results["records"]
        wav_bytes = results["wav_bytes"]

        # Convert audio to Base64 for the React frontend
        audio_base64 = base64.b64encode(
            wav_bytes
        ).decode("utf-8")

        # Extract windspeed values
        values = [
            record["windspeed_mps"]
            for record in records
        ]

        return jsonify({
            "success": True,
            "audio": audio_base64,
            "values": values,
            "unit": "m/s",
            "description": "Windspeed values extracted from your NASA image.",
            "stats": results["stats"],
            "warnings": results["warnings"]
        })

    except Exception as error:

        app.logger.exception("Image processing failed")

        return jsonify({
            "error": "Processing failed: " + str(error)
        }), 500


# HANDLE LARGE UPLOADS
@app.errorhandler(413)
def file_too_large(error):

    return jsonify({
        "error": "Image is too large. Please upload an image smaller than 4 MB."
    }), 413


# RUN LOCALLY
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)

