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
    busy: false,
    defaults: null,
    basicModePresets: null,
    basicModeDefaultPreset: 'Normal',
    basicModeNote: ''
  }),

  getters: {
    isReady: (state) => state.status === 'ready' && !state.busy,
    getDefaults: (state) => state.defaults,
    getBasicModePresets: (state) => state.basicModePresets
  },

  actions: {
    async fetchStatus() {
      try {
        const response = await api.get('/status')
        const data = response.data
        
        this.status = data.status || 'ready'
        this.device = data.device || 'CPU'
        this.busy = data.busy || false
        this.defaults = data.defaults || null
        
        if (data.basic_mode) {
          this.basicModePresets = data.basic_mode.presets || null
          this.basicModeDefaultPreset = data.basic_mode.default_preset || 'Normal'
          this.basicModeNote = data.basic_mode.note || ''
        }
        
        return data
      } catch (error) {
        throw new Error(`状态获取失败：${error.message}`)
      }
    },

    async preview(params, onProgress) {
      try {
        const formData = new FormData()
        Object.keys(params).forEach(key => {
          formData.append(key, params[key])
        })

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

    async generate(params, onProgress) {
      try {
        const formData = new FormData()
        Object.keys(params).forEach(key => {
          formData.append(key, params[key])
        })

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
    }
  }
})
