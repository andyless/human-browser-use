"""Canvas fingerprint noise injection."""


def get_canvas_script() -> str:
    """Return JS to add imperceptible noise to canvas operations."""
    return """
    // Add imperceptible noise to canvas toDataURL and toBlob
    const origToDataURL = HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL = function(type, quality) {
        // Only modify 2D canvas (not WebGL)
        const ctx = this.getContext('2d');
        if (ctx) {
            // Add tiny noise to a single pixel
            const imageData = ctx.getImageData(0, 0, 1, 1);
            // Modify least significant bit
            imageData.data[0] = imageData.data[0] ^ (Math.random() > 0.5 ? 1 : 0);
            ctx.putImageData(imageData, 0, 0);
        }
        return origToDataURL.call(this, type, quality);
    };

    const origToBlob = HTMLCanvasElement.prototype.toBlob;
    if (origToBlob) {
        HTMLCanvasElement.prototype.toBlob = function(callback, type, quality) {
            const ctx = this.getContext('2d');
            if (ctx) {
                const imageData = ctx.getImageData(0, 0, 1, 1);
                imageData.data[0] = imageData.data[0] ^ (Math.random() > 0.5 ? 1 : 0);
                ctx.putImageData(imageData, 0, 0);
            }
            return origToBlob.call(this, callback, type, quality);
        };
    }

    // Override getImageData to add noise
    const origGetImageData = CanvasRenderingContext2D.prototype.getImageData;
    CanvasRenderingContext2D.prototype.getImageData = function(sx, sy, sw, sh) {
        const imageData = origGetImageData.call(this, sx, sy, sw, sh);
        // Add noise to a random pixel in the data
        if (imageData.data.length >= 4) {
            const idx = Math.floor(Math.random() * (imageData.data.length / 4)) * 4;
            imageData.data[idx] = imageData.data[idx] ^ 1;
        }
        return imageData;
    };
    """
