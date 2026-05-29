import time

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image, ImageDraw, ImageFont


load_dotenv()

scope = "user-read-currently-playing"

CACHE_PATH = "/home/ryan/Spotify-Now-Playing-Display/.spotify_token_cache"

sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        scope=scope,
        cache_path=CACHE_PATH,
        open_browser=False
    )
)

# ---------- Matrix setup ----------

options = RGBMatrixOptions()
options.rows = 32
options.cols = 64
options.chain_length = 1
options.parallel = 1
options.hardware_mapping = "adafruit-hat"
options.gpio_slowdown = 4

options.drop_privileges = False

matrix = RGBMatrix(options=options)

font = ImageFont.load_default()


# ---------- Spotify helpers ----------

def get_now_playing():
    current = sp.current_user_playing_track()

    if current is None or current["item"] is None:
        return None

    track = current["item"]

    artist_names = []
    for artist in track["artists"]:
        artist_names.append(artist["name"])

    return {
        "song": track["name"],
        "artist": ", ".join(artist_names),
        "progress_ms": current["progress_ms"],
        "duration_ms": track["duration_ms"],
        "is_playing": current["is_playing"],
        "fetched_at": time.time(),
    }


def get_live_progress_ms(now_playing):
    progress_ms = now_playing["progress_ms"]

    if now_playing["is_playing"]:
        elapsed_seconds = time.time() - now_playing["fetched_at"]
        progress_ms += int(elapsed_seconds * 1000)

    return min(progress_ms, now_playing["duration_ms"])


# ---------- Drawing helpers ----------

def draw_progress_bar(draw, progress_ms, duration_ms):
    if duration_ms <= 0:
        return

    bar_x = 2
    bar_y = 28
    bar_width = 60
    bar_height = 3

    ratio = progress_ms / duration_ms
    filled_width = int(bar_width * ratio)

    draw.rectangle(
        (bar_x, bar_y, bar_x + bar_width, bar_y + bar_height),
        outline=(40, 40, 40)
    )

    draw.rectangle(
        (bar_x, bar_y, bar_x + filled_width, bar_y + bar_height),
        fill=(0, 255, 180)
    )


def draw_matrix(now_playing, scroll_x):
    image = Image.new("RGB", (64, 32), (0, 0, 0))
    draw = ImageDraw.Draw(image)

    if now_playing is None:
        draw.text((2, 10), "NO MUSIC", font=font, fill=(255, 80, 80))
        matrix.SetImage(image)
        return scroll_x

    # Header
    draw.text((2, 1), "NOW PLAYING", font=font, fill=(255, 0, 140))

    # Scrolling song line
    song_line = now_playing["song"] + " - " + now_playing["artist"]
    text_width = draw.textlength(song_line, font=font)

    draw.text((scroll_x, 13), song_line, font=font, fill=(0, 200, 255))

    # Progress bar
    live_progress = get_live_progress_ms(now_playing)
    draw_progress_bar(draw, live_progress, now_playing["duration_ms"])

    matrix.SetImage(image)

    scroll_x -= 1

    if scroll_x < -text_width:
        scroll_x = 64

    return scroll_x


# ---------- Main loop ----------

now_playing = None
last_fetch_time = 0
scroll_x = 64

FETCH_INTERVAL_SECONDS = 5
FRAME_DELAY_SECONDS = 0.05

try:
    while True:
        current_time = time.time()

        if current_time - last_fetch_time > FETCH_INTERVAL_SECONDS:
            new_now_playing = get_now_playing()
            last_fetch_time = current_time

            if new_now_playing != now_playing:
                scroll_x = 64

            now_playing = new_now_playing

        scroll_x = draw_matrix(now_playing, scroll_x)

        time.sleep(FRAME_DELAY_SECONDS)

except KeyboardInterrupt:
    matrix.Clear()
    print("Stopped matrix display.")
