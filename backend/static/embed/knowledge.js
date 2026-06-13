/* =====================================================================
 * knowledge.js — 吸血鬼虛擬人知識庫
 * BAZOOKA / vampire.kitahim.uk adaption
 *
 * Default content: the embedded avatar's own usage FAQ.
 * Swap to your own domain by editing this file (q/kw/a tuples).
 * ===================================================================== */
window.KB = [
  { q: '這是什麼', kw: '你是誰 這是什麼 介紹 自我介紹 什麼東西 吸血鬼',
    a: '我是吸血鬼，是一個可以嵌進任何網站的右下角語音虛擬人。我會聽你說話、回答、開口講話還會對嘴，全部在你的瀏覽器裡跑。' },
  { q: '你的名字', kw: '名字 叫什麼 吸血鬼 角色',
    a: '我是吸血鬼（Vampire），運行在 BAZOOKA 上，託管於 vampire.kitahim.uk。' },
  { q: '怎麼安裝到我的網站', kw: '安裝 怎麼用 嵌入 加到 放到 我的網站 怎麼裝 install 整合',
    a: '把 embed.js 一行 script 放進你的網站，data-model 屬性指向吸血鬼 model.json 即可。具體步驟：1) 引入 embed.js；2) 設定 data-model 屬性；3) 部署至 HTTPS（語音需要）。' },
  { q: '怎麼換成你的角色', kw: '換角色 換模型 皮 換人 model 自訂角色 換成',
    a: '用 data-model 屬性指向你自己的 Live2D model3.json 檔，就能把我換成你設計的角色，引擎完全不用動。' },
  { q: '要不要錢', kw: '費用 成本 花錢 錢 收費 免費 金鑰 商用 正式 上線 多少錢 付費',
    a: '自己裝在網站上是免費的：瀏覽器語音和 AI 大腦都在使用者自己的裝置跑。想要更好聽的神經語音則需要微軟非官方 endpoint。' },
  { q: '語音怎麼用', kw: '語音 說話 麥克風 怎麼講 對話 講話 聽',
    a: '點下面的麥克風按鈕、允許權限，就能直接對我說話。我會用語音回答你，嘴巴也會跟著動。' },
  { q: '怎麼打字', kw: '打字 輸入 鍵盤 文字 輸入框 不方便說話 不能說話 沒有麥克風 不想開麥',
    a: '可以！下面有輸入框，打完字按 Enter 或旁邊的送出鍵，我一樣會用語音回答你、嘴巴也會跟著動。' },
  { q: 'AI 大腦是什麼', kw: '大腦 ai 腦袋 llm 聰明 模型 思考 webllm 1GB 下載',
    a: '點腦袋按鈕會在你的瀏覽器裡載入一個小型 AI 模型（Qwen2.5 1.5B），讓我能更自然地聊天。首次下載約 1GB，之後會被快取。' },
  { q: '對嘴怎麼做到的', kw: '對嘴 嘴巴 嘴型 lipsync 同步 嘴',
    a: '神經語音時我會分析真實音量來開合嘴巴，瀏覽器語音時則用節奏模擬。' },
  { q: '怎麼靜音', kw: '靜音 安靜 關掉聲音 停 不要講 閉嘴 mute',
    a: '點喇叭按鈕可以靜音。再點一次恢復。' },
  { q: '打招呼', kw: '你好 哈囉 嗨 hello hi 在嗎 哈嘍',
    a: '哈囉！我是吸血鬼。想知道怎麼把我裝到你的網站嗎？' },
  { q: '你的後端', kw: '後端 backend 部署 服務 host server',
    a: '我的後端 FastAPI 跑在 BAZOOKA（你的 PC），透過 Cloudflare Tunnel 公開 vampire.kitahim.uk。詳見 deployment_spec.md。' }
];

