# 🌐 Vampire Live2D Deployment Spec — kitahim.uk

> **最後更新：** 2026-06-11
> **Host：** BAZOOKA (Windows NT 10.0.26200, 16GB+ RAM, GPU)
> **Backend：** FastAPI 0.135.2 + uvicorn 0.41.0
> **Tunnel：** cloudflared 2026.5.2 (running, PID 6844)
> **Domain：** kitahim.uk (Cloudflare managed)

---

## 1. 架構藍圖

```
[Browser / VTube Studio / PixiJS client]
         │
         │ wss://vampire.kitahim.uk
         ▼
[Cloudflare Edge (free CDN + DDoS protection)]
         │
         │ Cloudflare Tunnel (encrypted, outbound-only)
         ▼
[cloudflared daemon on BAZOOKA (PID 6844)]
         │
         │ localhost:8000
         ▼
[FastAPI backend (uvicorn)]
         │
         ├─ GET  /                          Service info
         ├─ GET  /health                    Health + telemetry
         ├─ GET  /api/v1/models             List all deployed models
         ├─ GET  /api/v1/models/{name}      Get one model metadata
         ├─ GET  /api/v1/auth/ticket        Issue auth ticket
         ├─ WS   /api/v1/live2d/control     60 FPS parameter push
         └─ GET  /static/live2d/{model}/... Static model assets
```

**核心安全特性：**
- Outbound-only tunnel（BAZOOKA 唔需要開 inbound port）
- HTTPS 自動（Cloudflare 提供 certificate）
- DDoS 防護（Cloudflare 默認）
- 60 FPS WebSocket 支援（Cloudflare 接受 WebSocket）
- Ticket-based auth（1 hour expiry）
- Per-IP connection limit（1 條 stream per IP）

---

## 2. File Layout（deployment-ready）

```
C:\Users\kitap\.openclaw\workspace\live2d_xiaob\
├── backend\
│   ├── app.py                          # Vanilla FastAPI (~9 KB, 11 routes)
│   └── static\
│       └── live2d\
│           └── vampire\                # Symlink OR copy of model assets
│               ├── 吸血鬼.moc3         (6.83 MB)
│               ├── 吸血鬼.2048\        (4 texture_*.png, 4.38 MB)
│               ├── 吸血鬼.model3.json
│               ├── 吸血鬼.physics3.json
│               ├── 吸血鬼.cdi3.json
│               ├── 吸血鬼.vtube.json
│               └── *.exp3.json         (12 emotion expressions)
├── docs\
│   └── deployment_spec.md              # This file
├── scripts\
│   ├── Check_Encoding.py
│   ├── Verify_Vampire_Model.py
│   ├── Optimize_Vampire_Textures.py
│   └── Patch_Vampire_Model_References.py
└── vampire\                            # SOURCE-OF-TRUTH model folder
    └── vampire_vts\                    # 25 files, 11.47 MB
        └── (same content as backend\static\live2d\vampire\)
```

**Note:** `vampire/` 係 source-of-truth，`backend/static/live2d/vampire/` 係 deployment copy。改 source 後要 re-sync（見 Step 4）。

---

## 3. Deployment Scenarios

### Scenario B（新開 named tunnel `vampire-bot`，**推薦**）

```powershell
# 1. Create tunnel (one-time)
& "C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel create vampire-bot

# 2. Capture TUNNEL_ID from output, create config
$configPath = "$env:USERPROFILE\.cloudflared\vampire-bot-config.yml"
$tunnelId = Read-Host "Paste TUNNEL_ID from step 1"
@"
tunnel: $tunnelId
credentials-file: C:\Users\$env:USERNAME\.cloudflared\$tunnelId.json

ingress:
  - hostname: vampire.kitahim.uk
    service: http://localhost:8000
  - service: http_status:404
"@ | Out-File -FilePath $configPath -Encoding utf8

# 3. Create DNS record
& "C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel route dns vampire-bot vampire.kitahim.uk

# 4. Test
& "C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel --config $configPath run vampire-bot

# 5. (After verifying) Install as service
& "C:\Program Files (x86)\cloudflared\cloudflared.exe" service install
& "C:\Program Files (x86)\cloudflared\cloudflared.exe" service install --config $configPath
```

---

## 4. Sync Model to Backend Static

每次 source-of-truth 改咗，要 re-sync：

