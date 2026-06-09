<template>
  <div class="control-panel">
    <div class="panel-header">
      <h2>控制面板</h2>
      <div class="mode-switch">
        <button 
          :class="{ active: localSettingsMode === 'basic' }"
          @click="switchMode('basic')"
        >
          基础模式
        </button>
        <button 
          :class="{ active: localSettingsMode === 'advanced' }"
          @click="switchMode('advanced')"
        >
          高级模式
        </button>
      </div>
    </div>

    <div class="panel-body">
      <div class="section">
        <label>提示词预设</label>
        <select v-model="selectedPromptPreset" class="prompt-preset-select">
          <option v-for="(preset, key) in promptPresets" :key="key" :value="key">
            {{ preset.label }}
          </option>
        </select>
      </div>

      <div class="section">
        <label>画面内容</label>
        <select v-model="selectedContentPreset" class="prompt-preset-select">
          <option v-for="(preset, key) in contentPresets" :key="key" :value="key">
            {{ preset.label }}
          </option>
        </select>
      </div>

      <div class="section">
        <label>提示词</label>
        <div class="prompt-combined">
          <span v-if="selectedPromptPreset !== 'none'" class="preset-prefix style-prefix">{{ presetPromptText }}</span>
          <span v-if="selectedContentPreset !== 'none'" class="preset-prefix content-prefix">{{ contentPromptText }}</span>
          <textarea 
            v-model="userPromptText"
            rows="3"
            :placeholder="placeholderText"
            class="user-prompt-input"
            :class="{ 'has-preset': hasAnyPreset }"
          ></textarea>
        </div>
      </div>

      <div class="section">
        <label>负面提示词</label>
        <textarea 
          v-model="localNegativePrompt"
          rows="2"
          placeholder="不希望出现的内容..."
        ></textarea>
      </div>

      <div class="section">
        <div class="row">
          <div class="col">
            <label>宽度</label>
            <input type="number" v-model.number="localWidth" min="64" step="8">
          </div>
          <div class="col">
            <label>高度</label>
            <input type="number" v-model.number="localHeight" min="64" step="8">
          </div>
        </div>
        <div v-if="sizeWarning" class="size-warning">
          ⚠️ {{ sizeWarning }}
        </div>
      </div>

      <div class="section">
        <div class="row">
          <div class="col">
            <label>随机种子</label>
            <input type="number" v-model.number="localSeed">
          </div>
          <div class="col">
            <label>输出格式</label>
            <select v-model="localOutputFormat">
              <option value="png">PNG</option>
              <option value="jpg">JPG</option>
              <option value="webp">WebP</option>
            </select>
          </div>
        </div>
        <button @click="randomizeSeed" class="random-seed-btn">🎲 随机种子</button>
      </div>

      <div v-if="localSettingsMode === 'basic'" class="section basic-mode">
        <label>质量预设</label>
        <select v-model="selectedPreset">
          <option v-for="(preset, key) in presets" :key="key" :value="key">
            {{ preset.label }} - {{ preset.description }}
          </option>
        </select>
        <p class="preset-note">{{ basicModeNote }}</p>
      </div>

      <div v-if="localSettingsMode === 'advanced'" class="section advanced-mode">
        <h3>Stage 1 (LCM 预览)</h3>
        <div class="row">
          <div class="col">
            <label>步数</label>
            <input type="number" v-model.number="lcmSteps" min="1" max="20">
          </div>
          <div class="col">
            <label>引导强度</label>
            <input type="number" v-model.number="lcmGuidance" min="0" max="20" step="0.1">
          </div>
        </div>
        <div class="row">
          <div class="col">
            <label>去噪强度</label>
            <input type="number" v-model.number="lcmDenoise" min="0" max="1" step="0.05">
          </div>
          <div class="col">
            <label>上采样倍率</label>
            <input type="number" v-model.number="latentScale" min="1" max="3" step="0.1">
          </div>
        </div>
        <div class="row">
          <div class="col">
            <label>Scribble 强度</label>
            <input type="number" v-model.number="scribbleScale1" min="0" max="2" step="0.1">
          </div>
          <div class="col">
            <label>Canny 强度</label>
            <input type="number" v-model.number="cannyScale1" min="0" max="2" step="0.1">
          </div>
        </div>

        <h3>Stage 2 (DPMPP 精修)</h3>
        <div class="row">
          <div class="col">
            <label>步数</label>
            <input type="number" v-model.number="dpmppSteps" min="10" max="100">
          </div>
          <div class="col">
            <label>引导强度</label>
            <input type="number" v-model.number="dpmppGuidance" min="0" max="20" step="0.1">
          </div>
        </div>
        <div class="row">
          <div class="col">
            <label>去噪强度</label>
            <input type="number" v-model.number="dpmppDenoise" min="0" max="1" step="0.05">
          </div>
          <div class="col">
            <label>Scribble 强度</label>
            <input type="number" v-model.number="scribbleScale2" min="0" max="2" step="0.1">
          </div>
        </div>
      </div>

      <div class="action-buttons">
        <button @click="$emit('preview', getGenerationParams())" :disabled="isGenerating">
          👁️ 预览
        </button>
        <button @click="$emit('generate', getGenerationParams())" class="primary" :disabled="isGenerating">
          🎨 生成
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useApiStore } from '../stores/api'

