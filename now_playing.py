import os
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

load_dotenv()

scope = "user-read-currently-playing"

sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(scope=scope)
)


def format_time(ms):
    total_seconds = ms // 1000
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes}:{seconds:02}"


def make_progress_bar(progress_ms, duration_ms, bar_length=30):
    if duration_ms == 0:
        return f"[{('-' * bar_length)}]"
    ratio = progress_ms / duration_ms
    filled_length = int(ratio * bar_length)
    empty_length = bar_length - filled_length

    bar = "█" * filled_length + "-" * empty_length
    return f"[{bar}]"

def get_now_playing():
    current = sp.current_user_playing_track()

    if current is None or current["item"] is None:
        return None

    track = current["item"]

    song_name = track["name"]
    album_name = track["album"]["name"]
    progress_ms = current["progress_ms"]
    duration_ms = track["duration_ms"]
    is_playing = current["is_playing"]

    artist_names = []

    for artist in track["artists"]:
        artist_names.append(artist["name"])

    artist_string = ", ".join(artist_names)

    return {
        "song": song_name,
        "artist": artist_string,
        "album": album_name,
        "progress_ms": progress_ms,
        "duration_ms": duration_ms,
        "is_playing": is_playing,
    }

def display_now_playing(now_playing):
    os.system("clear")

    if now_playing is None:
        print("Nothing is currently playing.")
        return

    progress_bar = make_progress_bar(
        now_playing["progress_ms"],
        now_playing["duration_ms"]
    )

    current_time = format_time(now_playing["progress_ms"])
    total_time = format_time(now_playing["duration_ms"])

    if now_playing["is_playing"]:
        status = "Playing"
    else:
        status = "Paused"

    print("Now Playing")
    print(now_playing["song"])
    print(now_playing["artist"])
    print(now_playing["album"])
    print()
    print(f"{progress_bar} {current_time} / {total_time}")
    print(status)


while True:
    display_now_playing(get_now_playing())
    time.sleep(1)