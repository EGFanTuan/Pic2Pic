import { defineStore } from 'pinia'
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 300000
})

export const useApiStore = defineStore('api', {
  state: () => ({
    status: 'initializing',
    device: 'CPU',
    gpu_name: null,
    busy: false,
    defaults: null,
    basicModePresets: null,
    basicModeDefaultPreset: 'Normal',
    basicModeNote: '',
    promptPresets: null,
    contentPresets: null,
    progress: {
      percentage: 0,
      status: 'idle',
      details: ''
    }
  }),

  getters: {
    isReady: (state) => state.status === 'ready' && !state.busy,
    getDefaults: (state) => state.defaults,
    getBasicModePresets: (state) => state.basicModePresets,
    getPromptPresets: (state) => state.promptPresets,
    getContentPresets: (state) => state.contentPresets
  },

  actions: {
    async fetchStatus() {
      try {
        const response = await api.get('/status')
        const data = response.data
        
        this.status = data.status || 'ready'
        this.device = data.device || 'CPU'
        this.gpu_name = data.gpu_name || null
        this.busy = data.busy || false
        this.defaults = data.defaults || null
        
        if (data.basic_mode) {
          this.basicModePresets = data.basic_mode.presets || null
          this.basicModeDefaultPreset = data.basic_mode.default_preset || 'Normal'
          this.basicModeNote = data.basic_mode.note || ''
        }
        
        if (data.prompt_presets) {
          this.promptPresets = data.prompt_presets
        }
        
        if (data.content_presets) {
          this.contentPresets = data.content_presets
        }
        
        if (data.progress) {
          this.progress = data.progress
        }
        
        return data
      } catch (error) {
        throw new Error(`状态获取失败：${error.message}`)
      }
    },

    async preview(imageBlob, params, onProgress) {
      try {
        const formData = new FormData()
        if (imageBlob) {
          formData.append('image', imageBlob, 'scribble.png')
        }
        formData.append('params', JSON.stringify(params))

        const response = await api.post('/preview', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          },
          onUploadProgress: onProgress ? (progressEvent) => {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            onProgress(progress)
          } : undefined
        })

        return response.data
      } catch (error) {
        throw new Error(error.response?.data?.error || `预览失败：${error.message}`)
      }
    },

    async generate(imageBlob, params, onProgress) {
      try {
        const formData = new FormData()
        if (imageBlob) {
          formData.append('image', imageBlob, 'scribble.png')
        }
        formData.append('params', JSON.stringify(params))

        const response = await api.post('/generate', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          },
          onUploadProgress: onProgress ? (progressEvent) => {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            onProgress(progress)
          } : undefined
        })

        return response.data
      } catch (error) {
        throw new Error(error.response?.data?.error || `生成失败：${error.message}`)
      }
    },

    async switchDevice(device) {
      try {
        const response = await api.post('/switch_device', { device })
        const data = response.data
        if (data.status === 'success') {
          this.device = data.device
          this.gpu_name = data.gpu_name
        }
        return data
      } catch (error) {
        throw new Error(error.response?.data?.error || `切换设备失败：${error.message}`)
      }
    }
  }
})
