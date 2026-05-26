import json
import os
from datetime import datetime

from course_data import COURSE_NAME, PAR_TOTAL

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE = os.path.join(BASE_DIR, "rounds.json")

def load_rounds():
    try:
        with open(FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        print("⚠️ 紀錄檔損壞，將從空白開始。")
        return []

def save_rounds(rounds):
    with open(FILE, "w", encoding="utf-8") as file:
        json.dump(rounds, file, ensure_ascii=False, indent=2)

def build_round_record(players_stats, note=""):
    now = datetime.now()
    return {
        "id": now.strftime("%Y%m%d_%H%M%S"),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M"),
        "course": COURSE_NAME,
        "par_total": PAR_TOTAL,
        "tee": "白梯",
        "note": note.strip(),
        "players": players_stats,
    }

def add_round(players_stats, note=""):
    rounds = load_rounds()
    rounds.append(build_round_record(players_stats, note))
    save_rounds(rounds)
    return rounds[-1]["id"]
