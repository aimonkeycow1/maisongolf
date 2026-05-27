import json
import os
from datetime import datetime

from courses import DEFAULT_COURSE_ID, DEFAULT_TEE_ID, course_meta_for_round

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


def build_round_record(players_stats, note="", course_id=None, tee_id=None, user_email=None):
    now = datetime.now()
    cid = course_id or DEFAULT_COURSE_ID
    tid = tee_id or DEFAULT_TEE_ID
    meta = course_meta_for_round(cid, tid)
    if not meta:
        meta = course_meta_for_round(DEFAULT_COURSE_ID, DEFAULT_TEE_ID)

    record = {
        "id": now.strftime("%Y%m%d_%H%M%S"),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M"),
        "course_id": meta["course_id"],
        "course": meta["course"],
        "tee_id": meta["tee_id"],
        "tee": meta["tee"],
        "par_total": meta["par_total"],
        "yardage_total": meta["yardage_total"],
        "pars": meta["pars"],
        "note": note.strip(),
        "players": players_stats,
    }
    if user_email:
        record["user_email"] = user_email
    return record


def add_round(players_stats, note="", course_id=None, tee_id=None, user_email=None):
    rounds = load_rounds()
    rounds.append(build_round_record(players_stats, note, course_id, tee_id, user_email=user_email))
    save_rounds(rounds)
    return rounds[-1]["id"]

