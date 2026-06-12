import os
import re

path = 'backend/static/embed/widget.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update CSS selectors by replacing them one by one
css_replacements = [
    ("#voice-list {", "#voice-list, #emote-list {"),
    ("#voice-list.open {", "#voice-list.open, #emote-list.open {"),
    ("#voice-list .vl-header {", "#voice-list .vl-header, #emote-list .vl-header {"),
    ("#voice-list .vl-empty {", "#voice-list .vl-empty, #emote-list .vl-empty {"),
    ("#voice-list .vl-item {", "#voice-list .vl-item, #emote-list .vl-item {"),
    ("#voice-list .vl-item:hover {", "#voice-list .vl-item:hover, #emote-list .vl-item:hover {"),
    ("#voice-list .vl-item.active {", "#voice-list .vl-item.active, #emote-list .vl-item.active {"),
    ("#voice-list .vl-item .vl-name {", "#voice-list .vl-item .vl-name, #emote-list .vl-item .vl-name {"),
    ("#voice-list .vl-item .vl-id {", "#voice-list .vl-item .vl-id, #emote-list .vl-item .vl-id {"),
    ("#voice-list .vl-item.active .vl-id {", "#voice-list .vl-item.active .vl-id, #emote-list .vl-item.active .vl-id {"),
    ("#voice-list .vl-section {", "#voice-list .vl-section, #emote-list .vl-section {")
]

for old, new in css_replacements:
    # Try with different indentations
    if old in content:
        content = content.replace(old, new)
        print(f"CSS replaced: {old}")
    else:
        # Try finding with spaces
        found = False
        for indent in ["  ", "    ", "      "]:
            indented_old = indent + old
            indented_new = indent + new
            if indented_old in content:
                content = content.replace(indented_old, indented_new)
                print(f"CSS replaced (indented): {old}")
                found = True
                break
        if not found:
            print(f"CSS WARNING: {old} not found!")

# 2. Update HTML
html_target = 'id="voice-list" role="listbox"'
if html_target in content:
    lines = content.splitlines()
    for idx, line in enumerate(lines):
        if html_target in line:
            indent = line[:len(line) - len(line.lstrip())]
            lines[idx] = line + "\n" + indent + '<div id="emote-list" role="listbox" aria-label="表情選擇"></div>'
            print("HTML replaced successfully.")
            break
    content = "\n".join(lines)
else:
    print("HTML ERROR: voice-list container not found.")

# 3. Add Canvas Click reaction
canvas_target = "canvasEl.addEventListener('pointermove'"
if canvas_target in content:
    lines = content.splitlines()
    found_idx = -1
    for idx, line in enumerate(lines):
        if canvas_target in line:
            found_idx = idx
            break
    if found_idx != -1:
        # Find the next });
        end_idx = -1
        for j in range(found_idx, found_idx + 10):
            if '});' in lines[j]:
                end_idx = j
                break
        if end_idx != -1:
            indent = lines[found_idx][:len(lines[found_idx]) - len(lines[found_idx].lstrip())]
            click_code = (
                f"\n{indent}canvasEl.addEventListener('click', () => {{\n"
                f"{indent}  if (model && typeof model.motion === 'function') {{\n"
                f"{indent}    try {{\n"
                f"{indent}      model.motion('Scene1');\n"
                f"{indent}      console.log('[Live2D] Play clicked reaction motion: Scene1');\n"
                f"{indent}    }} catch (e) {{\n"
                f"{indent}      console.warn('[Live2D] Failed to play Scene1 motion:', e);\n"
                f"{indent}    }}\n"
                f"{indent}  }}\n"
                f"{indent}}});"
            )
            lines[end_idx] = lines[end_idx] + click_code
            print("Canvas click code inserted successfully.")
            content = "\n".join(lines)
        else:
            print("Canvas click error: closing pointermove listener not found.")
else:
    print("Canvas click error: pointermove listener not found.")

# 4. Update Ticker (Dynamic sway on speak)
ticker_search = "PARAM_BODY_ANGLE_X"
if ticker_search in content:
    lines = content.splitlines()
    found_idx = -1
    for idx, line in enumerate(lines):
        if ticker_search in line and 'bodySwayX' in line:
            found_idx = idx
            break
    if found_idx != -1:
        start_line = found_idx
        # Let's search upwards for the comment // 身體晃動
        if '身體晃動' in lines[found_idx - 1]:
            start_line = found_idx - 1
            
        end_line = -1
        for j in range(found_idx, found_idx + 8):
            if "PARAM_BODY_ANGLE_Y" in lines[j] and "safeSetParam" in lines[j]:
                end_line = j
                break
        if end_line != -1:
            indent = lines[found_idx][:len(lines[found_idx]) - len(lines[found_idx].lstrip())]
            replacement_code = (
                f"{indent}// 身體與肩膀晃動 (PARAM_BODY_ANGLE_X/Y/Z, PARAM_shoulder)\n"
                f"{indent}let bodySwayX = Math.sin(t * 0.4) * 2.5;\n"
                f"{indent}let bodySwayY = Math.cos(t * 0.3) * 1.5;\n"
                f"{indent}if (isSpeaking) {{\n"
                f"{indent}  // 說話時增加晃動幅度和頻率，讓身體顯得生動\n"
                f"{indent}  bodySwayX += Math.sin(t * 3.0) * 3.5;\n"
                f"{indent}  bodySwayY += Math.cos(t * 2.5) * 2.0;\n"
                f"{indent}  safeSetParam('PARAM_BODY_ANGLE_Z', Math.sin(t * 2.0) * 2.0);\n"
                f"{indent}  safeSetParam('PARAM_shoulder', Math.sin(t * 4.0) * 3.5);\n"
                f"{indent}}} else {{\n"
                f"{indent}  safeSetParam('PARAM_BODY_ANGLE_Z', 0.0);\n"
                f"{indent}  safeSetParam('PARAM_shoulder', 0.0);\n"
                f"{indent}}}\n"
                f"{indent}safeSetParam('PARAM_BODY_ANGLE_X', bodySwayX);\n"
                f"{indent}safeSetParam('PARAM_BODY_ANGLE_Y', bodySwayY);"
            )
            # Replace lines from start_line to end_line
            new_lines = lines[:start_line] + [replacement_code] + lines[end_line+1:]
            print("Ticker sway code inserted successfully.")
            content = "\n".join(new_lines)
        else:
            print("Ticker error: safeSetParam PARAM_BODY_ANGLE_Y not found.")
    else:
        print("Ticker error: PARAM_BODY_ANGLE_X set line not found.")
else:
    print("Ticker error: PARAM_BODY_ANGLE_X not found.")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("WRITE DONE!")
