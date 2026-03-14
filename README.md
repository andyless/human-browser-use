<div align="center">

# 🧬 human-browser-use

### Make browser automation indistinguishable from a real human.

A drop-in extension for [browser-use](https://github.com/browser-use/browser-use) that replaces robotic instant actions with realistic human behavior — smooth mouse curves, natural typing rhythm, inertia scrolling, and stealth fingerprint masking.

**[English](README.md)** · **[中文](README_zh.md)** · **[日本語](README_ja.md)**

</div>

---

<div align="center">

🖱️ Bezier mouse trajectories &emsp; ⌨️ Lognormal typing dynamics &emsp; 📜 Inertia scrolling &emsp; 🛡️ Stealth fingerprint masking

</div>

<br/>

<div align="center">
<img src="screen_shot.png" width="720" alt="Mouse trajectory visualization — blue trail shows speed heatmap, red dots mark clicks, keyboard events logged in real-time"/>
</div>

<br/>

# 🤖 LLM Quickstart

1. Direct your favorite coding agent (Cursor, Claude Code, etc.) to [skill.md](https://github.com/andyless/human-browser-use/blob/master/skill.md)
2. Prompt away!

<br/>

# 👋 Human Quickstart

**1. Install with [uv](https://docs.astral.sh/uv/) or pip (Python >= 3.11):**

```bash
# With uv (recommended)
uv init && uv add human-browser-use && uv sync

# Or with pip
pip install human-browser-use
```

> Don't have Chromium? Run `playwright install chromium` after installing.

**2. Run your first human-like automation:**

```python
import asyncio
from human_browser_use import HumanBrowserSession, HumanBrowserProfile, HumanBehaviorConfig

async def main():
    session = HumanBrowserSession(
        human_config=HumanBehaviorConfig(),
        browser_profile=HumanBrowserProfile(headless=False),
    )
    await session.start()
    await session.navigate_to("https://example.com")

    page = await session.get_current_page()
    inputs = await page.get_elements_by_css_selector("input")
    await inputs[0].click()              # smooth Bezier mouse trajectory
    await inputs[0].fill("hello world")  # natural typing rhythm with typos
    await page.press("Enter")

    await session.reset()

asyncio.run(main())
```

That's it. Every `click()`, `fill()`, and `scroll()` now moves like a real person.

<br/>

# 🤖 Use with browser-use Agent

Just pass `HumanBrowserSession` where you'd normally use `BrowserSession` — the Agent gets human-like behavior for free:

```python
from browser_use import Agent
from langchain_openai import ChatOpenAI
from human_browser_use import HumanBrowserSession, HumanBrowserProfile, HumanBehaviorConfig

async def main():
    agent = Agent(
        task="Search for 'browser automation' on Google and click the first result",
        llm=ChatOpenAI(model="gpt-4o"),
        browser_session=HumanBrowserSession(
            human_config=HumanBehaviorConfig(),
            browser_profile=HumanBrowserProfile(headless=False),
        ),
    )
    await agent.run()

asyncio.run(main())
```

<br/>

# 💻 CLI

All browser-use CLI commands, now with human-like behavior:

```bash
hbu open https://example.com       # Navigate (with stealth)
hbu state                           # See clickable elements
hbu click 5                         # Click element (human-like trajectory)
hbu type "Hello"                    # Type text (human-like dynamics)
hbu screenshot page.png             # Take screenshot
hbu close                           # Close browser
```

The CLI keeps the browser alive between commands. Every interaction automatically uses Bezier mouse trajectories, lognormal typing, and stealth fingerprint masking.

<br/>

# 🧩 Claude Code Skill

Install the skill so Claude Code knows how to use human-browser-use:

```bash
mkdir -p ~/.claude/skills/human-browser-use
curl -o ~/.claude/skills/human-browser-use/SKILL.md \
  https://raw.githubusercontent.com/andyless/human-browser-use/main/skill.md
```

Then just tell Claude Code: *"use human-browser-use to fill in the form on this page"* — it will write the automation code for you.

<br/>

# 🐾 Use with OpenClaw

[OpenClaw](https://github.com/anthropics/openclaw) accepts any `BrowserSession`. Pass in `HumanBrowserSession` and all browser interactions become human-like:

```python
from human_browser_use import HumanBrowserSession, HumanBrowserProfile, HumanBehaviorConfig

session = HumanBrowserSession(
    human_config=HumanBehaviorConfig(),
    browser_profile=HumanBrowserProfile(headless=False),
)
# Pass session to your OpenClaw agent — done.
```

<br/>

# Demo

### 🖱️ Mouse Trajectory Visualization

The test page captures every mouse event dispatched by the automation. The blue-to-red trail shows speed (blue = slow, red = fast). Click markers show where clicks landed with crosshair precision.

**Run it yourself:**

```bash
# Terminal 1: Start the test page server
python -m http.server 8765

# Terminal 2: Run the automation test
python test_tracker.py
```

<br/>

# ⚙️ Configuration

Every behavior is configurable and can be toggled independently:

```python
config = HumanBehaviorConfig()

# --- Mouse ---
config.mouse.overshoot_probability = 0.15       # overshoot chance (auto-increases for long moves)
config.mouse.click_offset_sigma = 3.0           # click position randomness (px)
config.mouse.press_duration_range = (0.05, 0.15) # button hold time (sec)

# --- Keyboard ---
config.keyboard.delay_mu = 4.17                 # lognormal mean → ~65ms avg inter-key delay
config.keyboard.typo_probability = 0.02          # typo chance per keystroke
config.keyboard.common_bigram_factor = 0.7       # "th", "er" etc. typed 30% faster

# --- Scroll ---
config.scroll.impulse_delta_range = (80, 200)    # initial scroll impulse (px)
config.scroll.inertia_decay = 0.85               # velocity decay per frame

# --- Timing ---
config.timing.pre_action_delay_range = (0.1, 0.3) # think time before actions (sec)

# --- Feature toggles ---
config.enable_stealth = True            # stealth JS injection
config.enable_human_mouse = True        # human-like mouse movement
config.enable_human_keyboard = True     # human-like typing
config.enable_human_scroll = True       # human-like scrolling
```

<br/>

# FAQ

<details>
<summary><b>How is this different from browser-use?</b></summary>

[browser-use](https://github.com/browser-use/browser-use) is the core browser automation framework. human-browser-use is an extension that adds human-like behavior on top. You still use browser-use — we just make it move like a real person instead of a robot.

- `BrowserSession` → instant clicks, instant typing, no mouse movement
- `HumanBrowserSession` → Bezier trajectories, lognormal typing, inertia scroll, stealth JS
</details>

<details>
<summary><b>Does it work with any LLM?</b></summary>

Yes. human-browser-use doesn't touch the LLM layer. It only changes how the browser executes actions. Use it with GPT-4o, Claude, Gemini, Ollama, or any LLM that browser-use supports.
</details>

<details>
<summary><b>Will it bypass all anti-bot detection?</b></summary>

It significantly raises the bar. The stealth layer hides common automation fingerprints (`navigator.webdriver`, WebGL, canvas, Chrome runtime). The behavior layer produces DOM-level mouse/keyboard events that look human. But no tool guarantees 100% bypass — sophisticated systems also check IP reputation, session patterns, and more.
</details>

<details>
<summary><b>Can I use it without an LLM (direct API)?</b></summary>

Yes! See the Quickstart above. You can script everything manually with `page.get_elements_by_css_selector()`, `.click()`, `.fill()`, etc. No LLM required.
</details>

<details>
<summary><b>How does the mouse trajectory work?</b></summary>

Single continuous Bezier curve with arc-length parameterized variable speed:
- **0–5%**: Quick ramp-up (0.3x → 2.5x average speed)
- **5–75%**: Fast cruise at 2.3–2.5x with slight sine variation
- **75–100%**: Cubic ease-out deceleration (2.5x → 0.3x)
- Sub-pixel drift at the end (sigma 0.3–1.5px) — natural hand settling
- Duration follows Fitts' Law: `0.05 + 0.07 * log2(1 + distance/20)` seconds
</details>

<details>
<summary><b>How does the keyboard simulation work?</b></summary>

- **Inter-key delay**: Lognormal distribution (μ=4.17, σ=0.3 → ~65ms average)
- **Bigram speedup**: Common pairs like "th", "er" typed 30% faster
- **Typo simulation**: 2% chance → wrong nearby key → pause → backspace → correct key
- **Word boundaries**: Extra 80–160ms pause after spaces
</details>

<details>
<summary><b>What stealth features are included?</b></summary>

JavaScript injected on every page load:
- `navigator.webdriver` → `undefined`
- Fake `navigator.plugins` (Chrome PDF Plugin, etc.)
- WebGL vendor/renderer spoofing (ANGLE strings)
- Canvas fingerprint noise
- `window.chrome.runtime` presence
- Permissions API response masking
- 20+ Chrome launch flags to reduce detection surface
</details>

<br/>

# Architecture

```
human_browser_use/
├── session.py                  # HumanBrowserSession — main entry point
├── profile.py                  # HumanBrowserProfile — stealth Chrome flags
├── config.py                   # All configuration classes
├── actor/
│   ├── page.py                 # HumanPage — wraps elements as HumanElement
│   ├── element.py              # HumanElement — click/fill with human behavior
│   └── mouse.py                # HumanMouse — low-level mouse actor
├── behavior/
│   ├── mouse_trajectory.py     # Bezier curves + variable speed resampling
│   ├── keyboard_dynamics.py    # Lognormal delays + typo simulation
│   ├── scroll_dynamics.py      # Impulse-inertia scroll physics
│   └── timing.py               # Pre-action delays
├── stealth/
│   ├── injection.py            # StealthInjector — compiles & injects JS
│   └── scripts/                # navigator, webgl, canvas, chrome_runtime, dimensions
└── watchdogs/
    └── human_action_watchdog.py  # Agent-driven human behavior
```

**Two interaction paths, both human-like:**

| Path | Flow | When |
|---|---|---|
| Agent-driven | EventBus → `HumanActionWatchdog` → human behavior | Using `Agent()` with LLM |
| Direct API | `HumanPage` → `HumanElement.click()/fill()` → human behavior | Scripting without LLM |

<br/>

## License

MIT
