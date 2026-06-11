/**
 * Param Mapper — 將 DeepSeek response 嘅 params 映射到 Cubism model
 * 支援：
 *   1. 直接 params 字典 → setParameterValueById
 *   2. expression preset → 合併預設 params
 *   3. 範圍 clamp (根據 PARAM_REGISTRY)
 *   4. 平滑插值（避免動作突跳）
 */

class ParamMapper {
  constructor(model) {
    this.model = model;  // Cubism Model 實例
    this.currentParams = {};  // 當前 model 狀態
    this.targetParams = {};   // 目標狀態
    this.interpolationSpeed = 0.15;  // 平滑過渡速度 (0~1)
  }

  /**
   * 應用一個 DeepSeek response
   * @param {Object} response - {text, params, expression, motion}
   */
  applyResponse(response) {
    // 1. 先處理 expression preset（如果有的話）
    let mergedParams = {};
    if (response.expression && EXPRESSION_PRESETS[response.expression]) {
      mergedParams = { ...EXPRESSION_PRESETS[response.expression] };
      console.log(`[param_mapper] Applying expression preset: ${response.expression}`);
    }

    // 2. 合併 explicit params（覆蓋 preset）
    if (response.params) {
      Object.assign(mergedParams, response.params);
    }

    // 3. 設定 target
    this.setTarget(mergedParams);

    // 4. 處理 motion（如果有的話）
    if (response.motion && this.model.motion) {
      try {
        this.model.motion.startMotion(response.motion);
      } catch (e) {
        console.warn(`[param_mapper] Motion ${response.motion} failed:`, e);
      }
    }
  }

  /**
   * 設定 target params（會喺每 frame 嘅 update() 平滑過渡）
   */
  setTarget(params) {
    for (const [key, value] of Object.entries(params)) {
      // 驗證 param name
      if (!PARAM_REGISTRY[key]) {
        console.warn(`[param_mapper] Unknown param: ${key}, skip`);
        continue;
      }

      // Clamp 到合法範圍
      const [min, max] = PARAM_REGISTRY[key].range;
      const clamped = Math.max(min, Math.min(max, value));

      this.targetParams[key] = clamped;
    }
  }

  /**
   * 每 frame 呼叫：平滑過渡 current → target
   */
  update() {
    if (!this.model) return;

    for (const [key, target] of Object.entries(this.targetParams)) {
      const current = this.currentParams[key] || 0;
      const newValue = current + (target - current) * this.interpolationSpeed;

      // 設置到 Cubism model
      try {
        this.model.setParameterValueById(key, newValue);
      } catch (e) {
        // 偶爾會 throw "Parameter not found"，略過
      }

      this.currentParams[key] = newValue;
    }
  }

  /**
   * 重置所有 params 到 0
   */
  reset() {
    this.targetParams = {};
    this.currentParams = {};
  }
}

if (typeof window !== 'undefined') {
  window.ParamMapper = ParamMapper;
}
