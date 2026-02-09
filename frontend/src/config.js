// API configuration for different environments
const API_BASE = import.meta.env.PROD 
  ? 'https://concord-backend.onrender.com'  // Replace with your actual backend URL
  : 'http://localhost:8000'

export default API_BASE