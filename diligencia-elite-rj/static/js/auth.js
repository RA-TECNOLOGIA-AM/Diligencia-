class AuthService {
    constructor() {
        this.token = localStorage.getItem('accessToken');
        this.user = JSON.parse(localStorage.getItem('user') || 'null');
        this.tokenRefreshInterval = null;
        this.sessionTimeoutWarning = null;
        this.lastActivity = Date.now();
        this.inactivityTimeout = 30 * 60 * 1000;
        this.initializeActivity();
    }

    async register(data) {
        try {
            const response = await fetch('/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Erro ao registrar');
            }

            return await response.json();
        } catch (error) {
            throw error;
        }
    }

    async login(email, password, rememberMe = false) {
        try {
            const response = await fetch('/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password, remember_me: rememberMe })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Erro ao fazer login');
            }

            const data = await response.json();
            this.setToken(data.access_token);
            this.setUser(data.user);
            this.startTokenRefresh();

            return data;
        } catch (error) {
            throw error;
        }
    }

    async logout() {
        try {
            await fetch('/auth/logout', {
                method: 'POST',
                headers: this.getAuthHeaders()
            });
        } finally {
            this.clearAuth();
        }
    }

    async refreshToken() {
        try {
            const response = await fetch('/auth/refresh', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (!response.ok) {
                this.clearAuth();
                throw new Error('Token refresh failed');
            }

            const data = await response.json();
            this.setToken(data.access_token);

            return data.access_token;
        } catch (error) {
            this.clearAuth();
            throw error;
        }
    }

    async forgotPassword(email) {
        try {
            const response = await fetch('/auth/forgot-password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Erro ao solicitar recuperação');
            }

            return await response.json();
        } catch (error) {
            throw error;
        }
    }

    async resetPassword(token, newPassword, confirmPassword) {
        try {
            const response = await fetch('/auth/reset-password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    token,
                    new_password: newPassword,
                    confirm_password: confirmPassword
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Erro ao redefinir senha');
            }

            return await response.json();
        } catch (error) {
            throw error;
        }
    }

    async changePassword(currentPassword, newPassword, confirmPassword) {
        try {
            const response = await fetch('/auth/change-password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...this.getAuthHeaders()
                },
                body: JSON.stringify({
                    current_password: currentPassword,
                    new_password: newPassword,
                    confirm_password: confirmPassword
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Erro ao alterar senha');
            }

            this.clearAuth();
            return await response.json();
        } catch (error) {
            throw error;
        }
    }

    async getProfile() {
        try {
            const response = await fetch('/api/users/profile', {
                method: 'GET',
                headers: this.getAuthHeaders()
            });

            if (!response.ok) {
                if (response.status === 401) {
                    this.clearAuth();
                }
                throw new Error('Erro ao carregar perfil');
            }

            const user = await response.json();
            this.setUser(user);
            return user;
        } catch (error) {
            throw error;
        }
    }

    async updateProfile(data) {
        try {
            const response = await fetch('/api/users/profile', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    ...this.getAuthHeaders()
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Erro ao atualizar perfil');
            }

            const user = await response.json();
            this.setUser(user);
            return user;
        } catch (error) {
            throw error;
        }
    }

    async uploadAvatar(file) {
        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('/api/users/profile/avatar', {
                method: 'POST',
                headers: this.getAuthHeaders(),
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Erro ao fazer upload da foto');
            }

            return await response.json();
        } catch (error) {
            throw error;
        }
    }

    async updatePreferences(theme, language) {
        try {
            const response = await fetch('/api/users/profile/preferences', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...this.getAuthHeaders()
                },
                body: JSON.stringify({ theme, language })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Erro ao atualizar preferências');
            }

            return await response.json();
        } catch (error) {
            throw error;
        }
    }

    async deleteAccount(password) {
        try {
            const response = await fetch('/api/users/account', {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    ...this.getAuthHeaders()
                },
                body: JSON.stringify({ password })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Erro ao deletar conta');
            }

            this.clearAuth();
            return await response.json();
        } catch (error) {
            throw error;
        }
    }

    isAuthenticated() {
        return !!this.token && !!this.user;
    }

    getUser() {
        return this.user;
    }

    getToken() {
        return this.token;
    }

    hasRole(role) {
        return this.user && this.user.role === role;
    }

    hasAnyRole(...roles) {
        return this.user && roles.includes(this.user.role);
    }

    getAuthHeaders() {
        return {
            'Authorization': `Bearer ${this.token}`
        };
    }

    async makeAuthenticatedRequest(url, options = {}) {
        if (!this.isAuthenticated()) {
            throw new Error('Not authenticated');
        }

        const headers = {
            ...options.headers,
            ...this.getAuthHeaders()
        };

        try {
            let response = await fetch(url, { ...options, headers });

            if (response.status === 401) {
                try {
                    await this.refreshToken();
                    headers['Authorization'] = `Bearer ${this.token}`;
                    response = await fetch(url, { ...options, headers });
                } catch (error) {
                    this.clearAuth();
                    window.location.href = '/login';
                    throw new Error('Session expired');
                }
            }

            return response;
        } catch (error) {
            throw error;
        }
    }

    setToken(token) {
        this.token = token;
        localStorage.setItem('accessToken', token);
    }

    setUser(user) {
        this.user = user;
        localStorage.setItem('user', JSON.stringify(user));
        this.updateActivity();
    }

    clearAuth() {
        this.token = null;
        this.user = null;
        localStorage.removeItem('accessToken');
        localStorage.removeItem('user');
        this.stopTokenRefresh();
        this.stopSessionTimeoutWarning();
    }

    startTokenRefresh() {
        this.stopTokenRefresh();
        this.tokenRefreshInterval = setInterval(() => {
            if (this.isAuthenticated()) {
                this.refreshToken().catch(() => window.location.href = '/login');
            }
        }, 12 * 60 * 1000);
    }

    stopTokenRefresh() {
        if (this.tokenRefreshInterval) {
            clearInterval(this.tokenRefreshInterval);
            this.tokenRefreshInterval = null;
        }
    }

    initializeActivity() {
        ['mousedown', 'keydown', 'scroll', 'touchstart'].forEach(event => {
            document.addEventListener(event, () => this.updateActivity(), true);
        });

        if (this.isAuthenticated()) {
            this.startSessionTimeoutWarning();
        }
    }

    updateActivity() {
        this.lastActivity = Date.now();
    }

    startSessionTimeoutWarning() {
        this.sessionTimeoutWarning = setInterval(() => {
            if (this.isAuthenticated()) {
                const inactiveTime = Date.now() - this.lastActivity;
                if (inactiveTime > this.inactivityTimeout) {
                    this.clearAuth();
                    alert('Sua sessão expirou por inatividade.');
                    window.location.href = '/login';
                }
            }
        }, 60000);
    }

    stopSessionTimeoutWarning() {
        if (this.sessionTimeoutWarning) {
            clearInterval(this.sessionTimeoutWarning);
            this.sessionTimeoutWarning = null;
        }
    }
}

const auth = new AuthService();

if (!auth.isAuthenticated()) {
    const publicPages = ['/login', '/signup', '/forgot-password', '/reset-password'];
    if (!publicPages.includes(window.location.pathname)) {
        window.location.href = '/login';
    }
}
