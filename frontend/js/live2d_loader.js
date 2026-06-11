/**
 * Live2D Loader — 用 PIXI.js + pixi-live2d-display 載入吸血鬼 model
 */

class Live2DLoader {
  constructor(canvasElement) {
    this.canvas = canvasElement;
    this.app = null;
    this.model = null;
    this.paramMapper = null;
  }

  async init() {
    // 等 Cubism SDK ready
    if (typeof PIXI === 'undefined') {
      throw new Error('PIXI.js 未加載');
    }
    if (typeof Live2DCubismFramework === 'undefined') {
      throw new Error('Cubism Framework 未加載');
    }

    // 創建 PIXI Application
    this.app = new PIXI.Application({
      view: this.canvas,
      width: this.canvas.clientWidth,
      height: this.canvas.clientHeight,
      backgroundColor: 0x1a0a1a,
      antialias: true,
      resolution: window.devicePixelRatio || 1,
      autoDensity: true
    });

    // 等 PIXI init
    await new Promise(resolve => setTimeout(resolve, 100));

    // 載入吸血鬼 model
    const modelPath = 'live2d/吸血鬼.model3.json';
    
    try {
      this.model = await PIXI.live2d.Live2DModel.from(modelPath, {
        autoInteract: false  // 我哋自己揸 fit，唔好 default mouse follow
      });

      this.app.stage.addChild(this.model);

      // 縮放 + 置中
      const scale = Math.min(
        this.app.screen.width / this.model.width,
        this.app.screen.height / this.model.height
      ) * 0.85;
      this.model.scale.set(scale);
      this.model.x = (this.app.screen.width - this.model.width * scale) / 2;
      this.model.y = (this.app.screen.height - this.model.height * scale) / 2;

      // 創建 param mapper
      this.paramMapper = new ParamMapper(this.model.internalModel.coreModel);

      // 每 frame update
      this.app.ticker.add(() => {
        if (this.paramMapper) this.paramMapper.update();
        // Idle breathing
        if (this.model.internalModel && this.model.internalModel.coreModel) {
          const breathVal = 0.5 + 0.3 * Math.sin(Date.now() / 2000);
          try {
            this.model.internalModel.coreModel.setParameterValueById('PARAM_BREATH', breathVal);
          } catch (e) {}
        }
      });

      // 點擊頭部觸發 random reaction
      this.model.on('pointertap', (event) => {
        if (event.data && event.data.global) {
          const localX = (event.data.global.x - this.model.x) / this.model.scale.x;
          const localY = (event.data.global.y - this.model.y) / this.model.scale.y;
          if (localY < this.model.height * 0.3) {
            // 頭部點擊
            this._randomReaction();
          }
        }
      });

      console.log('[Live2DLoader] Model loaded:', modelPath);
      return this.model;

    } catch (e) {
      console.error('[Live2DLoader] Failed to load model:', e);
      throw e;
    }
  }

  _randomReaction() {
    if (!this.paramMapper) return;
    const reactions = [
      { 'PARAM_ANGLE_X': 0.3, 'PARAM_MOUTH_FORM': 0.4, 'PARAM_EYE_L_SMILE': 0.5 },
      { 'PARAM_ANGLE_X': -0.3, 'PARAM_MOUTH_FORM': -0.3, 'PARAM_BROW_L_Y': 0.3 },
      { 'Paramwings': 1.0, 'PARAM_EYE_L_OPEN': 0.7, 'PARAM_MOUTH_FORM': 0.5 },
      { 'PARAM_ANGLE_Y': -0.2, 'PARAM_MOUTH_FORM': -0.5, 'PARAM_BROW_L_Y': -0.3 }
    ];
    const r = reactions[Math.floor(Math.random() * reactions.length)];
    this.paramMapper.setTarget(r);
    setTimeout(() => {
      this.paramMapper.targetParams = {};
    }, 2000);
  }

  resize() {
    if (!this.app || !this.model) return;
    this.app.renderer.resize(this.canvas.clientWidth, this.canvas.clientHeight);
    const scale = Math.min(
      this.app.screen.width / this.model.width,
      this.app.screen.height / this.model.height
    ) * 0.85;
    this.model.scale.set(scale);
    this.model.x = (this.app.screen.width - this.model.width * scale) / 2;
    this.model.y = (this.app.screen.height - this.model.height * scale) / 2;
  }
}

if (typeof window !== 'undefined') {
  window.Live2DLoader = Live2DLoader;
}
