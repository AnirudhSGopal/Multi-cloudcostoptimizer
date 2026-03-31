import api from './api'

const azureService = {
  getCosts: (params) => api.get('/azure/costs', { params }),
  getStorageUsage: () => api.get('/azure/storage'),
  getSecurityFindings: () => api.get('/azure/security'),
  getRecommendations: () => api.get('/azure/recommendations'),
  getContainers: () => api.get('/azure/containers'),
}

export default azureService