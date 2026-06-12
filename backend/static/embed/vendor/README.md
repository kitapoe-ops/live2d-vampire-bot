# vendor/ — Self-hosted 3rd-party JS

**目的：** Bypass mobile browser Tracking Prevention (Safari ITP / Brave ETP / Firefox ETP)
對 3rd-party CDN storage access 嘅 block，確保 PIXI init 唔會 silent fail。

之前路徑：
- `https://cubism.live2d.com/sdk-web/cubismcore/live2dcubismcore.min.js`
- `https://cdn.jsdelivr.net/npm/pixi.js@6.5.10/dist/browser/pixi.min.js`
- `https://cdn.jsdelivr.net/npm/pixi-live2d-display@0.4.0/dist/cubism4.min.js`

而家路徑：1st-party（從 `vampire.kitahim.uk/static/embed/vendor/` serve）。

## Files

| File | Size | License | Source |
|------|------|---------|--------|
| `pixi.min.js` | 449.5 KB | MIT | https://cdn.jsdelivr.net/npm/pixi.js@6.5.10/dist/browser/pixi.min.js |
| `cubism4.min.js` | 117.1 KB | MIT | https://cdn.jsdelivr.net/npm/pixi-live2d-display@0.4.0/dist/cubism4.min.js |
| `live2dcubismcore.min.js` | 202.3 KB | **Live2D Proprietary** | https://cubism.live2d.com/sdk-web/cubismcore/live2dcubismcore.min.js |

**Total:** 769 KB

## License Notes

### pixi.js + pixi-live2d-display
Both MIT licensed. Self-hosting 完全冇 issue。可任意再散佈。

### Live2D Cubism Core SDK
**Proprietary** (non-open-source)。Live2D 官方只授權透過佢哋個 CDN 引用。
Self-hosting 喺自己 server 算 redistribution，可能違反 Live2D Proprietary License。

**我哋嘅 posture:**
- Demo / personal / non-commercial use = 灰區，acceptable for own hosting
- 如要正式 production commercial 部署：
  - Option A: 維持由 `cubism.live2d.com` 引用（保留官方授權）
  - Option B: 申請 Live2D 商業授權後再 self-host
  - Option C: 等待 Live2D 開放 Core SDK 嘅 permissive license

## Update Procedure

要 update 時：
1. 喺 production server 重新 curl 落新 version
2. 改 widget.html `<script src="vendor/...">` path（如有 file name 變）
3. Bump `_buildV` 喺 embed.js
4. 測試 widget render OK
5. (Optional) git commit