const props = defineProps({
  prompt: String,
  negativePrompt: String,
  seed: Number,
  outputFormat: String,
  settingsMode: String,
  qualityPreset: String,
  canvasWidth: Number,
  canvasHeight: Number,
  isGenerating: Boolean
})

const emit = defineEmits([
  'update:prompt',
  'update:negativePrompt',
  'update:seed',
  'update:outputFormat',
  'update:settingsMode',
  'update:qualityPreset',
  'update:canvasWidth',
  'update:canvasHeight',
  'generate',
  'preview'
])

const apiStore = useApiStore()

const localWidth = ref(props.canvasWidth)
const localHeight = ref(props.canvasHeight)
const localPrompt = ref(props.prompt || '')
const localNegativePrompt = ref(props.negativePrompt || '')
const localSeed = ref(props.seed || 143)
const localOutputFormat = ref(props.outputFormat || 'png')
const localSettingsMode = ref(props.settingsMode || 'basic')
const selectedPreset = ref(props.qualityPreset || 'Normal')
const selectedPromptPreset = ref('none')
const selectedContentPreset = ref('none')
const userPromptText = ref('')

const promptPresets = computed(() => {
  return apiStore.promptPresets || {
    none: { label: '无预设', prompt: '' },
    pixar3d: { label: '🎨 皮克斯 3D', prompt: '' },
    cyberpunk: { label: '🌃 赛博朋克', prompt: '' },
    inkwash: { label: '🖌️ 水墨画', prompt: '' },
    ghibli: { label: '🌿 宫崎骏风', prompt: '' },
    highquality: { label: '✨ 高质量通用', prompt: '' },
    realistic: { label: '📷 写实摄影', prompt: '' },
    anime: { label: '🌸 动漫风格', prompt: '' },
    conceptart: { label: '🎬 概念艺术', prompt: '' },
  }
})

const presetPromptText = computed(() => {
  const preset = promptPresets.value[selectedPromptPreset.value]
  return preset ? preset.prompt : ''
})

const contentPresets = computed(() => {
  return apiStore.contentPresets || {
    none: { label: '不限内容', prompt: '' },
    portrait: { label: '👤 人物肖像', prompt: '' },
    landscape: { label: '🏞️ 自然风景', prompt: '' },
    city: { label: '🏙️ 城市建筑', prompt: '' },
    animal: { label: '🐾 动物', prompt: '' },
    scifi: { label: '🚀 科幻太空', prompt: '' },
    fantasy: { label: '🐉 幻想世界', prompt: '' },
  }
})

const contentPromptText = computed(() => {
  const preset = contentPresets.value[selectedContentPreset.value]
  return preset ? preset.prompt : ''
})

const hasAnyPreset = computed(() => {
  return selectedPromptPreset.value !== 'none' || selectedContentPreset.value !== 'none'
})

const placeholderText = computed(() => {
  if (hasAnyPreset.value) return '在此追加你的描述...'
  return '描述你想要生成的图像...'
})

const buildFullPrompt = () => {
  const parts = []
  if (presetPromptText.value) parts.push(presetPromptText.value)
  if (contentPromptText.value) parts.push(contentPromptText.value)
  if (userPromptText.value.trim()) parts.push(userPromptText.value.trim())
  return parts.join(', ')
}

