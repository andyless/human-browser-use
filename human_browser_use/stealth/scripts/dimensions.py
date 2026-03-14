"""Window dimension consistency fixes."""


def get_dimensions_script() -> str:
    """Return JS to ensure window dimension consistency."""
    return """
    // Ensure outerWidth/outerHeight are larger than innerWidth/innerHeight
    // (In headless or automation, these can be equal, which is a detection signal)
    const origOuterWidth = Object.getOwnPropertyDescriptor(window, 'outerWidth');
    const origOuterHeight = Object.getOwnPropertyDescriptor(window, 'outerHeight');

    if (window.outerWidth === window.innerWidth) {
        Object.defineProperty(window, 'outerWidth', {
            get: () => window.innerWidth + 16,  // scrollbar width
            configurable: true,
        });
    }

    if (window.outerHeight === window.innerHeight) {
        Object.defineProperty(window, 'outerHeight', {
            get: () => window.innerHeight + 88,  // toolbar + tab bar height
            configurable: true,
        });
    }

    // Ensure screen dimensions are reasonable
    if (screen.width < window.innerWidth) {
        Object.defineProperty(screen, 'width', {
            get: () => Math.max(1920, window.innerWidth),
            configurable: true,
        });
    }
    if (screen.height < window.innerHeight) {
        Object.defineProperty(screen, 'height', {
            get: () => Math.max(1080, window.innerHeight),
            configurable: true,
        });
    }

    // Ensure screen.availWidth/availHeight are set properly
    Object.defineProperty(screen, 'availWidth', {
        get: () => screen.width,
        configurable: true,
    });
    Object.defineProperty(screen, 'availHeight', {
        get: () => screen.height - 40,  // taskbar
        configurable: true,
    });

    // Ensure screenX and screenY are not 0,0 (common in headless)
    if (window.screenX === 0 && window.screenY === 0) {
        Object.defineProperty(window, 'screenX', {
            get: () => 10,
            configurable: true,
        });
        Object.defineProperty(window, 'screenY', {
            get: () => 10,
            configurable: true,
        });
    }
    """
