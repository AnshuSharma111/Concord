// API configuration for different environments
const API_BASE = import.meta.env.PROD 
  ? 'https://concord-backend-zhc5.onrender.com'  // Deployed backend URL
  : 'http://localhost:8000'

export default API_BASE