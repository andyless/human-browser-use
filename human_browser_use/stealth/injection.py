"""StealthInjector - compiles and manages stealth JS injection."""

from human_browser_use.stealth.scripts.navigator import get_navigator_script
from human_browser_use.stealth.scripts.webgl import get_webgl_script
from human_browser_use.stealth.scripts.canvas import get_canvas_script
from human_browser_use.stealth.scripts.chrome_runtime import get_chrome_runtime_script
from human_browser_use.stealth.scripts.dimensions import get_dimensions_script


class StealthInjector:
    """Compiles and provides stealth JavaScript for injection."""

    def __init__(self):
        self._compiled_script: str | None = None

    def get_stealth_script(self) -> str:
        """Get the compiled stealth script. Cached after first call."""
        if self._compiled_script is None:
            self._compiled_script = self._compile()
        return self._compiled_script

    def _compile(self) -> str:
        """Compile all stealth scripts into a single IIFE."""
        scripts = [
            get_navigator_script(),
            get_webgl_script(),
            get_canvas_script(),
            get_chrome_runtime_script(),
            get_dimensions_script(),
        ]

        combined = '\n'.join(scripts)
        return f'(function() {{\n{combined}\n}})();'