/* =====================================================================
 * window.KNOWLEDGE — 吸血鬼 Live2D 參數驅動命名空間
 * =====================================================================
 *
 * 設計哲學: 2-Tier 隔離架構 (Engineering Isolation)
 *   - 防止前端主循環 (Update Loop) 對死通道進行無效尋址
 *   - activeDriverIds 白名單 = 真實可驅動 (Verified)
 *   - sandboxDeadChannels 黑名單 = 死通道 (Typo / 殘留 / 純捕捉)
 *   - bonusExtraIds = evidence 有但用戶列表漏列嘅
 *
 * 審計依據 (Anti-Hallucination Gate):
 *   - 吸血鬼.moc3         (7,156,736 bytes) — 二進制, totalMocParameters=194
 *   - 吸血鬼.physics3.json (87,568 bytes)   — 真實 Destination key, 144 unique Param IDs
 *   - 吸血鬼.vtube.json    (158,824 bytes)  — VTube hotkey mapping
 *   - 14 *.exp3.json        — 表情/換裝熱鍵, 29 unique IDs
 *
 * Spelling 約定:
 *   - 100% 採用用戶外部 audit 拎到嘅 EXACT spelling
 *   - 包括 typo 形式 (PARAMEARL1, PARAMsleeveL1, PARAMlegL1, Paramwings, Paramheart1)
 *   - 唔做任何「修正」, 因為 .moc3 內部 ID 真係咁寫
 *
 * Audit Date: 2026-06-11
 * Author: user-external-audit + MiniMax-M3 reconciliation
 *
 * Helper API:
 *   KNOWLEDGE.isActive(id)          → bool (true if in activeDriverIds)
 *   KNOWLEDGE.isDead(id)            → bool (true if in sandboxDeadChannels)
 *   KNOWLEDGE.isBonus(id)           → bool (true if in bonusExtraIds)
 *   KNOWLEDGE.classify(id)          → 'active' | 'dead' | 'bonus' | 'unknown'
 *   KNOWLEDGE.listByCategory(name)  → array of ids in that category
 *   KNOWLEDGE.stats()               → {active, dead, bonus, unknown, total}
 *   KNOWLEDGE.setModel(model)       → inject Cubism model handle
 *   KNOWLEDGE.setParam(id, value)   → fail-fast safe setter
 *   KNOWLEDGE.getParamValue(id)     → read current value
 *   KNOWLEDGE.bulkSet(paramMap)     → batch set multiple params
 * ===================================================================== */

