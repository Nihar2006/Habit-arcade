const getApiBaseUrl = () => {
  if (window.ENV_API_URL) return window.ENV_API_URL.replace(/\/$/, '');
  if (localStorage.getItem('api_url')) return localStorage.getItem('api_url').replace(/\/$/, '');
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    return 'http://127.0.0.1:8000/api';
  }
  return 'https://habit-arcade.onrender.com/api';
};

const API_BASE_URL = getApiBaseUrl();

class ApiService {
  static getToken() {
    return localStorage.getItem('token');
  }

  static setToken(token) {
    localStorage.setItem('token', token);
  }

  static removeToken() {
    localStorage.removeItem('token');
  }

  static async request(endpoint, method = 'GET', body = null) {
    const headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    };

    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const config = {
      method,
      headers
    };

    if (body) {
      config.body = JSON.stringify(body);
    }

    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
      const data = await response.json();

      if (!response.ok) {
        if (response.status === 401 && !endpoint.includes('/auth/login')) {
          this.removeToken();
          window.dispatchEvent(new Event('auth_expired'));
        }
        throw new Error(data.detail || 'API request failed');
      }

      return data;
    } catch (err) {
      console.error(`API Error [${method} ${endpoint}]:`, err);
      throw err;
    }
  }

  // Auth Methods
  static async signup(username, email, password) {
    const res = await this.request('/auth/signup', 'POST', { username, email, password });
    if (res.access_token) {
      this.setToken(res.access_token);
    }
    return res;
  }

  static async login(username_or_email, password) {
    const res = await this.request('/auth/login', 'POST', { username_or_email, password });
    if (res.access_token) {
      this.setToken(res.access_token);
    }
    return res;
  }

  static async getMe() {
    return await this.request('/auth/me', 'GET');
  }

  // Habit CRUD Methods
  static async getHabits() {
    return await this.request('/habits', 'GET');
  }

  static async createHabit(title, category = 'General', target_frequency = 'daily') {
    return await this.request('/habits', 'POST', { title, category, target_frequency });
  }

  static async updateHabit(id, title, category, target_frequency) {
    return await this.request(`/habits/${id}`, 'PUT', { title, category, target_frequency });
  }

  static async deleteHabit(id) {
    return await this.request(`/habits/${id}`, 'DELETE');
  }

  // Game Mechanics Methods
  static async toggleHabit(id) {
    return await this.request(`/habits/${id}/toggle`, 'POST');
  }

  static async reviveHabit(id) {
    return await this.request(`/habits/${id}/revive`, 'POST');
  }

  // Stats Methods
  static async getHeatmap() {
    return await this.request('/stats/heatmap', 'GET');
  }

  static async getDayStats(dateStr) {
    return await this.request(`/stats/day/${dateStr}`, 'GET');
  }
}
