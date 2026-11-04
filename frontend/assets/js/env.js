// Deployment API origin. Localhost keeps using the local backend.
window.SAMACHAR_API_URL = /^(localhost|127\.0\.0\.1)$/.test(location.hostname)
  ? ''
  : 'https://samachar-api-production.up.railway.app';
