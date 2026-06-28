/**
 * DSR Petrol Platform — Client-Side Hash Router
 */

class Router {
    constructor() {
        this.routes = [];
        this.currentRoute = null;
        this._onRouteChange = null;
        window.addEventListener('hashchange', () => this._resolve());
    }

    /** Register a route */
    add(path, handler, options = {}) {
        this.routes.push({ path, handler, ...options });
        return this;
    }

    /** Set callback when route changes */
    onChange(callback) {
        this._onRouteChange = callback;
    }

    /** Navigate to a path */
    navigate(path) {
        window.location.hash = path;
    }

    /** Get the current hash path */
    getPath() {
        return window.location.hash.slice(1) || '/login';
    }

    /** Resolve the current route */
    _resolve() {
        const path = this.getPath();
        const match = this.routes.find(r => {
            if (r.path === path) return true;
            // Simple param matching: /dsr/:id
            if (r.path.includes(':')) {
                const regex = new RegExp('^' + r.path.replace(/:([^/]+)/g, '([^/]+)') + '$');
                return regex.test(path);
            }
            return false;
        });

        if (match) {
            // Extract params
            const params = {};
            if (match.path.includes(':')) {
                const keys = match.path.match(/:([^/]+)/g)?.map(k => k.slice(1)) || [];
                const regex = new RegExp('^' + match.path.replace(/:([^/]+)/g, '([^/]+)') + '$');
                const values = path.match(regex);
                if (values) {
                    keys.forEach((key, i) => { params[key] = values[i + 1]; });
                }
            }

            this.currentRoute = { ...match, params };
            if (this._onRouteChange) this._onRouteChange(this.currentRoute);
            match.handler(params);
        } else {
            // Default route
            this.navigate('/login');
        }
    }

    /** Start the router */
    start() {
        this._resolve();
    }
}

const router = new Router();
export default router;
