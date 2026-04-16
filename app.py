import os
import subprocess
import uuid
from datetime import datetime
from email.message import EmailMessage
import smtplib

from flask import Flask, jsonify, render_template, request, send_file
from PIL import Image, ImageEnhance, ImageOps, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "captures")
ASSET_DIR = os.path.join(BASE_DIR, "assets")
STEVE_IMAGE = os.path.join(ASSET_DIR, "Steve.jpg")
FRAME_IMAGE = os.path.join(ASSET_DIR, "Frame.jpg")

os.makedirs(OUTPUT_DIR, exist_ok=True)

app = Flask(__name__)


def _timestamp_id():
    return datetime.utcnow().strftime("%Y%m%d%H%M%S") + "-" + str(uuid.uuid4())[:6]


def _run_camera_capture(filepath):
    cmd = [
        "gphoto2",
        "--capture-image-and-download",
        "--filename",
        filepath,
        "--force-overwrite",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "Camera capture failed")


def _run_preview_capture(filepath):
    cmd = ["gphoto2", "--capture-preview", "--filename", filepath, "--force-overwrite"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "Preview capture failed")


def apply_watermark(source, destination):
    with Image.open(source).convert("RGB") as image:
        draw = ImageDraw.Draw(image)
        text = os.environ.get("WATERMARK_TEXT", "50thCAM")
        font_size = max(28, int(image.width * 0.035))
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", font_size)
        except OSError:
            font = ImageFont.load_default()
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_w = text_bbox[2] - text_bbox[0]
        text_h = text_bbox[3] - text_bbox[1]
        x = image.width - text_w - 30
        y = image.height - text_h - 30
        draw.rectangle((x - 20, y - 12, x + text_w + 20, y + text_h + 12), fill=(0, 0, 0, 145))
        draw.text((x, y), text, font=font, fill=(255, 255, 255))
        image.save(destination, "JPEG", quality=95)


def apply_1976_filter(source, destination):
    with Image.open(source).convert("RGB") as image:
        sepia = ImageOps.colorize(ImageOps.grayscale(image), "#3e2f1c", "#f9e3a1")
        contrast = ImageEnhance.Contrast(sepia).enhance(1.2)
        color = ImageEnhance.Color(contrast).enhance(1.15)
        final = ImageEnhance.Brightness(color).enhance(1.05)
        final.save(destination, "JPEG", quality=95)


def _cover_fit(source, size):
    src_w, src_h = source.size
    dst_w, dst_h = size
    ratio = max(float(dst_w) / src_w, float(dst_h) / src_h)
    resized = source.resize((int(src_w * ratio), int(src_h * ratio)), Image.Resampling.LANCZOS)
    left = max(0, (resized.width - dst_w) // 2)
    top = max(0, (resized.height - dst_h) // 2)
    return resized.crop((left, top, left + dst_w, top + dst_h))


def create_social_image(filtered_source, destination):
    canvas_size = (2868, 1320)
    panel_w = canvas_size[0] // 2

    with Image.new("RGB", canvas_size, "black") as canvas:
        with Image.open(filtered_source).convert("RGB") as filtered_img:
            left_panel = _cover_fit(filtered_img, (panel_w, canvas_size[1]))
            canvas.paste(left_panel, (0, 0))

        if os.path.exists(STEVE_IMAGE):
            with Image.open(STEVE_IMAGE).convert("RGB") as steve_img:
                right_panel = _cover_fit(steve_img, (canvas_size[0] - panel_w, canvas_size[1]))
                canvas.paste(right_panel, (panel_w, 0))

        if os.path.exists(FRAME_IMAGE):
            with Image.open(FRAME_IMAGE).convert("RGBA") as frame_img:
                frame = _cover_fit(frame_img, canvas_size)
                canvas_rgba = canvas.convert("RGBA")
                canvas_rgba.alpha_composite(frame)
                canvas = canvas_rgba.convert("RGB")

        canvas.save(destination, "JPEG", quality=95)


def process_capture(original_path):
    file_id = os.path.basename(original_path).replace("original-", "").replace(".jpg", "")
    watermarked = os.path.join(OUTPUT_DIR, "originalW-%s.jpg" % file_id)
    filtered = os.path.join(OUTPUT_DIR, "1976edition-%s.jpg" % file_id)
    social = os.path.join(OUTPUT_DIR, "social-%s.jpg" % file_id)

    apply_watermark(original_path, watermarked)
    apply_1976_filter(watermarked, filtered)
    create_social_image(filtered, social)

    return {
        "id": file_id,
        "original": os.path.basename(original_path),
        "watermarked": os.path.basename(watermarked),
        "filtered": os.path.basename(filtered),
        "social": os.path.basename(social),
    }


def _send_email(name, recipient, files):
    host = os.environ.get("SMTP_HOST")
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASS")
    sender = os.environ.get("MAIL_FROM", user)

    if not host or not sender:
        raise RuntimeError("Email is not configured. Set SMTP_HOST and MAIL_FROM/SMTP_USER.")

    msg = EmailMessage()
    msg["Subject"] = "Your 50thCAM photos"
    msg["From"] = sender
    msg["To"] = recipient
    msg.set_content("Hi %s,\n\nHere are your photos from 50thCAM.\n" % name)

    for file_path in files:
        with open(file_path, "rb") as fh:
            data = fh.read()
        msg.add_attachment(data, maintype="image", subtype="jpeg", filename=os.path.basename(file_path))

    with smtplib.SMTP(host, port, timeout=30) as server:
        server.starttls()
        if user and password:
            server.login(user, password)
        server.send_message(msg)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/preview.jpg")
def preview():
    preview_file = os.path.join(OUTPUT_DIR, "preview.jpg")
    try:
        _run_preview_capture(preview_file)
        return send_file(preview_file, mimetype="image/jpeg")
    except Exception:
        fallback = Image.new("RGB", (640, 480), color=(30, 30, 30))
        draw = ImageDraw.Draw(fallback)
        draw.text((20, 220), "Camera preview unavailable", fill=(255, 255, 255))
        fallback.save(preview_file, "JPEG", quality=85)
        return send_file(preview_file, mimetype="image/jpeg")


@app.route("/api/capture", methods=["POST"])
def capture():
    file_id = _timestamp_id()
    original = os.path.join(OUTPUT_DIR, "original-%s.jpg" % file_id)
    try:
        _run_camera_capture(original)
        result = process_capture(original)
        return jsonify({"ok": True, "images": result})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.route("/captures/<path:filename>")
def file(filename):
    return send_file(os.path.join(OUTPUT_DIR, filename), mimetype="image/jpeg")


@app.route("/api/send", methods=["POST"])
def send_email():
    payload = request.get_json(force=True, silent=True) or {}
    name = (payload.get("name") or "").strip()
    email = (payload.get("email") or "").strip()
    image_id = (payload.get("image_id") or "").strip()

    if not name or not email or not image_id:
        return jsonify({"ok": False, "error": "Name, email, and image_id are required."}), 400

    files = [
        os.path.join(OUTPUT_DIR, "originalW-%s.jpg" % image_id),
        os.path.join(OUTPUT_DIR, "1976edition-%s.jpg" % image_id),
        os.path.join(OUTPUT_DIR, "social-%s.jpg" % image_id),
    ]

    for file_path in files:
        if not os.path.exists(file_path):
            return jsonify({"ok": False, "error": "Missing generated image files."}), 404

    try:
        _send_email(name, email, files)
        return jsonify({"ok": True})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")), debug=False)
