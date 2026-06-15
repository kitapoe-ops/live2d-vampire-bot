"""
researcher/state.py — Outfit Switch Debug Research State
=========================================================
Goal: 修復 live2d-fork 換裝問題（Part26/Part30 黑色服裝無法切換）
"""

import json, os, sys
from pathlib import Path

STATE_FILE = Path(__file__).parent / "state.json"

DEFAULT_STATE = {
    "id": "live2d_outfit",
    "goal": "修復 live2d-fork 換裝問題（vampire/vampire2 切換，Part26/30 黑色服裝）",
    "project": "live2d-fork",
    "interval_minutes": 15,
    "dimensions": [
        {
            "name": "HYSTERESIS",
            "description": "化妝/表情切換後服裝參數被覆蓋",
            "complete": False,
            "confidence": None,
            "findings": None,
            "attempts": []
        },
        {
            "name": "PART_INVISIBILITY",
            "description": "黑色服裝 Part26/30 為看不見（opacity=0）",
            "complete": False,
            "confidence": None,
            "findings": None,
            "attempts": []
        },
        {
            "name": "MOTION_RESET",
            "description": "任何 motion 播放後服裝被重置為默認（白色）",
            "complete": False,
            "confidence": None,
            "findings": None,
            "attempts": []
        },
        {
            "name": "PARAM_DRIFT",
            "description": "每幀 render loop 中 PARAMoutfit1_2 值飄移",
            "complete": False,
            "confidence": None,
            "findings": None,
            "attempts": []
        },
        {
            "name": "EMOTION_CONFLICT",
            "description": "applyEmotion() 與 applyOutfit() 參數衝突",
            "complete": False,
            "confidence": None,
            "findings": None,
            "attempts": []
        },
    ],
    "completed_dimensions": [],
    "last_action": None,
    "last_review": None,
    "iteration_count": 0,
    "cron_id": None,
    "status": "in_progress"  # in_progress | resolved | blocked
}

def load():
    if not STATE_FILE.exists():
        return DEFAULT_STATE.copy()
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def mark_dimension(name, complete, confidence, findings, action):
    state = load()
    for dim in state["dimensions"]:
        if dim["name"] == name:
            dim["complete"] = complete
            dim["confidence"] = confidence
            dim["findings"] = findings
            dim["attempts"].append(action)
            break
    state["last_action"] = action
    state["last_review"] = __import__("datetime").datetime.now().isoformat()
    state["iteration_count"] += 1
    save(state)
    return state

def all_complete():
    state = load()
    return all(d["complete"] for d in state["dimensions"])

def set_status(status):
    state = load()
    state["status"] = status
    save(state)

def set_cron_id(cron_id):
    state = load()
    state["cron_id"] = cron_id
    save(state)
