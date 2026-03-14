"""Navigator property overrides to hide automation fingerprints."""


def get_navigator_script() -> str:
    """Return JS to override navigator.webdriver and related properties."""
    return """
    // Override navigator.webdriver
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined,
        configurable: true,
    });

    // Delete the webdriver property if it exists on the prototype
    if (Navigator.prototype.hasOwnProperty('webdriver')) {
        delete Navigator.prototype.webdriver;
        Object.defineProperty(Navigator.prototype, 'webdriver', {
            get: () => undefined,
            configurable: true,
        });
    }

    // Override navigator.plugins to simulate real Chrome plugins
    const makePluginArray = () => {
        const plugins = [
            {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format'},
            {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: ''},
            {name: 'Native Client', filename: 'internal-nacl-plugin', description: ''},
            {name: 'Chromium PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format'},
            {name: 'Chromium PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: ''},
        ];

        const pluginArray = Object.create(PluginArray.prototype);
        plugins.forEach((p, i) => {
            const plugin = Object.create(Plugin.prototype);
            Object.defineProperties(plugin, {
                name: {get: () => p.name, enumerable: true},
                filename: {get: () => p.filename, enumerable: true},
                description: {get: () => p.description, enumerable: true},
                length: {get: () => 1, enumerable: true},
            });
            Object.defineProperty(pluginArray, i, {
                get: () => plugin,
                enumerable: true,
            });
        });

        Object.defineProperties(pluginArray, {
            length: {get: () => plugins.length, enumerable: true},
            item: {value: (i) => pluginArray[i] || null},
            namedItem: {value: (name) => {
                for (let i = 0; i < plugins.length; i++) {
                    if (pluginArray[i].name === name) return pluginArray[i];
                }
                return null;
            }},
            refresh: {value: () => {}},
        });

        return pluginArray;
    };

    Object.defineProperty(navigator, 'plugins', {
        get: () => makePluginArray(),
        configurable: true,
    });

    // Override navigator.languages
    Object.defineProperty(navigator, 'languages', {
        get: () => ['en-US', 'en'],
        configurable: true,
    });

    // Override navigator.hardwareConcurrency to a common value
    Object.defineProperty(navigator, 'hardwareConcurrency', {
        get: () => 8,
        configurable: true,
    });

    // Override navigator.deviceMemory
    if (navigator.deviceMemory !== undefined) {
        Object.defineProperty(navigator, 'deviceMemory', {
            get: () => 8,
            configurable: true,
        });
    }

    // Override navigator.maxTouchPoints for non-touch device
    Object.defineProperty(navigator, 'maxTouchPoints', {
        get: () => 0,
        configurable: true,
    });
    """
