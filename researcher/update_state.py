import json
from pathlib import Path

STATE_FILE = Path(__file__).parent / "state.json"

state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
print("Current status:", state["status"])
print("Dimensions:")
for d in state["dimensions"]:
    print(f"  [{('Y' if d['complete'] else ' ')}] {d['name']}: {d['description']}")

# Mark HYSTERESIS
for dim in state["dimensions"]:
    if dim["name"] == "HYSTERESIS":
        dim["complete"] = True
        dim["confidence"] = "Medium"
        dim["findings"] = "model.expression() in applyEmotion() could override PARAMoutfit1_2; fix adds applyOutfit() sync call after expression to re-assert outfit params"
        dim["attempts"].append({
            "commit": "047ef52",
            "fix": "applyOutfit(emoteState.outfit) added after model.expression() in applyEmotion()",
            "confidence": "Medium"
        })
        break

state["last_action"] = "v53: applyOutfit after model.expression() to prevent HYSTERESIS"
state["last_review"] = "2026-06-15T10:34:00"
state["iteration_count"] += 1

STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
print("\nUpdated state saved.")
print("\nNew dimension state:")
for d in state["dimensions"]:
    print(f"  [{('Y' if d['complete'] else ' ')}] {d['name']}: confidence={d['confidence']}")
