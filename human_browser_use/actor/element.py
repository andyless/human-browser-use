"""HumanElement - Element actor with human-like mouse trajectory and keyboard dynamics."""

import asyncio
import logging
import random

from browser_use.actor.element import Element

from human_browser_use.config import HumanBehaviorConfig
from human_browser_use.behavior.mouse_trajectory import MouseTrajectory
from human_browser_use.behavior.keyboard_dynamics import KeyboardDynamics
from human_browser_use.behavior.timing import ActionTiming

logger = logging.getLogger(__name__)


class HumanElement(Element):
    """Element with human-like click (trajectory) and fill (keyboard dynamics).

    Overrides the base Element.click() and Element.fill() to dispatch
    mouse events along a realistic trajectory and type with lognormal delays.
    """

    def __init__(self, *args, human_config: HumanBehaviorConfig | None = None, mouse_state: dict | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._human_config = human_config or HumanBehaviorConfig()
        self._trajectory = MouseTrajectory(self._human_config.mouse)
        self._keyboard = KeyboardDynamics(self._human_config.keyboard)
        self._timing = ActionTiming(self._human_config.timing)
        # Shared mouse position state across elements (dict reference so all elements share it)
        self._mouse_state = mouse_state if mouse_state is not None else {'x': 0.0, 'y': 0.0}

    async def _move_mouse_human(self, target_x: float, target_y: float):
        """Move mouse along a human-like trajectory with realistic speed profile."""
        session_id = await self._ensure_session()
        timed_points = self._trajectory.generate_with_timing(
            self._mouse_state['x'], self._mouse_state['y'],
            target_x, target_y,
        )
        if not timed_points:
            return

        for px, py, delay in timed_points:
            await self._client.send.Input.dispatchMouseEvent(
                params={'type': 'mouseMoved', 'x': px, 'y': py},
                session_id=session_id,
            )
            await asyncio.sleep(delay)

        self._mouse_state['x'] = target_x
        self._mouse_state['y'] = target_y

    async def click(self, button='left', click_count=1, modifiers=None) -> None:
        """Click element with human-like mouse trajectory.

        Instead of teleporting to the element center, generates a realistic
        trajectory path and dispatches mouseMoved events along it.
        """
        if not self._human_config.enable_human_mouse:
            return await super().click(button, click_count, modifiers)

        session_id = await self._ensure_session()

        # Get viewport dimensions
        layout_metrics = await self._client.send.Page.getLayoutMetrics(session_id=session_id)
        viewport_width = layout_metrics['layoutViewport']['clientWidth']
        viewport_height = layout_metrics['layoutViewport']['clientHeight']

        # Scroll into view
        try:
            await self._client.send.DOM.scrollIntoViewIfNeeded(
                params={'backendNodeId': self._backend_node_id},
                session_id=session_id,
            )
            await asyncio.sleep(0.05)
        except Exception:
            pass

        # Get element center coordinates (try multiple methods)
        center_x, center_y = await self._get_element_center(session_id, viewport_width, viewport_height)
        if center_x is None:
            logger.warning('Could not get element geometry, falling back to base click')
            return await super().click(button, click_count, modifiers)

        # Apply random click offset
        dx = random.gauss(0, self._human_config.mouse.click_offset_sigma)
        dy = random.gauss(0, self._human_config.mouse.click_offset_sigma)
        click_x = max(0, min(viewport_width - 1, center_x + dx))
        click_y = max(0, min(viewport_height - 1, center_y + dy))

        # Pre-action delay
        await asyncio.sleep(self._timing.get_pre_action_delay())

        # Move mouse along trajectory
        await self._move_mouse_human(click_x, click_y)

        # Mouse down
        modifier_flags = self._get_modifier_flags(modifiers)
        try:
            await asyncio.wait_for(
                self._client.send.Input.dispatchMouseEvent(
                    params={
                        'type': 'mousePressed',
                        'x': click_x, 'y': click_y,
                        'button': button, 'clickCount': click_count,
                        'modifiers': modifier_flags,
                    },
                    session_id=session_id,
                ),
                timeout=3.0,
            )
        except TimeoutError:
            logger.debug('Mouse down timed out')

        # Variable press duration
        await asyncio.sleep(self._trajectory.get_press_duration())

        # Mouse up
        try:
            await asyncio.wait_for(
                self._client.send.Input.dispatchMouseEvent(
                    params={
                        'type': 'mouseReleased',
                        'x': click_x, 'y': click_y,
                        'button': button, 'clickCount': click_count,
                        'modifiers': modifier_flags,
                    },
                    session_id=session_id,
                ),
                timeout=5.0,
            )
        except TimeoutError:
            logger.debug('Mouse up timed out')

        logger.debug(f'Human-clicked element at ({click_x:.0f}, {click_y:.0f})')

    async def fill(self, value: str, clear: bool = True) -> None:
        """Fill element with human-like keyboard dynamics.

        Types character-by-character with lognormal inter-key delays
        and optional typo simulation.
        """
        if not self._human_config.enable_human_keyboard:
            return await super().fill(value, clear)

        session_id = await self._ensure_session()

        # Scroll into view
        try:
            await self._client.send.DOM.scrollIntoViewIfNeeded(
                params={'backendNodeId': self._backend_node_id},
                session_id=session_id,
            )
            await asyncio.sleep(0.01)
        except Exception:
            pass

        # Get object ID for focus/clear operations
        result = await self._client.send.DOM.resolveNode(
            params={'backendNodeId': self._backend_node_id},
            session_id=session_id,
        )
        object_id = result['object']['objectId']

        # Focus element
        try:
            await self._client.send.DOM.focus(
                params={'backendNodeId': self._backend_node_id},
                session_id=session_id,
            )
        except Exception:
            await self._client.send.Runtime.callFunctionOn(
                params={'functionDeclaration': 'function() { this.focus(); }', 'objectId': object_id},
                session_id=session_id,
            )

        # Clear existing text
        if clear:
            try:
                await self._client.send.Runtime.callFunctionOn(
                    params={
                        'functionDeclaration': """function() {
                            if (this.value !== undefined) {
                                var nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                                    window.HTMLInputElement.prototype, 'value'
                                ) || Object.getOwnPropertyDescriptor(
                                    window.HTMLTextAreaElement.prototype, 'value'
                                );
                                if (nativeInputValueSetter && nativeInputValueSetter.set) {
                                    nativeInputValueSetter.set.call(this, '');
                                } else {
                                    this.value = '';
                                }
                            } else if (this.isContentEditable) {
                                this.textContent = '';
                            }
                            this.dispatchEvent(new Event('input', { bubbles: true }));
                        }""",
                        'objectId': object_id,
                    },
                    session_id=session_id,
                )
            except Exception:
                # Fallback: select all + delete
                await self._client.send.Input.dispatchKeyEvent(
                    params={'type': 'keyDown', 'key': 'a', 'code': 'KeyA', 'modifiers': 2},  # Ctrl+A
                    session_id=session_id,
                )
                await self._client.send.Input.dispatchKeyEvent(
                    params={'type': 'keyUp', 'key': 'a', 'code': 'KeyA', 'modifiers': 2},
                    session_id=session_id,
                )
                await asyncio.sleep(0.02)
                await self._client.send.Input.dispatchKeyEvent(
                    params={'type': 'keyDown', 'key': 'Delete', 'code': 'Delete', 'windowsVirtualKeyCode': 46},
                    session_id=session_id,
                )
                await self._client.send.Input.dispatchKeyEvent(
                    params={'type': 'keyUp', 'key': 'Delete', 'code': 'Delete', 'windowsVirtualKeyCode': 46},
                    session_id=session_id,
                )

        # Type with human-like dynamics
        self._keyboard.reset()
        i = 0
        while i < len(value):
            char = value[i]

            # Inter-key delay
            delay = self._keyboard.get_inter_key_delay(char)
            await asyncio.sleep(delay)

            # Possibly make a typo
            if char.isalpha() and self._keyboard.should_make_typo():
                typo_char = self._keyboard.get_typo_char(char)
                if typo_char:
                    await self._type_char(typo_char, session_id)
                    await asyncio.sleep(self._keyboard.get_typo_pause())
                    # Backspace to correct
                    await self._client.send.Input.dispatchKeyEvent(
                        params={'type': 'keyDown', 'key': 'Backspace', 'code': 'Backspace', 'windowsVirtualKeyCode': 8},
                        session_id=session_id,
                    )
                    await asyncio.sleep(0.03)
                    await self._client.send.Input.dispatchKeyEvent(
                        params={'type': 'keyUp', 'key': 'Backspace', 'code': 'Backspace', 'windowsVirtualKeyCode': 8},
                        session_id=session_id,
                    )
                    await asyncio.sleep(0.05)

            # Type correct character
            await self._type_char(char, session_id)
            i += 1

        # Trigger framework events
        try:
            await self._client.send.Runtime.callFunctionOn(
                params={
                    'functionDeclaration': """function() {
                        this.dispatchEvent(new Event('input', { bubbles: true }));
                        this.dispatchEvent(new Event('change', { bubbles: true }));
                    }""",
                    'objectId': object_id,
                },
                session_id=session_id,
            )
        except Exception:
            pass

        logger.debug(f'Human-typed {len(value)} chars into element')

    async def _type_char(self, char: str, session_id: str):
        """Type a single character with proper key events."""
        if char == '\n':
            await self._client.send.Input.dispatchKeyEvent(
                params={'type': 'keyDown', 'key': 'Enter', 'code': 'Enter', 'windowsVirtualKeyCode': 13},
                session_id=session_id,
            )
            await asyncio.sleep(0.001)
            await self._client.send.Input.dispatchKeyEvent(
                params={'type': 'char', 'text': '\r', 'key': 'Enter'},
                session_id=session_id,
            )
            await self._client.send.Input.dispatchKeyEvent(
                params={'type': 'keyUp', 'key': 'Enter', 'code': 'Enter', 'windowsVirtualKeyCode': 13},
                session_id=session_id,
            )
        else:
            modifiers = 1 if char.isupper() or char in '~!@#$%^&*()_+{}|:"<>?' else 0
            base_key = char.lower() if char.isalpha() else char
            vk_code = ord(base_key.upper()) if base_key.isalpha() else ord(char)
            key_code = f'Key{base_key.upper()}' if base_key.isalpha() else f'Digit{char}' if char.isdigit() else 'Space' if char == ' ' else ''

            await self._client.send.Input.dispatchKeyEvent(
                params={'type': 'keyDown', 'key': base_key, 'code': key_code, 'modifiers': modifiers, 'windowsVirtualKeyCode': vk_code},
                session_id=session_id,
            )
            await asyncio.sleep(0.003)
            await self._client.send.Input.dispatchKeyEvent(
                params={'type': 'char', 'text': char, 'key': char},
                session_id=session_id,
            )
            await self._client.send.Input.dispatchKeyEvent(
                params={'type': 'keyUp', 'key': base_key, 'code': key_code, 'modifiers': modifiers, 'windowsVirtualKeyCode': vk_code},
                session_id=session_id,
            )

    async def _get_element_center(self, session_id: str, vw: float, vh: float) -> tuple[float | None, float | None]:
        """Get element center coordinates, trying multiple methods."""
        # Method 1: getContentQuads
        try:
            quads_result = await self._client.send.DOM.getContentQuads(
                params={'backendNodeId': self._backend_node_id},
                session_id=session_id,
            )
            quads = quads_result.get('quads', [])
            if quads:
                q = quads[0]
                cx = sum(q[i] for i in range(0, 8, 2)) / 4
                cy = sum(q[i] for i in range(1, 8, 2)) / 4
                return max(0, min(vw - 1, cx)), max(0, min(vh - 1, cy))
        except Exception:
            pass

        # Method 2: getBoxModel
        try:
            box_result = await self._client.send.DOM.getBoxModel(
                params={'backendNodeId': self._backend_node_id},
                session_id=session_id,
            )
            content = box_result['model']['content']
            cx = sum(content[i] for i in range(0, 8, 2)) / 4
            cy = sum(content[i] for i in range(1, 8, 2)) / 4
            return max(0, min(vw - 1, cx)), max(0, min(vh - 1, cy))
        except Exception:
            pass

        # Method 3: getBoundingClientRect via JS
        try:
            result = await self._client.send.DOM.resolveNode(
                params={'backendNodeId': self._backend_node_id},
                session_id=session_id,
            )
            object_id = result['object']['objectId']
            rect_result = await self._client.send.Runtime.callFunctionOn(
                params={
                    'functionDeclaration': 'function() { var r = this.getBoundingClientRect(); return {x: r.x, y: r.y, w: r.width, h: r.height}; }',
                    'objectId': object_id,
                    'returnByValue': True,
                },
                session_id=session_id,
            )
            r = rect_result['result']['value']
            return r['x'] + r['w'] / 2, r['y'] + r['h'] / 2
        except Exception:
            pass

        return None, None

    def _get_modifier_flags(self, modifiers) -> int:
        """Convert modifier list to CDP modifier flags."""
        if not modifiers:
            return 0
        flags = 0
        for m in modifiers:
            if m == 'Alt':
                flags |= 1
            elif m == 'Control':
                flags |= 2
            elif m == 'Meta':
                flags |= 4
            elif m == 'Shift':
                flags |= 8
        return flags

    async def _ensure_session(self) -> str:
        """Ensure we have a valid session ID."""
        if self._session_id is None:
            cdp_session = await self._browser_session.get_or_create_cdp_session()
            self._session_id = cdp_session.session_id
        return self._session_id
