import os

def patch_file(path, logger=print):
    if not os.path.exists(path):
        logger(f"SKIP: {path}")
        return
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    original = content

    # Fix 1: applyOutfit — add Part59 after cache invalidation
    OLD_AO = """        // Invalidate v22 per-frame write cache for outfit params so the next
        // RAF always writes fresh (v22Set would otherwise skip if value unchanged).
        if (typeof __v22_lastValue !== 'undefined' && __v22_lastValue) {
          for (const k of ['PARAMoutfit1_2', 'PARAMhariWB', 'PARAMhariWB2', 'PARAMhari_7', 'PARAMhari_8', 'PARAMhari_3']) {
            __v22_lastValue[k] = undefined;
          }
        }
      }"""

    NEW_AO = """        // Invalidate v22 per-frame write cache for outfit params so the next
        // RAF always writes fresh (v22Set would otherwise skip if value unchanged).
        if (typeof __v22_lastValue !== 'undefined' && __v22_lastValue) {
          for (const k of ['PARAMoutfit1_2', 'PARAMhariWB', 'PARAMhariWB2', 'PARAMhari_7', 'PARAMhari_8', 'PARAMhari_3']) {
            __v22_lastValue[k] = undefined;
          }
        }
        // 2026-06-15 v61 FIX: Part59 (nude body) management.
        // CDI3: Part59=1 dressed body (vampire), Part59=0 nude body (vampire2/white).
        // Idle.motion3.json sets Part59=1 every loop — must override on every applyOutfit call.
        try {
          const cm2 = model && model.internalModel && model.internalModel.coreModel;
          if (cm2) {
            const isVampire = (outfitName === 'vampire');
            const part59Op = isVampire ? 1.0 : 0.0;
            const part26Op = isVampire ? 1.0 : 0.0;
            const _setPart = function(pName, op) {
              try { if (typeof cm2.setPartOpacityById==='function') cm2.setPartOpacityById(pName, op); } catch(e){}
              try {
                const cnt = (typeof cm2.getPartCount==='function') ? cm2.getPartCount() : 60;
                for (let pi=0; pi<cnt; pi++) {
                  try { if (cm2.getPartId(pi)===pName) { cm2.setPartOpacity(pi, op); break; } } catch(e2){}
                }
              } catch(e3){}
            };
            _setPart('Part59', part59Op);
            _setPart('Part26', part26Op);
          }
        } catch(ePart59) {}
      }"""

    if OLD_AO in content:
        content = content.replace(OLD_AO, NEW_AO)
        logger(f"[1] applyOutfit Part59 fix OK")
    else:
        logger(f"[1] applyOutfit pattern NOT FOUND")

    # Fix 2: Per-frame loop — add Part59 every frame
    OLD_PF = """            for (const p of blackParts)  setPart(p, isBlack ? 1.0 : 0.0);
            for (const p of whiteParts) setPart(p, isBlack ? 0.0 : 1.0);
          } catch(e) {}
        });

        // v52 per-frame diagnostic"""

    NEW_PF = """            for (const p of blackParts)  setPart(p, isBlack ? 1.0 : 0.0);
            for (const p of whiteParts) setPart(p, isBlack ? 0.0 : 1.0);
            // 2026-06-15 v61: CRITICAL — Part59 (body) every frame.
            // Idle.motion3 sets Part59=1 every loop. For vampire2: Part59=0 = nude body.
            try {
              const part59Op = isBlack ? 1.0 : 0.0;
              const _sp59 = function(pName, op) {
                try { if (typeof cm.setPartOpacityById==='function') cm.setPartOpacityById(pName, op); } catch(e){}
                try {
                  const cnt = (typeof cm.getPartCount==='function') ? cm.getPartCount() : 60;
                  for (let pi=0; pi<cnt; pi++) {
                    try { if (cm.getPartId(pi)===pName) { cm.setPartOpacity(pi, op); break; } } catch(e2){}
                  }
                } catch(e3){}
              };
              _sp59('Part59', part59Op);
            } catch(ePart59) {}
          } catch(e) {}
        });

        // v52 per-frame diagnostic"""

    if OLD_PF in content:
        content = content.replace(OLD_PF, NEW_PF)
        logger(f"[2] per-frame Part59 fix OK")
    else:
        logger(f"[2] per-frame pattern NOT FOUND")

    if content != original:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger(f"[S] Saved: {os.path.basename(path)}")
    else:
        logger(f"[=] No changes: {os.path.basename(path)}")

if __name__ == '__main__':
    print("Patching Part59 fix (v61)...")
    patch_file(r"C:\Users\kitap\.openclaw\workspace\live2d-fork\backend\static\embed\widget.html")
    patch_file(r"C:\Users\kitap\.openclaw\workspace\live2d-fork\dist-pages\widget.html")
    print("Done.")