"""Chrome runtime and Permissions API masking."""


def get_chrome_runtime_script() -> str:
    """Return JS to simulate window.chrome and fix Permissions API."""
    return """
    // Ensure window.chrome exists with runtime
    if (!window.chrome) {
        window.chrome = {};
    }
    if (!window.chrome.runtime) {
        window.chrome.runtime = {
            connect: function() { return { onMessage: { addListener: function() {} }, postMessage: function() {} }; },
            sendMessage: function() {},
            onMessage: { addListener: function() {}, removeListener: function() {} },
            onConnect: { addListener: function() {}, removeListener: function() {} },
            id: undefined,
        };
    }

    // Fix Permissions API to not reveal automation
    if (navigator.permissions) {
        const origQuery = navigator.permissions.query;
        navigator.permissions.query = function(parameters) {
            // Notifications permission - return 'prompt' instead of 'denied' (which bots typically have)
            if (parameters.name === 'notifications') {
                return Promise.resolve({
                    state: Notification.permission || 'prompt',
                    onchange: null,
                });
            }
            return origQuery.call(this, parameters);
        };
    }

    // Fix window.Notification
    if (typeof Notification !== 'undefined') {
        const origNotificationPermission = Object.getOwnPropertyDescriptor(Notification, 'permission');
        if (origNotificationPermission) {
            Object.defineProperty(Notification, 'permission', {
                get: () => 'default',
                configurable: true,
            });
        }
    }
    """