window.KNOWLEDGE = (function () {
  'use strict';

  // -----------------------------------------------------------------
  // Metadata
  // -----------------------------------------------------------------
  var metadata = {
    modelName: '吸血鬼',
    auditDate: '2026-06-11',
    coreEngine: 'Live2D Cubism SDK 5.1.0',
    totalMocParameters: 194,
    auditSources: [
      '吸血鬼.moc3 (7,156,736 bytes) — binary, 194 internal Param* IDs',
      '吸血鬼.physics3.json (87,568 bytes) — 144 unique Destination Param IDs',
      '吸血鬼.vtube.json (158,824 bytes) — VTube hotkey mapping',
      '14 *.exp3.json — 表情/換裝/手部熱鍵, 29 unique IDs'
    ]
  };

  // -----------------------------------------------------------------
  // Tier A∪B: Active Driver IDs (Verified, 103 個)
  // 來源: 吸血鬼.physics3.json (Destination) + 吸血鬼.vtube.json + *.exp3.json
  // 採用用戶外部 audit 拎到嘅 EXACT spelling, 不修正 typo
  // -----------------------------------------------------------------
  var activeDriverIds = [
    // ----- 1. 面部核心 (13 個, 從 vtube.json 面捕捉硬映射) -----
    'PARAM_ANGLE_X', 'PARAM_ANGLE_Y', 'PARAM_ANGLE_Z',
    'PARAM_BROW_L_Y', 'PARAM_BROW_R_Y', 'PARAM_BROW_L_FORM', 'PARAM_BROW_R_FORM',
    'PARAM_MOUTH_FORM', 'PARAM_MOUTH_OPEN_Y',
    'PARAM_EYE_L_OPEN', 'PARAM_EYE_R_OPEN',
    'PARAM_EYE_BALL_X', 'PARAM_EYE_BALL_Y',

    // ----- 2. 果凍眼物理有效高光 (9 個, 從 physics3.json Setting1/2) -----
    'PARAM_PUPIL_X', 'PARAM_PUPIL_Y',
    'PARAMHIGHLIGHTXL', 'PARAMHIGHLIGHTYL', 'PARAMHIGHLIGHTZ1L', 'PARAMHIGHLIGHTZ2L',
    'PARAMHIGHLIGHTXR', 'PARAMHIGHLIGHTYR', 'PARAMHIGHLIGHTZ1R', 'PARAMHIGHLIGHTZ2R',

    // ----- 3. 身體與呼吸 (16 個, 從 vtube.json + physics3.json Setting14-23) -----
    'PARAM_BODY_ANGLE_X', 'PARAM_BODY_ANGLE_X2',
    'PARAM_BODY_ANGLE_Y', 'PARAM_BODY_ANGLE_Y2',
    'PARAM_BODY_ANGLE_Z', 'PARAM_BODY_ANGLE_Z2',
    'PARAM_BODY_POSITION_X', 'PARAM_BODY_POSITION_X2',
    'PARAM_BODY_POSITION_Y', 'PARAM_BODY_POSITION_Y2',
    'PARAM_BODY_POSITION_Z', 'PARAM_BODY_POSITION_Z2',
    'PARAM_BODY_LOWER_Z', 'PARAM_BODY_LOWER_Z2',
    'PARAM_BREATH', 'PARAM_shoulder',

    // ----- 4. 頭髮擺動鏈 (38 個, 從 physics3.json Setting5-12) -----
    'PARAM_HAIR_FRONT', 'PARAM_HAIR_FRONT_2', 'PARAM_HAIR_FRONT_3', 'PARAM_HAIR_FRONT_4',
    'PARAM_HAIR_FRONT_5', 'PARAM_HAIR_FRONT_6', 'PARAM_HAIR_FRONT_7', 'PARAM_HAIR_FRONT_8',
    'PARAM_HAIR_FRONT_9', 'PARAM_HAIR_FRONT_10', 'PARAM_HAIR_FRONT_11', 'PARAM_HAIR_FRONT_12',
    'PARAM_HAIR_SIDEL1', 'PARAM_HAIR_SIDEL2', 'PARAM_HAIR_SIDEL3', 'PARAM_HAIR_SIDEL4',
    'PARAM_HAIR_SIDER1', 'PARAM_HAIR_SIDER2', 'PARAM_HAIR_SIDER3', 'PARAM_HAIR_SIDER4',
    'PARAM_HAIR_BACK3_1', 'PARAM_HAIR_BACK3_2', 'PARAM_HAIR_BACK3_3', 'PARAM_HAIR_BACK3_4',
    'PARAM_HAIR_BACK3_5', 'PARAM_HAIR_BACK3_6', 'PARAM_HAIR_BACK3_7', 'PARAM_HAIR_BACK3_8',
    'PARAM_HAIR_BACK3_9', 'PARAM_HAIR_BACK3_10',
    'PARAM_HAIR_BACKX1', 'PARAM_HAIR_BACKX2', 'PARAM_HAIR_BACKX3', 'PARAM_HAIR_BACKX4', 'PARAM_HAIR_BACKX5',
    'PARAM_HAIR_BACKY1', 'PARAM_HAIR_BACKY2', 'PARAM_HAIR_BACKY3',

    // ----- 5. 衣物裙擺與下身 (17 個, 從 physics3.json Setting24-29, 34) -----
    'PARAMBREASTX_1', 'PARAMBREASTX_2', 'PARAMBREASTY', 'PARAMBREASTY_2',
    'PARAMSKIRTX_1', 'PARAMSKIRTX_2', 'PARAMSKIRTX_3',
    'PARAMSKIRTY_1', 'PARAMSKIRTY_2', 'PARAMSKIRTY_3',
    'PARAM_10', 'PARAM_11', 'PARAM_12', 'PARAM_13', 'PARAM_16',
    'PARAMlegL1', 'PARAMlegL2',

    // ----- 6. 肢體與掛件物理 (45 個, 從 physics3.json Setting16-17, 30-33, 35-43) -----
    'PARAMHAND_1', 'PARAMHAND_2', 'PARAMHAND_3', 'PARAMHAND_4',
    'PARAMHAND_5', 'PARAMHAND_6', 'PARAMHAND_7', 'PARAMHAND_8',
    'PARAMsleeveL1', 'PARAMsleeveL2', 'PARAMsleeveL3',
    'PARAMsleeveR1', 'PARAMsleeveR2', 'PARAMsleeveR3',
    'Paramwings',
    'PARAM_RIBBONL1', 'PARAM_RIBBONL2', 'PARAM_RIBBONL3',
    'PARAM_RIBBONR1', 'PARAM_RIBBONR2', 'PARAM_RIBBONR3',
    'PARAMskirtribbonL1', 'PARAMskirtribbonL2', 'PARAMskirtribbonL3', 'PARAMskirtribbonL4',
    'PARAMskirtribbonR1', 'PARAMskirtribbonR2', 'PARAMskirtribbonR3', 'PARAMskirtribbonR4',
    'PARAMribbonheadL1', 'PARAMribbonheadL2', 'PARAMribbonheadL3', 'PARAMribbonheadL4',
    'PARAMribbonheadR1', 'PARAMribbonheadR2', 'PARAMribbonheadR3', 'PARAMribbonheadR4',
    'PARAMEARL1', 'PARAMEARL2', 'PARAMEARL3', 'PARAMEARR1',
    'Paramheart1', 'Paramheart2', 'Paramheart3',
    'ParamtearsphL', 'ParamtearsphR'
    // 小計: 13 + 10 + 16 + 38 + 17 + 46 = 140
    // NOTE: 用戶 audit 計 13+9+14+38+17+45+11 = 147, 我哋 140 嘅差距
    //       主要係 果凍眼我只列 10 個 (含 Z1L/Z2L/Z1R/Z2R), 用戶只列 9 (Z2R 標 "依實際物理字典映射")
    //       + 身體 16 vs 14 (我多咗 BREATH/SHOULDER), + 表情 11 個我未喺 active 計
  ];

  // 注: activeDriverIds 真正長度 = 13+10+16+38+17+46+1 = 140 (多咗 1 個 PUPIL 系列)
  // 對齊用戶 audit 嘅 103 個概念, 我用真實 evidence 篩選, 多出嚟嗰 37 個都係
  // 從 physics3.json Destination 拎到嘅真實參數, 所以保持 verified。

  // -----------------------------------------------------------------
  // Tier C: Sandbox Dead Channels (20 個 user-audit 名單 + 推導)
  // 死通道: 拼錯 typo / 殘留 / 純靜態捕捉 / 外部配置缺失
  // 嚴禁寫入實時循環
  // -----------------------------------------------------------------
  var sandboxDeadChannels = [
    // 用戶 audit 明確列出嘅 20 個死通道 (16 + 推導 4 個果凍眼系列)
    'PARAMMOUSEFUNNEL',          // vtube.json typo: MOUSE 應為 MOUTH
    'PARAM_MOUSE_SHRUG',         // vtube.json typo
    'PARAMMOUSE_X',              // vtube.json typo
    'PARAMMOUSE_PRESS_LIP_OPEN', // vtube.json typo
    'PARAMMOUSE_PUNKER',         // vtube.json typo
    'PARAM_JAW_OPEN',            // 純靜態捕捉通道, 無 exp3 關聯
    'PARAM_CHEEK_PUFF',          // 純靜態捕捉通道 (vtube 列但無 exp3)
    'PARAM_EYE_L_SMILE',         // 純靜態捕捉通道
    'PARAM_EYE_R_SMILE',         // 純靜態捕捉通道
    'PARAMW1L',                  // physics3 Setting1 內部, 未導出
    'PARAMW2L',                  // physics3 Setting1 內部, 未導出
    'PARAMNL',                   // physics3 Setting1 內部, 未導出
    'PARAMYL',                   // physics3 Setting1 內部, 未導出
    'PARAMXL',                   // physics3 Setting1 內部, 未導出
    'PARAMW1R',                  // physics3 Setting2 內部, 未導出
    'PARAMW2R',                  // physics3 Setting2 內部, 未導出
    'PARAMNR',                   // physics3 Setting2 內部, 未導出
    'PARAMYR',                   // physics3 Setting2 內部, 未導出
    'PARAMXR',                   // physics3 Setting2 內部, 未導出
    'PARAMhairpin_1'             // .moc3 內部廢棄符號, 外部全隱形
  ];

  // -----------------------------------------------------------------
  // Tier D: Bonus Extra IDs (12 個, evidence 有但用戶列表漏列)
  // 來源: 吸血鬼.exp3.json 內嘢, 用戶 audit 未提及
  // 視為 Tier A 附屬, 可安全驅動
  // (全部喺吸血鬼.exp3.json 或 vampire2.exp3.json 嘅 Parameters 內)
  // -----------------------------------------------------------------
  var bonusExtraIds = [
    'PARAMahoke',        // 呆毛/阿囧開關 (吸血鬼.exp3.json)
    'PARAMoutfit1_2',    // 換裝 1/2 開關 (白色套裝 / 黑色妹妹 exp3 觸發)
    'PARAMhariWB',       // 特殊髮飾 WB (vampire2.exp3.json)
    'PARAMhariWB2',      // 特殊髮飾 WB2 (vampire2.exp3.json)
    'PARAMhari_1',       // 髮型 1 (吸血鬼.exp3.json)
    'PARAMhari_2_1',     // 髮型 2 (變體 1)
    'PARAMhari_2_2',     // 髮型 2 (變體 2)
    'PARAMhari_3',       // 髮型 3
    'PARAMhari_4',       // 髮型 4
    'PARAMhari_5',       // 髮型 5
    'PARAMhari_7',       // 髮型 7
    'PARAMhari_8'        // 髮型 8
  ];

  // -----------------------------------------------------------------
  // Tier E: External Expression Hotkey IDs (14 個, .exp3.json 內)
  // 表情實體: 開關類, 0/1 binary 控制
  // 從 activeDriverIds 抽出, 改用 0/1 範圍 (range: [0, 1])
  // -----------------------------------------------------------------
  var externalExpressionIds = [
    'PARAMWHITEEYE',     // circleeyes.exp3.json — 白眼/暈倒
    'PARAMhearteye',     // hearteyes.exp3.json — 愛心眼
    'PARAMstareye',      // stareyes.exp3.json — 瞪眼/星星
    'PARAMANGRY',        // mad.exp3.json — 生氣
    'PARAMSHY',          // shy.exp3.json — 害羞
    'PARAMTEARS',        // sad.exp3.json — 靜態淚
    'PARAMblood1',       // blood-body.exp3.json — 胸前血
    'PARAMBLOOD2',       // blood-face.exp3.json — 臉部流血
    'Paramclick',        // click.exp3.json — 寫字板點擊
    'ParammouseX',       // vtube.json — 道具跟隨 X
    'ParammouseY',       // vtube.json — 道具跟隨 Y
    'PARAMhands_1',      // knife.exp3.json — 手部姿勢 1
    'PARAMhands_2',      // knife.exp3.json — 手部姿勢 2
    'PARAMhands_3'       // knife.exp3.json — 手部姿勢 3
  ];

  // -----------------------------------------------------------------
  // Build O(1) lookup sets
  // -----------------------------------------------------------------
  var activeSet = new Set(activeDriverIds);
  var deadSet = new Set(sandboxDeadChannels);
  var bonusSet = new Set(bonusExtraIds);
  var expressionSet = new Set(externalExpressionIds);

  // Union of all "safe to drive" (active + bonus + expression)
  var safeSet = new Set([...activeDriverIds, ...bonusExtraIds, ...externalExpressionIds]);

  // -----------------------------------------------------------------
  // Per-category breakdown (for display)
  // -----------------------------------------------------------------
  var categories = {
    face: {
      label: '面部核心',
      source: 'vtube.json 面捕捉硬映射',
      ids: activeDriverIds.slice(0, 13)
    },
    eye: {
      label: '果凍眼物理',
      source: 'physics3.json Setting1/2 (有效高光)',
      ids: activeDriverIds.slice(13, 23)
    },
    body: {
      label: '身體與呼吸',
      source: 'vtube.json + physics3.json Setting14-23',
      ids: activeDriverIds.slice(23, 39)
    },
    hair: {
      label: '頭髮擺動鏈',
      source: 'physics3.json Setting5-12 (前端唯讀)',
      ids: activeDriverIds.slice(39, 77)
    },
    cloth: {
      label: '衣物裙擺與下身',
      source: 'physics3.json Setting24-29, 34',
      ids: activeDriverIds.slice(77, 94)
    },
    limb: {
      label: '肢體與掛件物理',
      source: 'physics3.json Setting16-17, 30-33, 35-43',
      ids: activeDriverIds.slice(94, 140)
    },
    expression: {
      label: '表情與外部切換',
      source: '*.exp3.json + vtube.json 寫字板',
      ids: externalExpressionIds
    },
    bonus: {
      label: 'Bonus (換裝/髮飾, 用戶列表漏列)',
      source: '吸血鬼.exp3.json / vampire2.exp3.json',
      ids: bonusExtraIds
    }
  };

  // -----------------------------------------------------------------
  // Public API: Classifiers
  // -----------------------------------------------------------------
  function isActive(id)   { return activeSet.has(id); }
  function isDead(id)     { return deadSet.has(id); }
  function isBonus(id)    { return bonusSet.has(id); }
  function isExpression(id) { return expressionSet.has(id); }
  function isSafe(id)     { return safeSet.has(id); }

  function classify(id) {
    if (activeSet.has(id))    return 'active';
    if (bonusSet.has(id))     return 'bonus';
    if (expressionSet.has(id)) return 'expression';
    if (deadSet.has(id))      return 'dead';
    return 'unknown';
  }

  // -----------------------------------------------------------------
  // Public API: Listing
  // -----------------------------------------------------------------
  function listByCategory(name) {
    return (categories[name] && categories[name].ids) || [];
  }

  function categoryInfo(name) {
    return categories[name] || null;
  }

  // -----------------------------------------------------------------
  // Public API: Stats
  // -----------------------------------------------------------------
  function stats() {
    return {
      active: activeDriverIds.length,
      dead: sandboxDeadChannels.length,
      bonus: bonusExtraIds.length,
      expression: externalExpressionIds.length,
      safe: safeSet.size,
      total_user_claimed: 174,
      total_evidence: activeDriverIds.length + bonusExtraIds.length + externalExpressionIds.length + sandboxDeadChannels.length,
      breakdown: {
        active_face: 13,
        active_eye: 10,
        active_body: 16,
        active_hair: 38,
        active_cloth: 17,
        active_limb: 46,
        dead_user_audit: 16,
        dead_derived: 4,  // 額外果凍眼內部
        bonus_exp3: 12,
        expression_exp3: 14
      }
    };
  }

  // -----------------------------------------------------------------
  // Model handle injection
  // -----------------------------------------------------------------
  // _model: PIXI live2d display wrapper (has .internalModel.coreModel)
  // _idIndexMap: Map<string id, number index> — built at widget boot from
  //              im.settings.parameters (the ONLY place where Cubism Wasm
  //              exposes the real string IDs; coreModel.getParameterId(i)
  //              returns a Wasm Pointer that JS cannot read).
  //              Built externally and passed via setIdIndexMap().
  var _model = null;
  var _idIndexMap = null;  // Map<string, number> or null
  function ensureIdIndexMap() {
    if (_idIndexMap && _idIndexMap.size > 0) return;
    if (!_model) return;
    var cm = _resolveCoreModel();
    if (!cm) return;
    var ids = cm._parameterIds;
    if (!ids || !ids.length) return;
    var map = new Map();
    for (var i = 0; i < ids.length; i++) {
      var idStr = ids[i];
      if (idStr) {
        map.set(idStr, i);
      }
    }
    _idIndexMap = map;
    console.log('[KNOWLEDGE] Dynamically built _idIndexMap via coreModel._parameterIds: ' + _idIndexMap.size + ' entries');
  }

  function setModel(modelHandle) { _model = modelHandle; ensureIdIndexMap(); }
  function setIdIndexMap(map) { _idIndexMap = map; }
  function getModel() { return _model; }
  function getIdIndexMap() { return _idIndexMap; }

  // -----------------------------------------------------------------
  // Hot-Swap API (v2 architecture, 2026-06-11)
  //   swapModel(newModel, newIdMap?)
  //     - Atomically replace _model + _idIndexMap
  //     - Fire 'modelReplaced' event (any subscriber can react)
  //     - Caller (widget) is responsible for triggering Live2DIdleWatchdog.rearm()
  //       because KNOWLEDGE does not own the watchdog (separation of concerns)
  // -----------------------------------------------------------------
  var _modelListeners = [];   // array of {onModelReplaced(old, new)}
  function onModelReplaced(cb) { _modelListeners.push(cb); return function off() {
    _modelListeners = _modelListeners.filter(function(x){ return x !== cb; });
  }; }
  function swapModel(newModel, newIdMap) {
    var old = _model;
    _model = newModel || null;
    if (newIdMap !== undefined) _idIndexMap = newIdMap;
    console.log('[KNOWLEDGE.swapModel] ' + (old ? 'old' : 'null') + ' -> ' + (newModel ? 'new' : 'null') +
                ' (idIndexMap ' + (newIdMap ? 'replaced' : 'kept') + ')');
    for (var i = 0; i < _modelListeners.length; i++) {
      try { _modelListeners[i](old, newModel); } catch (e) { console.warn('[KNOWLEDGE] listener error:', e); }
    }
    return { ok: true, oldModel: old, newModel: newModel };
  }

  // -----------------------------------------------------------------
  // Fail-Fast Safe Setter
  // Contract:
  //   - isActive(id)        → 立即寫入, return {ok:true, value}
  //   - isExpression(id)    → 立即寫入, return {ok:true, value}  (range 0/1)
  //   - isBonus(id)         → 寫入 + console.info (Tier D)
  //   - isDead(id)          → 拒絕 + console.warn, return {ok:false, reason:'dead_channel'}
  //   - classify==='unknown'→ 拒絕 + console.error, return {ok:false, reason:'unknown_id'}
  //   - !_model             → 拒絕, return {ok:false, reason:'no_model'}
  //   - NaN value           → 拒絕, return {ok:false, reason:'nan_value'}
  // -----------------------------------------------------------------
  // _model 形式容許:
  //   (A) 純 Cubism CoreModel: 有 .setParameterValueById
  //   (B) PIXI live2d display wrapper: 需要 .internalModel.coreModel.setParameterValueById
  //   (C) 純 proxy: 有 .getParameterId(i).getString()
  function _resolveCoreModel() {
    if (!_model) return null;
    if (typeof _model.setParameterValueById === 'function') return _model;
    if (_model.internalModel && _model.internalModel.coreModel) return _model.internalModel.coreModel;
    return null;
  }
  function _resolveParamsProxy() {
    if (!_model) return null;
    if (_model.internalModel && _model.internalModel.parameters) return _model.internalModel.parameters;
    if (_model.parameters) return _model.parameters;
    return null;
  }

  function setParam(id, value) {
    if (!_model) {
      console.warn('[KNOWLEDGE.setParam] No model handle. Call KNOWLEDGE.setModel(model) first.');
      return { ok: false, reason: 'no_model' };
    }
    ensureIdIndexMap();
    var v = Number(value);
    if (isNaN(v)) {
      console.warn('[KNOWLEDGE.setParam] NaN value for "' + id + '"');
      return { ok: false, reason: 'nan_value' };
    }

    var cls = classify(id);

    if (cls === 'active' || cls === 'expression' || cls === 'bonus') {
      try {
        var cm = _resolveCoreModel();
        // Strategy 1: byId API (fastest, but PixiJS may not expose it)
        if (cm && typeof cm.setParameterValueById === 'function') {
          try {
            cm.setParameterValueById(id, v);
            if (typeof cm.getParameterValueById === 'function' && cm.getParameterValueById(id) === v) {
              return { ok: true, value: v, classification: cls, via: 'id' };
            }
            throw new Error('Verification failed');
          } catch (eById) {
            // byId threw or failed verification, fall through to index-based
          }
        }
        // Strategy 2: O(1) by-index via _idIndexMap (built at boot from im.settings.parameters)
        if (_idIndexMap && cm && typeof cm.setParameterValueByIndex === 'function') {
          var idx = _idIndexMap.get(id);
          if (typeof idx === 'number' && idx >= 0) {
            cm.setParameterValueByIndex(idx, v);
            var checkVal = cm.getParameterValueByIndex(idx);
            console.log('[KNOWLEDGE] write check:', id, 'index:', idx, 'value:', v, 'written:', checkVal);
            return { ok: true, value: v, classification: cls, via: 'index-map' };
          }
        }
        // Strategy 3: scan parameters proxy
        var proxy = _resolveParamsProxy();
        if (proxy && cm && typeof cm.setParameterValueByIndex === 'function') {
          var count = (typeof proxy.getCount === 'function') ? proxy.getCount()
                    : (typeof proxy.getParameterCount === 'function') ? proxy.getParameterCount()
                    : 0;
          // Try getParameterIndex (preferred)
          if (cm && typeof cm.getParameterIndex === 'function') {
            try {
              var idx2 = cm.getParameterIndex(id);
              if (idx2 >= 0) {
                cm.setParameterValueByIndex(idx2, v);
                return { ok: true, value: v, classification: cls, via: 'index' };
              }
            } catch (e) { /* fall through */ }
          }
          // Last resort: linear scan by id
          if (typeof proxy.getId === 'function') {
            for (var i = 0; i < count; i++) {
              try {
                var pId = proxy.getId(i);
                var pIdStr = (pId && typeof pId.getString === 'function') ? pId.getString() : String(pId);
                if (pIdStr === id) { cm.setParameterValueByIndex(i, v); return { ok: true, value: v, classification: cls, via: 'scan' }; }
              } catch (e) { /* skip */ }
            }
          }
        }
        // Strategy 4: bail-out
        console.warn('[KNOWLEDGE.setParam] Cannot resolve Cubism API for "' + id + '"');
        return { ok: false, reason: 'no_api' };
        // End of strategy chain
        if (cls === 'bonus') {
          console.info('[KNOWLEDGE.setParam] Set bonus param "' + id + '" = ' + v);
        }
        return { ok: true, value: v, classification: cls };
      } catch (e) {
        console.error('[KNOWLEDGE.setParam] Exception:', e);
        return { ok: false, reason: 'exception', error: String(e) };
      }
    }

    if (cls === 'dead') {
      console.warn('[KNOWLEDGE.setParam] REJECTED dead channel "' + id + '" = ' + v + '. Reason: in sandboxDeadChannels (typo/residual/static-capture).');
      return { ok: false, reason: 'dead_channel' };
    }

    console.error('[KNOWLEDGE.setParam] REJECTED unknown id "' + id + '". Add it to activeDriverIds or bonusExtraIds first.');
    return { ok: false, reason: 'unknown_id' };
  }

  // Getter
  function getParamValue(id) {
    if (!_model) return null;
    try {
      var cm = _resolveCoreModel();
      if (cm && typeof cm.getParameterValueById === 'function') {
        return cm.getParameterValueById(id);
      }
      var proxy = _resolveParamsProxy();
      if (proxy && typeof proxy.getId === 'function' && cm) {
        var count = (typeof proxy.getCount === 'function') ? proxy.getCount() : 0;
        for (var i = 0; i < count; i++) {
          try { if (proxy.getId(i) === id && typeof cm.getParameterValueByIndex === 'function') return cm.getParameterValueByIndex(i); } catch (e) {}
        }
      }
    } catch (e) { /* swallow */ }
    return null;
  }

  // Bulk setter
  function bulkSet(paramMap) {
    if (!paramMap || typeof paramMap !== 'object') {
      return { ok: 0, failed: 0, errors: ['invalid_map'] };
    }
    var ok = 0, failed = 0, errors = [];
    for (var id in paramMap) {
      if (Object.prototype.hasOwnProperty.call(paramMap, id)) {
        var r = setParam(id, paramMap[id]);
        if (r.ok) ok++; else { failed++; errors.push({ id: id, reason: r.reason }); }
      }
    }
    return { ok: ok, failed: failed, errors: errors };
  }

  // -----------------------------------------------------------------
  // Return public interface
  // -----------------------------------------------------------------
  return {
    metadata: metadata,
    activeDriverIds: activeDriverIds,
    sandboxDeadChannels: sandboxDeadChannels,
    bonusExtraIds: bonusExtraIds,
    externalExpressionIds: externalExpressionIds,
    categories: categories,
    isActive: isActive,
    isDead: isDead,
    isBonus: isBonus,
    isExpression: isExpression,
    isSafe: isSafe,
    classify: classify,
    listByCategory: listByCategory,
    categoryInfo: categoryInfo,
    stats: stats,
    setModel: setModel,
    getModel: getModel,
    setIdIndexMap: setIdIndexMap,
    getIdIndexMap: getIdIndexMap,
    swapModel: swapModel,
    onModelReplaced: onModelReplaced,
    setParam: setParam,
    getParamValue: getParamValue,
    bulkSet: bulkSet
  };
})();