```powershell
$src = "C:\Users\kitap\.openclaw\workspace\live2d_xiaob\vampire\vampire_vts"
$dst = "C:\Users\kitap\.openclaw\workspace\live2d_xiaob\backend\static\live2d\vampire"

# Clear dst
if (Test-Path $dst) { Remove-Item $dst -Recurse -Force }
New-Item -ItemType Directory -Path $dst -Force | Out-Null

# Copy all files + subdirs
Get-ChildItem $src -File | Copy-Item -Destination $dst -Force
foreach ($sub in Get-ChildItem $src -Directory) {
    $subDst = "$dst\$($sub.Name)"
    New-Item -ItemType Directory -Path $subDst -Force | Out-Null
    Get-ChildItem $sub.FullName -File | Copy-Item -Destination $subDst -Force
}

# Audit
$total = (Get-ChildItem $dst -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB
Write-Host "Synced $total MB to $dst"
```

---

## 5. Backend Service 化（NSSM）

```powershell
$nssm = "C:\Tools\nssm\nssm.exe"   # Download from https://nssm.cc if missing
$python = (Get-Command python).Source
$appDir = "C:\Users\kitap\.openclaw\workspace\live2d_xiaob\backend"
$appPy = "$appDir\app.py"
$logDir = "C:\Users\kitap\.openclaw\logs"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }

& $nssm install BAZOOKAVampireBackend $python $appPy
& $nssm set BAZOOKAVampireBackend AppDirectory $appDir
& $nssm set BAZOOKAVampireBackend AppStdout "$logDir\vampire_backend.log"
& $nssm set BAZOOKAVampireBackend AppStderr "$logDir\vampire_backend_error.log"
& $nssm set BAZOOKAVampireBackend AppRotateFiles 1
& $nssm set BAZOOKAVampireBackend AppRotateBytes 10485760
& $nssm set BAZOOKAVampireBackend Start SERVICE_AUTO_START

# Start
& $nssm start BAZOOKAVampireBackend
Get-Service BAZOOKAVampireBackend
```

---

## 6. End-to-End Test

```powershell
# Local health
curl http://localhost:8000/health
# Expected: {"status":"healthy", "uptime_sec":...}

# List models
curl http://localhost:8000/api/v1/models
# Expected: {"models":[{"name":"vampire","path":"/static/live2d/vampire/",...}]}

# Get ticket
$ticket = (curl http://localhost:8000/api/v1/auth/ticket).ticket

# Static asset (use URL-encoded 吸血鬼)
curl http://localhost:8000/static/live2d/vampire/%E5%90%B8%E8%A1%80%E9%AC%BC.model3.json
# Expected: Cubism 3 JSON with FileReferences

# WebSocket test (use wscat or browser)
# ws://localhost:8000/api/v1/live2d/control?token=***&model=vampire

# After Cloudflare tunnel up:
curl https://vampire.kitahim.uk/health
```

---

## 7. Cloudflare Access（可選）

喺 Cloudflare Dashboard → Zero Trust → Access：
1. Add Application → Self-hosted
2. Application domain: `vampire.kitahim.uk`
3. Policy: Email OTP, allow only your email
4. 防止陌生人 access

---

## 8. Endpoints Quick Reference

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Service info |
| GET | `/health` | Health + telemetry |
| GET | `/api/v1/models` | List deployed models |
| GET | `/api/v1/models/{name}` | Get model metadata |
| GET | `/api/v1/auth/ticket` | Issue 1hr auth ticket |
| WS | `/api/v1/live2d/control?token=&model=` | 60 FPS parameter push |
| GET | `/static/live2d/{model}/...` | Model assets (read-only) |

---

## 9. 預計時間表

| Step | 時間 |
|------|------|
| Create Cloudflare tunnel | 2 min |
| DNS record | 1 min |
| Backend service install | 2 min |
| Sync model to static | 30 sec |
| End-to-end test | 3 min |
| **Total** | **~8 min** |

---

## 10. Rollback Plan

```powershell
# Stop service
nssm stop BAZOOKAVampireBackend
nssm remove BAZOOKAVampireBackend confirm

# Stop tunnel
& "C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel stop vampire-bot
& "C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel delete vampire-bot

# DNS cleanup via Cloudflare Dashboard
```

---

*最後更新：2026-06-11*
