"""Daily challenge: one seeded deck per UTC day, with personal-best tracking."""
import datetime
import hashlib
import random


def today_seed() -> int:
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    h = hashlib.sha256(("declare-daily-" + today).encode("utf-8")).hexdigest()
    return int(h[:16], 16)


def today_label() -> str:
    return datetime.datetime.utcnow().strftime("%Y-%m-%d")


def daily_rng():
    return random.Random(today_seed())


def is_new_day(profile):
    last = profile.last_match_config.get("daily_label", "")
    return last != today_label()


def record_daily_attempt(profile, score, won):
    profile.last_match_config["daily_label"] = today_label()
    bests = profile.last_match_config.setdefault("daily_bests", {})
    label = today_label()
    prev = bests.get(label)
    if won and (prev is None or score < prev):
        bests[label] = score
        return True
    return False
