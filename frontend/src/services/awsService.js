import api from './api'

const awsService = {
  getCosts: (params) => api.get('/aws/costs', { params }),
  getStorageUsage: () => api.get('/aws/storage'),
  getSecurityFindings: () => api.get('/aws/security'),
  getRecommendations: () => api.get('/aws/recommendations'),
  getBuckets: () => api.get('/aws/buckets'),
}

export default awsService