const basicModeNote = computed(() => apiStore.basicModeNote || '普通模式会自动设置关键控制强度')

const sizeWarning = computed(() => {
  const w = localWidth.value || 0
  const h = localHeight.value || 0
  if (w * h > 800 * 600) {
    return `当前尺寸 ${w}×${h}（${(w * h / 1000000).toFixed(2)}M 像素）可能超出显存限制，建议控制在 800×600 以内`
  }
  return ''
})

const presets = computed(() => {
  return apiStore.basicModePresets || {
    Noob: {
      label: 'Noob',
      description: '为unet留足发挥空间',
      scribble_scale_stage1: 0.6,
      canny_scale_stage1: 0.3,
      scribble_scale_stage2: 0.5,
    },
    Normal: {
      label: 'Normal',
      description: '平衡想法与创意',
      scribble_scale_stage1: 0.8,
      canny_scale_stage1: 0.5,
      scribble_scale_stage2: 0.8,
    },
    Hardcore: {
      label: 'Hardcore',
      description: '画面由你主导',
      scribble_scale_stage1: 1.1,
      canny_scale_stage1: 0.7,
      scribble_scale_stage2: 1.1,
    },
    God: {
      label: 'God',
      description: '你将作为达芬奇',
      scribble_scale_stage1: 1.3,
      canny_scale_stage1: 0.9,
      scribble_scale_stage2: 1.3,
    }
  }
})

const lcmSteps = ref(4)
const lcmGuidance = ref(2.5)
const lcmDenoise = ref(0.9)
const latentScale = ref(1.5)
const scribbleScale1 = ref(0.9)
const cannyScale1 = ref(0.4)
const dpmppSteps = ref(35)
const dpmppGuidance = ref(8.0)
const dpmppDenoise = ref(0.6)
const scribbleScale2 = ref(0.9)

watch(() => props.canvasWidth, (newVal) => {
  if (newVal !== undefined && newVal !== localWidth.value) localWidth.value = newVal
})

watch(() => props.canvasHeight, (newVal) => {
  if (newVal !== undefined && newVal !== localHeight.value) localHeight.value = newVal
})

watch(() => props.prompt, (newVal) => {
  // 仅当外部 prompt 与当前构建的不同时才同步（避免循环）
  if (newVal !== undefined && newVal !== localPrompt.value) {
    if (selectedPromptPreset.value === 'none') {
      userPromptText.value = newVal || ''
    }
  }
})

watch(() => props.negativePrompt, (newVal) => {
  if (newVal !== undefined && newVal !== localNegativePrompt.value) localNegativePrompt.value = newVal
})

watch(() => props.seed, (newVal) => {
  if (newVal !== undefined && newVal !== localSeed.value) localSeed.value = newVal
})

watch(() => props.outputFormat, (newVal) => {
  if (newVal !== undefined && newVal !== localOutputFormat.value) localOutputFormat.value = newVal
})

watch(() => props.settingsMode, (newVal) => {
  if (newVal !== undefined && newVal !== localSettingsMode.value) localSettingsMode.value = newVal
})

watch(() => props.qualityPreset, (newVal) => {
  if (newVal !== undefined && newVal !== selectedPreset.value) selectedPreset.value = newVal
})

watch(localWidth, (newVal) => {
  emit('update:canvasWidth', newVal)
})

watch(localHeight, (newVal) => {
  emit('update:canvasHeight', newVal)
})

watch(localPrompt, (newVal) => {
  emit('update:prompt', newVal)
})

// 当用户文本或预设变化时，构建完整提示词并 emit
const syncFullPrompt = () => {
  localPrompt.value = buildFullPrompt()
}

watch(userPromptText, () => {
  syncFullPrompt()
})

watch(selectedPromptPreset, () => {
  userPromptText.value = ''
  syncFullPrompt()
})

watch(selectedContentPreset, () => {
  userPromptText.value = ''
  syncFullPrompt()
})

watch(localNegativePrompt, (newVal) => {
  emit('update:negativePrompt', newVal)
})

watch(localSeed, (newVal) => {
  emit('update:seed', newVal)
})

watch(localOutputFormat, (newVal) => {
  emit('update:outputFormat', newVal)
})

