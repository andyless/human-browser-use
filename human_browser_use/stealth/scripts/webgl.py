"""WebGL vendor/renderer fingerprint masking."""


def get_webgl_script() -> str:
    """Return JS to override WebGL renderer and vendor info."""
    return """
    // Override WebGL getParameter to return realistic GPU info
    const origGetParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(param) {
        // UNMASKED_VENDOR_WEBGL
        if (param === 0x9245) {
            return 'Google Inc. (NVIDIA)';
        }
        // UNMASKED_RENDERER_WEBGL
        if (param === 0x9246) {
            return 'ANGLE (NVIDIA, NVIDIA GeForce GTX 1660 SUPER Direct3D11 vs_5_0 ps_5_0, D3D11)';
        }
        return origGetParameter.call(this, param);
    };

    // Also override for WebGL2
    if (typeof WebGL2RenderingContext !== 'undefined') {
        const origGetParameter2 = WebGL2RenderingContext.prototype.getParameter;
        WebGL2RenderingContext.prototype.getParameter = function(param) {
            if (param === 0x9245) {
                return 'Google Inc. (NVIDIA)';
            }
            if (param === 0x9246) {
                return 'ANGLE (NVIDIA, NVIDIA GeForce GTX 1660 SUPER Direct3D11 vs_5_0 ps_5_0, D3D11)';
            }
            return origGetParameter2.call(this, param);
        };
    }

    // Override getExtension to hide debug extension info leak
    const origGetExtension = WebGLRenderingContext.prototype.getExtension;
    WebGLRenderingContext.prototype.getExtension = function(name) {
        if (name === 'WEBGL_debug_renderer_info') {
            // Return the extension but with our overridden getParameter
            return origGetExtension.call(this, name);
        }
        return origGetExtension.call(this, name);
    };
    """
