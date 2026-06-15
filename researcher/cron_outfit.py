"""
researcher/cron_outfit.py
=========================
Cron-triggered research loop for live2d-fork outfit switching debug.
每 15 分鐘被 cron job 調用，選擇下一個未完成的 dimension，
spawn subagent 做調試，直到全部完成通知 user。

Usage (cron or manual):
    python researcher/cron_outfit.py
"""

import sys, os
from pathlib import Path

# Ensure workspace in path
sys.path.insert(0, str(Path(__file__).parent.parent))
os.chdir(Path(__file__).parent.parent)

from researcher.state import load, save, mark_dimension, all_complete, set_status
from datetime import datetime

WORKSPACE = Path(__file__).parent.parent
WIDGET_HTML = WORKSPACE / "backend" / "static" / "embed" / "widget.html"
DIST_WIDGET = WORKSPACE / "dist-pages" / "widget.html"


def build_subagent_brief(state) -> str:
    """Generate the subagent brief for the next pending dimension."""

    pending = [d for d in state["dimensions"] if not d["complete"]]
    if not pending:
        return None

    dim = pending[0]
    all_dims_desc = "\n".join(
        f"  [{'✅' if d['complete'] else '⬜'}] {d['name']}: {d['description']}"
        for d in state["dimensions"]
    )

    brief = f"""## live2d-fork 換裝 Debug 任務（迭代 #{state['iteration_count']}）

### 目標
修復 live2d-fork 換裝問題：點擊 outfit toggle button 無法切換 vampire（黑色）↔ vampire2（白色）服裝。

### 當前維度焦點
** [{dim['name']}] — {dim['description']}
Previous attempts: {dim['attempts']}

### 所有維度狀態
{all_dims_desc}

### 已知代碼背景
- `widget.html` 中的 `OUTFIT_PARAMS` 定義了 vampire/vampire2 的 6 個參數
- `applyOutfit(outfitName)` 調用 `safeSetParam()` 寫入每幀
- `restoreOutfitFromEmoteState()` 在 motion 結束後 restore outfit
- v50 新增了 per-frame PARAMoutfit1_2 diagnostic + window.testOutfit
- Part26/Part30 = 黑色服裝 parts；Part59 = nude body
- PARAMoutfit1_2 = 1.0 → vampire(黑), 0.0 → vampire2(白)

### 你的任務（使用 M2 Hand-off 模式）
1. 閱讀 `backend/static/embed/widget.html` 最新代碼
2. 檢查 `dist-pages/widget.html` 是否已部署（`vampire.kitahim.uk/widget`）
3. 對當前 dimension 提出假設 → 設計實驗 → 驗證
4. **如果找到 fix**：寫入 `dist-pages/widget.html`，commit，然後 **用 `message` tool 主動通知 user（`5443164620`）**
5. **更新 state.py**：mark_dimension() with findings
6. **如果 15 分鐘內無法完成**：寫入 state.py 所有進度，main agent 下一輪繼續
7. **如果全部完成**：set_status("resolved") + message 通知 user

### 嚴格限制
- 每個 subagent 最多 15 分鐘（mode="run" hard cap）
- 只改 `backend/static/embed/widget.html` + `dist-pages/widget.html`（兩個都要同步）
- 部署用 `wrangler pages deploy dist-pages --project-name vampire-widget`
- 永遠用 `message` tool 主動通知，唔好等 user 問

### 回報格式（subagent 最後一行）
```
[STATE UPDATE]
dimension: {dim['name']}
complete: true/false
confidence: High/Medium/Low
findings: <single line summary>
action_taken: <what you did>
next_lead: <if not resolved, what to try next>
```
"""
    return brief


def trigger_subagent(brief: str, iteration: int):
    """Spawn a subagent to work on the current dimension."""
    import subprocess, json

    # Use OpenClaw sessions_spawn via a small helper script
    # We write the brief to a temp file and signal main agent
    task_file = WORKSPACE / "researcher" / "next_task.txt"
    with open(task_file, "w", encoding="utf-8") as f:
        f.write(brief)

    safe_brief = brief[:200].replace('\u2194', '->').replace('\u2713', '[OK]').replace('\u2b25', '[ ]')
    print(f"[{datetime.now().isoformat()}] Spawning subagent for iteration #{iteration}")
    print(f"  Task file: {task_file}")
    print(f"  Brief preview: {safe_brief}...")

    # The actual spawning happens via the cron job's agentTurn payload
    # This script is called by cron and just prepares the brief
    return str(task_file)


def main():
    state = load()

    print(f"\n=== live2d_outfit Cron [{datetime.now().isoformat()}] ===")
    print(f"Iteration: #{state['iteration_count']}")
    print(f"Status: {state['status']}")

    if state["status"] == "resolved":
        print("Already resolved. Nothing to do.")
        return

    pending = [d for d in state["dimensions"] if not d["complete"]]
    if not pending:
        print("All dimensions complete! Marking resolved.")
        set_status("resolved")
        print("TODO: send Telegram notification to user")
        return

    dim = pending[0]
    print(f"Next dimension: [{dim['name']}] {dim['description']}")
    print(f"Previous attempts: {dim['attempts']}")

    brief = build_subagent_brief(state)
    task_file = trigger_subagent(brief, state["iteration_count"])

    print(f"\nBrief written to: {task_file}")
    print("Next cron will re-read state and continue.")


if __name__ == "__main__":
    main()