watch(localSettingsMode, (newVal) => {
  emit('update:settingsMode', newVal)
})

watch(selectedPreset, (newVal) => {
  emit('update:qualityPreset', newVal)
})

const switchMode = (mode) => {
  emit('update:settingsMode', mode)
}

const randomizeSeed = () => {
  const newSeed = Math.floor(Math.random() * 2147483647)
  emit('update:seed', newSeed)
}

const getGenerationParams = () => {
  const params = {}
  
  if (localSettingsMode.value === 'basic') {
    const preset = presets.value[selectedPreset.value]
    if (preset) {
      params.scribble_scale_stage1 = preset.scribble_scale_stage1
      params.canny_scale_stage1 = preset.canny_scale_stage1
      params.scribble_scale_stage2 = preset.scribble_scale_stage2
    }
  } else {
    params.lcm_steps = lcmSteps.value
    params.lcm_guidance_scale = lcmGuidance.value
    params.lcm_denoise = lcmDenoise.value
    params.latent_scale_factor = latentScale.value
    params.scribble_scale_stage1 = scribbleScale1.value
    params.canny_scale_stage1 = cannyScale1.value
    params.dpmpp_steps = dpmppSteps.value
    params.dpmpp_guidance_scale = dpmppGuidance.value
    params.dpmpp_denoise = dpmppDenoise.value
    params.scribble_scale_stage2 = scribbleScale2.value
  }
  
  return params
}
</script>

<style scoped>
.control-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.panel-header {
  padding: 12px 16px;
  border-bottom: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.02);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-header h2 {
  margin: 0;
  font-size: 16px;
  color: var(--text);
}

.mode-switch {
  display: flex;
  gap: 4px;
}

.mode-switch button {
  padding: 6px 12px;
  font-size: 12px;
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.section {
  margin-bottom: 20px;
}

.section h3 {
  font-size: 14px;
  color: var(--text);
  margin: 16px 0 12px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--line);
}

.row {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}

.col {
  flex: 1;
}

.random-seed-btn {
  width: 100%;
  margin-top: 8px;
}

.preset-note {
  font-size: 12px;
  color: var(--sub);
  margin: 8px 0 0 0;
  padding: 8px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 4px;
}

.size-warning {
  font-size: 12px;
  color: var(--warn);
  margin-top: 8px;
  padding: 8px 10px;
  background: rgba(217, 138, 0, 0.1);
  border: 1px solid rgba(217, 138, 0, 0.25);
  border-radius: 4px;
  line-height: 1.4;
}

.action-buttons {
  display: flex;
  gap: 12px;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid var(--line);
}

.action-buttons button {
  flex: 1;
  padding: 12px;
  font-size: 14px;
}

.advanced-mode .row:last-child {
  margin-bottom: 0;
}

/* 提示词预设选择器 */
.prompt-preset-select {
  width: 100%;
}

/* 提示词组合输入框 */
.prompt-combined {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--line);
  border-radius: var(--border-radius);
  background: var(--panel);
  overflow: hidden;
  min-height: 80px;
}

.preset-prefix {
  padding: 6px 10px 2px 10px;
  font-size: 13px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
  user-select: none;
  font-style: italic;
}

.style-prefix {
  color: #8b9dc3;
  background: rgba(102, 126, 234, 0.06);
  border-bottom: 1px dashed rgba(102, 126, 234, 0.2);
}

.content-prefix {
  color: #7ecb8a;
  background: rgba(126, 203, 138, 0.06);
  border-bottom: 1px dashed rgba(126, 203, 138, 0.2);
}

.user-prompt-input {
  flex: 1;
  border: none !important;
  background: transparent;
  padding: 8px 10px;
  resize: vertical;
  font-family: inherit;
  font-size: 14px;
  color: var(--text);
  outline: none;
  min-height: 60px;
  width: 100%;
  box-sizing: border-box;
  border-radius: 0;
}

.user-prompt-input::placeholder {
  color: var(--sub);
}

.user-prompt-input.has-preset {
  padding-top: 4px;
}

/* 覆盖全局 textarea 样式中的冲突项 */
.prompt-combined .user-prompt-input {
  margin: 0;
  box-shadow: none;
}

textarea {
  resize: vertical;
  min-height: 80px;
}
</style>
