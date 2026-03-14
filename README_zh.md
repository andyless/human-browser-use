<div align="center">

# 🧬 human-browser-use

### 让浏览器自动化和真人操作无法区分。

基于 [browser-use](https://github.com/browser-use/browser-use) 的扩展，把机器人般的瞬间操作替换为真实的人类行为 —— 平滑鼠标曲线、自然打字节奏、惯性滚动、指纹伪装。

**[English](README.md)** · **[中文](README_zh.md)** · **[日本語](README_ja.md)**

</div>

---

<div align="center">

🖱️ 贝塞尔鼠标轨迹 &emsp; ⌨️ 对数正态打字节奏 &emsp; 📜 惯性滚动 &emsp; 🛡️ 隐身指纹伪装

</div>

<br/>

<div align="center">
<img src="screen_shot.png" width="720" alt="鼠标轨迹可视化 — 蓝色轨迹显示速度热力图，红点标记点击位置，键盘事件实时记录"/>
</div>

<br/>

# 🤖 LLM 快速开始

1. 把你常用的编程 Agent（Cursor、Claude Code 等）指向 [skill.md](https://github.com/andyless/human-browser-use/blob/master/skill.md)
2. 直接开始提问！

<br/>

# 👋 手动快速开始

**1. 用 [uv](https://docs.astral.sh/uv/) 或 pip 安装（Python >= 3.11）：**

```bash
# 用 uv（推荐）
uv init && uv add human-browser-use && uv sync

# 或者用 pip
pip install human-browser-use
```

> 没有 Chromium？安装后运行 `playwright install chromium`。

**2. 运行你的第一个人类化自动化：**

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
    await inputs[0].click()              # 平滑贝塞尔鼠标轨迹
    await inputs[0].fill("hello world")  # 自然打字节奏，会打错字
    await page.press("Enter")

    await session.reset()

asyncio.run(main())
```

就这么简单。所有的 `click()`、`fill()`、`scroll()` 现在都像真人一样移动。

<br/>

# 🤖 配合 browser-use Agent 使用

把 `HumanBrowserSession` 传到 Agent 里就行 —— Agent 自动获得人类化行为：

```python
from browser_use import Agent
from langchain_openai import ChatOpenAI
from human_browser_use import HumanBrowserSession, HumanBrowserProfile, HumanBehaviorConfig

async def main():
    agent = Agent(
        task="在 Google 上搜索 'browser automation' 并点击第一个结果",
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

# 💻 命令行

继承 browser-use 全部 CLI 命令，自动带人类化行为：

```bash
hbu open https://example.com       # 导航（带隐身）
hbu state                           # 查看可点击元素
hbu click 5                         # 点击元素（人类鼠标轨迹）
hbu type "Hello"                    # 输入文字（人类打字节奏）
hbu screenshot page.png             # 截图
hbu close                           # 关闭浏览器
```

浏览器在命令之间保持运行。每次交互自动使用贝塞尔鼠标轨迹、对数正态打字和隐身指纹伪装。

<br/>

# 🧩 Claude Code 技能

安装技能文件，让 Claude Code 知道如何使用 human-browser-use：

```bash
mkdir -p ~/.claude/skills/human-browser-use
curl -o ~/.claude/skills/human-browser-use/SKILL.md \
  https://raw.githubusercontent.com/andyless/human-browser-use/main/skill.md
```

然后直接对 Claude Code 说：*"用 human-browser-use 填写这个页面上的表单"* —— 它会自动帮你写代码。

<br/>

# 🐾 配合 OpenClaw 使用

[OpenClaw](https://github.com/anthropics/openclaw) 接受任何 `BrowserSession`。传入 `HumanBrowserSession`，所有浏览器交互自动变成人类化的：

```python
from human_browser_use import HumanBrowserSession, HumanBrowserProfile, HumanBehaviorConfig

session = HumanBrowserSession(
    human_config=HumanBehaviorConfig(),
    browser_profile=HumanBrowserProfile(headless=False),
)
# 把 session 传给你的 OpenClaw agent —— 搞定。
```

<br/>

# 演示

### 🖱️ 鼠标轨迹可视化

测试页面捕获了自动化发出的每一个鼠标事件。蓝到红的轨迹显示速度（蓝=慢，红=快），十字线标记点击落点。

**自己跑一下：**

```bash
# 终端 1：启动测试页面服务器
python -m http.server 8765

# 终端 2：运行自动化测试
python test_tracker.py
```

<br/>

# ⚙️ 配置

每种行为都可以独立配置和开关：

```python
config = HumanBehaviorConfig()

# --- 鼠标 ---
config.mouse.overshoot_probability = 0.15       # 冲过头的概率（长距离自动增加）
config.mouse.click_offset_sigma = 3.0           # 点击位置随机偏移 (px)
config.mouse.press_duration_range = (0.05, 0.15) # 按键按住时长 (秒)

# --- 键盘 ---
config.keyboard.delay_mu = 4.17                 # 对数正态均值 → 平均约 65ms 按键间隔
config.keyboard.typo_probability = 0.02          # 每次按键出错概率
config.keyboard.common_bigram_factor = 0.7       # "th"、"er" 等常见组合快 30%

# --- 滚动 ---
config.scroll.impulse_delta_range = (80, 200)    # 初始滚动冲量 (px)
config.scroll.inertia_decay = 0.85               # 每帧速度衰减

# --- 时间 ---
config.timing.pre_action_delay_range = (0.1, 0.3) # 操作前思考时间 (秒)

# --- 功能开关 ---
config.enable_stealth = True            # 隐身 JS 注入
config.enable_human_mouse = True        # 人类鼠标
config.enable_human_keyboard = True     # 人类键盘
config.enable_human_scroll = True       # 人类滚动
```

<br/>

# FAQ

<details>
<summary><b>和 browser-use 有什么区别？</b></summary>

[browser-use](https://github.com/browser-use/browser-use) 是核心浏览器自动化框架。human-browser-use 是在它上面加了人类化行为层。你仍然在用 browser-use —— 我们只是让它动起来像真人。

- `BrowserSession` → 瞬间点击、瞬间打字、没有鼠标移动
- `HumanBrowserSession` → 贝塞尔轨迹、对数正态打字、惯性滚动、隐身 JS
</details>

<details>
<summary><b>支持哪些 LLM？</b></summary>

全部支持。human-browser-use 不碰 LLM 层，只改变浏览器执行动作的方式。GPT-4o、Claude、Gemini、Ollama，browser-use 支持什么我们就支持什么。
</details>

<details>
<summary><b>能绕过所有反 bot 检测吗？</b></summary>

它大幅提高了检测门槛。隐身层隐藏了常见自动化指纹（`navigator.webdriver`、WebGL、Canvas、Chrome 运行时），行为层产生 DOM 级的鼠标/键盘事件。但没有工具能保证 100% —— 复杂系统还会检查 IP 信誉、会话模式等。
</details>

<details>
<summary><b>不用 LLM 能用吗（直接 API）？</b></summary>

可以！见上面的快速开始。用 `page.get_elements_by_css_selector()`、`.click()`、`.fill()` 等手动编排，不需要 LLM。
</details>

<details>
<summary><b>鼠标轨迹是怎么实现的？</b></summary>

单条连续贝塞尔曲线，弧长参数化变速重采样：
- **0–5%**：快速加速（0.3x → 2.5x 平均速度）
- **5–75%**：高速巡航 2.3–2.5x，带微小正弦波动
- **75–100%**：三次缓出减速（2.5x → 0.3x）
- 末段亚像素漂移（sigma 0.3–1.5px）— 手部自然晃动
- 时长遵循 Fitts 定律：`0.05 + 0.07 * log2(1 + distance/20)` 秒
</details>

<details>
<summary><b>键盘模拟怎么做的？</b></summary>

- **按键间隔**：对数正态分布（μ=4.17, σ=0.3 → 平均约 65ms）
- **常见组合加速**："th"、"er" 等快 30%
- **打字错误**：2% 概率 → 打错邻近键 → 停顿 → 退格 → 打对
- **词间停顿**：空格后额外 80–160ms
</details>

<details>
<summary><b>有哪些隐身功能？</b></summary>

每次页面加载时注入 JS：
- `navigator.webdriver` → `undefined`
- 模拟 `navigator.plugins`（Chrome PDF Plugin 等）
- WebGL 供应商/渲染器伪装（ANGLE 字符串）
- Canvas 指纹噪声
- `window.chrome.runtime` 存在性
- Permissions API 响应伪装
- 20+ Chrome 启动参数减少检测面
</details>

<br/>

# 架构

```
human_browser_use/
├── session.py                  # HumanBrowserSession — 主入口
├── profile.py                  # HumanBrowserProfile — 隐身 Chrome 启动参数
├── config.py                   # 所有配置类
├── actor/
│   ├── page.py                 # HumanPage — 把元素包装为 HumanElement
│   ├── element.py              # HumanElement — 人类化的 click/fill
│   └── mouse.py                # HumanMouse — 底层鼠标操作
├── behavior/
│   ├── mouse_trajectory.py     # 贝塞尔曲线 + 变速重采样
│   ├── keyboard_dynamics.py    # 对数正态延迟 + 打字错误模拟
│   ├── scroll_dynamics.py      # 冲量-惯性滚动物理
│   └── timing.py               # 操作前延迟
├── stealth/
│   ├── injection.py            # StealthInjector — 编译并注入 JS
│   └── scripts/                # navigator, webgl, canvas, chrome_runtime, dimensions
└── watchdogs/
    └── human_action_watchdog.py  # Agent 驱动的人类行为
```

**两条交互路径，都走人类化逻辑：**

| 路径 | 流程 | 场景 |
|---|---|---|
| Agent 驱动 | EventBus → `HumanActionWatchdog` → 人类行为 | 用 `Agent()` + LLM |
| 直接 API | `HumanPage` → `HumanElement.click()/fill()` → 人类行为 | 不用 LLM 手动编排 |

<br/>

## 许可证

MIT
