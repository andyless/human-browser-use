"""HumanActionWatchdog - DefaultActionWatchdog with human-like behavior."""

import asyncio
import logging
import math
import random

from browser_use.browser.watchdogs.default_action_watchdog import DefaultActionWatchdog
from browser_use.browser.views import BrowserError

from human_browser_use.config import HumanBehaviorConfig
from human_browser_use.behavior.mouse_trajectory import MouseTrajectory
from human_browser_use.behavior.keyboard_dynamics import KeyboardDynamics
from human_browser_use.behavior.scroll_dynamics import ScrollDynamics
from human_browser_use.behavior.timing import ActionTiming

logger = logging.getLogger(__name__)


class HumanActionWatchdog(DefaultActionWatchdog):
    """DefaultActionWatchdog with human-like mouse movement, typing, and scrolling.

    Overrides the core implementation methods to add:
    - Realistic mouse trajectories (WindMouse + Bezier) instead of instant teleport
    - Lognormal typing delays with typo simulation instead of fixed delays
    - Inertia-based scrolling instead of instant scroll
    """

    # Store current mouse position for trajectory generation
    _mouse_x: float = 0.0
    _mouse_y: float = 0.0
    _trajectory: MouseTrajectory | None = None
    _keyboard: KeyboardDynamics | None = None
    _scroll: ScrollDynamics | None = None
    _timing: ActionTiming | None = None
    _human_config: HumanBehaviorConfig | None = None

    def __init__(self, human_config: HumanBehaviorConfig | None = None, **kwargs):
        super().__init__(**kwargs)
        config = human_config or HumanBehaviorConfig()
        object.__setattr__(self, '_human_config', config)
        object.__setattr__(self, '_trajectory', MouseTrajectory(config.mouse))
        object.__setattr__(self, '_keyboard', KeyboardDynamics(config.keyboard))
        object.__setattr__(self, '_scroll', ScrollDynamics(config.scroll))
        object.__setattr__(self, '_timing', ActionTiming(config.timing))
        object.__setattr__(self, '_mouse_x', 0.0)
        object.__setattr__(self, '_mouse_y', 0.0)

    async def _move_mouse_human(self, target_x: float, target_y: float, cdp_session, session_id: str):
        """Move mouse along a human-like trajectory with realistic speed profile.

        Uses generate_with_timing() for per-point delays that mimic
        real human acceleration/deceleration patterns.
        """
        config = object.__getattribute__(self, '_human_config')
        if not config.enable_human_mouse:
            # Fall back to instant move
            await cdp_session.cdp_client.send.Input.dispatchMouseEvent(
                params={'type': 'mouseMoved', 'x': target_x, 'y': target_y},
                session_id=session_id,
            )
            object.__setattr__(self, '_mouse_x', target_x)
            object.__setattr__(self, '_mouse_y', target_y)
            return

        trajectory = object.__getattribute__(self, '_trajectory')
        mouse_x = object.__getattribute__(self, '_mouse_x')
        mouse_y = object.__getattribute__(self, '_mouse_y')

        timed_points = trajectory.generate_with_timing(mouse_x, mouse_y, target_x, target_y)

        if not timed_points:
            return

        for px, py, delay in timed_points:
            await cdp_session.cdp_client.send.Input.dispatchMouseEvent(
                params={'type': 'mouseMoved', 'x': px, 'y': py},
                session_id=session_id,
            )
            await asyncio.sleep(delay)

        object.__setattr__(self, '_mouse_x', target_x)
        object.__setattr__(self, '_mouse_y', target_y)

    async def _human_click(self, x: float, y: float, cdp_session, session_id: str):
        """Perform a human-like click: trajectory move + variable press duration."""
        config = object.__getattribute__(self, '_human_config')
        trajectory = object.__getattribute__(self, '_trajectory')

        # Apply random offset to click position
        if config.enable_human_mouse:
            dx = random.gauss(0, config.mouse.click_offset_sigma)
            dy = random.gauss(0, config.mouse.click_offset_sigma)
            click_x = x + dx
            click_y = y + dy
        else:
            click_x, click_y = x, y

        # Move mouse to target with trajectory
        await self._move_mouse_human(click_x, click_y, cdp_session, session_id)

        # Mouse down with timeout
        try:
            await asyncio.wait_for(
                cdp_session.cdp_client.send.Input.dispatchMouseEvent(
                    params={
                        'type': 'mousePressed',
                        'x': click_x,
                        'y': click_y,
                        'button': 'left',
                        'clickCount': 1,
                    },
                    session_id=session_id,
                ),
                timeout=3.0,
            )
            # Variable press duration
            press_duration = trajectory.get_press_duration()
            await asyncio.sleep(press_duration)
        except TimeoutError:
            logger.debug('Mouse down timed out, continuing...')

        # Mouse up with timeout
        try:
            await asyncio.wait_for(
                cdp_session.cdp_client.send.Input.dispatchMouseEvent(
                    params={
                        'type': 'mouseReleased',
                        'x': click_x,
                        'y': click_y,
                        'button': 'left',
                        'clickCount': 1,
                    },
                    session_id=session_id,
                ),
                timeout=5.0,
            )
        except TimeoutError:
            logger.debug('Mouse up timed out, continuing...')

    async def _click_element_node_impl(self, element_node) -> dict | None:
        """Override: Click element with human-like mouse trajectory and timing."""
        config = object.__getattribute__(self, '_human_config')

        if not config.enable_human_mouse:
            return await super()._click_element_node_impl(element_node)

        try:
            # Check if element is a file input or select dropdown
            tag_name = element_node.tag_name.lower() if element_node.tag_name else ''
            element_type = element_node.attributes.get('type', '').lower() if element_node.attributes else ''

            if tag_name == 'select':
                msg = f'Cannot click on <select> elements. Use dropdown_options(index={element_node.backend_node_id}) action instead.'
                return {'validation_error': msg}

            if tag_name == 'input' and element_type == 'file':
                msg = f'Cannot click on file input element (index={element_node.backend_node_id}). File uploads must be handled using upload_file_to_element action.'
                return {'validation_error': msg}

            # Get CDP client
            cdp_session = await self.browser_session.cdp_client_for_node(element_node)
            session_id = cdp_session.session_id
            backend_node_id = element_node.backend_node_id

            # Get viewport dimensions
            layout_metrics = await cdp_session.cdp_client.send.Page.getLayoutMetrics(session_id=session_id)
            viewport_width = layout_metrics['layoutViewport']['clientWidth']
            viewport_height = layout_metrics['layoutViewport']['clientHeight']

            # Scroll into view
            try:
                await cdp_session.cdp_client.send.DOM.scrollIntoViewIfNeeded(
                    params={'backendNodeId': backend_node_id}, session_id=session_id
                )
                await asyncio.sleep(0.05)
            except Exception as e:
                logger.debug(f'Failed to scroll element into view: {e}')

            # Get element coordinates
            element_rect = await self.browser_session.get_element_coordinates(backend_node_id, cdp_session)

            quads = []
            if element_rect:
                x, y, w, h = element_rect.x, element_rect.y, element_rect.width, element_rect.height
                quads = [[x, y, x + w, y, x + w, y + h, x, y + h]]

            if not quads:
                # Fall back to JS click
                logger.warning('Could not get element geometry, falling back to JavaScript click')
                try:
                    result = await cdp_session.cdp_client.send.DOM.resolveNode(
                        params={'backendNodeId': backend_node_id}, session_id=session_id
                    )
                    assert 'object' in result and 'objectId' in result['object']
                    object_id = result['object']['objectId']
                    await cdp_session.cdp_client.send.Runtime.callFunctionOn(
                        params={'functionDeclaration': 'function() { this.click(); }', 'objectId': object_id},
                        session_id=session_id,
                    )
                    await asyncio.sleep(0.05)
                    return None
                except Exception as js_e:
                    raise Exception(f'Failed to click element: {js_e}')

            # Find best visible quad
            best_quad = quads[0]
            center_x = sum(best_quad[i] for i in range(0, 8, 2)) / 4
            center_y = sum(best_quad[i] for i in range(1, 8, 2)) / 4
            center_x = max(0, min(viewport_width - 1, center_x))
            center_y = max(0, min(viewport_height - 1, center_y))

            # Check for occlusion
            is_occluded = await self._check_element_occlusion(backend_node_id, center_x, center_y, cdp_session)
            if is_occluded:
                logger.debug('Element is occluded, falling back to JavaScript click')
                try:
                    result = await cdp_session.cdp_client.send.DOM.resolveNode(
                        params={'backendNodeId': backend_node_id}, session_id=session_id
                    )
                    assert 'object' in result and 'objectId' in result['object']
                    object_id = result['object']['objectId']
                    await cdp_session.cdp_client.send.Runtime.callFunctionOn(
                        params={'functionDeclaration': 'function() { this.click(); }', 'objectId': object_id},
                        session_id=session_id,
                    )
                    await asyncio.sleep(0.05)
                    return None
                except Exception as js_e:
                    raise Exception(f'Failed to click occluded element: {js_e}')

            # >>> HUMAN-LIKE CLICK <<<
            try:
                # Pre-action delay
                timing = object.__getattribute__(self, '_timing')
                await asyncio.sleep(timing.get_pre_action_delay())

                await self._human_click(center_x, center_y, cdp_session, session_id)

                logger.debug(f'Clicked element with human trajectory at ({center_x:.0f}, {center_y:.0f})')
                return {'click_x': center_x, 'click_y': center_y}
            except Exception as e:
                logger.warning(f'Human click failed: {e}, falling back to JS click')
                try:
                    result = await cdp_session.cdp_client.send.DOM.resolveNode(
                        params={'backendNodeId': backend_node_id}, session_id=session_id
                    )
                    assert 'object' in result and 'objectId' in result['object']
                    object_id = result['object']['objectId']
                    await cdp_session.cdp_client.send.Runtime.callFunctionOn(
                        params={'functionDeclaration': 'function() { this.click(); }', 'objectId': object_id},
                        session_id=session_id,
                    )
                    await asyncio.sleep(0.1)
                    return None
                except Exception as js_e:
                    raise Exception(f'Failed to click element: {e}')
            finally:
                try:
                    cdp_session = await asyncio.wait_for(
                        self.browser_session.get_or_create_cdp_session(focus=True), timeout=3.0
                    )
                    await asyncio.wait_for(
                        cdp_session.cdp_client.send.Runtime.runIfWaitingForDebugger(session_id=cdp_session.session_id),
                        timeout=2.0,
                    )
                except (TimeoutError, Exception):
                    pass

        except BrowserError:
            raise
        except Exception as e:
            element_info = f'<{element_node.tag_name or "unknown"}'
            if element_node.backend_node_id:
                element_info += f' index={element_node.backend_node_id}'
            element_info += '>'
            error_detail = f'Failed to click element {element_info}.'
            if element_node.backend_node_id:
                error_detail += f' Index [{element_node.backend_node_id}] may be stale.'
            raise BrowserError(message=f'Failed to click element: {str(e)}', long_term_memory=error_detail)

    async def _click_on_coordinate(self, coordinate_x: int, coordinate_y: int, force: bool = False) -> dict | None:
        """Override: Click at coordinates with human-like trajectory."""
        config = object.__getattribute__(self, '_human_config')

        if not config.enable_human_mouse:
            return await super()._click_on_coordinate(coordinate_x, coordinate_y, force)

        try:
            cdp_session = await self.browser_session.get_or_create_cdp_session()
            session_id = cdp_session.session_id

            # Pre-action delay
            timing = object.__getattribute__(self, '_timing')
            await asyncio.sleep(timing.get_pre_action_delay())

            await self._human_click(coordinate_x, coordinate_y, cdp_session, session_id)

            logger.debug(f'Human-clicked at ({coordinate_x}, {coordinate_y})')
            return {'click_x': coordinate_x, 'click_y': coordinate_y}
        except Exception as e:
            logger.error(f'Failed to click at ({coordinate_x}, {coordinate_y}): {e}')
            raise BrowserError(
                message=f'Failed to click at coordinates: {e}',
                long_term_memory=f'Failed to click at ({coordinate_x}, {coordinate_y}).',
            )

    async def _type_char_with_events(self, char: str, cdp_session, session_id: str):
        """Type a single character with proper key events."""
        if char == '\n':
            await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
                params={'type': 'keyDown', 'key': 'Enter', 'code': 'Enter', 'windowsVirtualKeyCode': 13},
                session_id=session_id,
            )
            await asyncio.sleep(0.001)
            await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
                params={'type': 'char', 'text': '\r', 'key': 'Enter'},
                session_id=session_id,
            )
            await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
                params={'type': 'keyUp', 'key': 'Enter', 'code': 'Enter', 'windowsVirtualKeyCode': 13},
                session_id=session_id,
            )
        else:
            modifiers, vk_code, base_key = self._get_char_modifiers_and_vk(char)
            key_code = self._get_key_code_for_char(base_key)

            await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
                params={
                    'type': 'keyDown', 'key': base_key, 'code': key_code,
                    'modifiers': modifiers, 'windowsVirtualKeyCode': vk_code,
                },
                session_id=session_id,
            )
            await asyncio.sleep(0.003)
            await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
                params={'type': 'char', 'text': char, 'key': char},
                session_id=session_id,
            )
            await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
                params={
                    'type': 'keyUp', 'key': base_key, 'code': key_code,
                    'modifiers': modifiers, 'windowsVirtualKeyCode': vk_code,
                },
                session_id=session_id,
            )

    async def _type_text_human(self, text: str, cdp_session, session_id: str):
        """Type text with human-like dynamics: lognormal delays, typo simulation."""
        config = object.__getattribute__(self, '_human_config')
        keyboard = object.__getattribute__(self, '_keyboard')
        keyboard.reset()

        i = 0
        while i < len(text):
            char = text[i]

            # Get human-like delay
            delay = keyboard.get_inter_key_delay(char)
            await asyncio.sleep(delay)

            # Possibly make a typo (only for regular alphanumeric chars)
            if char.isalpha() and keyboard.should_make_typo():
                typo_char = keyboard.get_typo_char(char)
                if typo_char:
                    # Type the wrong character
                    await self._type_char_with_events(typo_char, cdp_session, session_id)

                    # Pause (recognition delay)
                    await asyncio.sleep(keyboard.get_typo_pause())

                    # Press Backspace to delete the typo
                    await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
                        params={'type': 'keyDown', 'key': 'Backspace', 'code': 'Backspace', 'windowsVirtualKeyCode': 8},
                        session_id=session_id,
                    )
                    await asyncio.sleep(0.03)
                    await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
                        params={'type': 'keyUp', 'key': 'Backspace', 'code': 'Backspace', 'windowsVirtualKeyCode': 8},
                        session_id=session_id,
                    )
                    await asyncio.sleep(0.05)

            # Type the correct character
            await self._type_char_with_events(char, cdp_session, session_id)
            i += 1

    async def _type_to_page(self, text: str):
        """Override: Type text to page with human-like dynamics."""
        config = object.__getattribute__(self, '_human_config')

        if not config.enable_human_keyboard:
            return await super()._type_to_page(text)

        try:
            cdp_session = await self.browser_session.get_or_create_cdp_session(target_id=None, focus=True)
            await self._type_text_human(text, cdp_session, cdp_session.session_id)
        except Exception as e:
            raise Exception(f'Failed to type to page: {str(e)}')

    async def _input_text_element_node_impl(self, element_node, text: str, clear: bool = True, is_sensitive: bool = False) -> dict | None:
        """Override: Input text with human-like keyboard dynamics.

        Replaces the fixed 0.001s/0.005s delays with lognormal distribution delays
        and optionally simulates typos.
        """
        config = object.__getattribute__(self, '_human_config')

        if not config.enable_human_keyboard:
            return await super()._input_text_element_node_impl(element_node, text, clear, is_sensitive)

        try:
            cdp_client = self.browser_session.cdp_client
            cdp_session = await self.browser_session.cdp_client_for_node(element_node)
            backend_node_id = element_node.backend_node_id
            input_coordinates = None

            # Scroll element into view
            try:
                await cdp_session.cdp_client.send.DOM.scrollIntoViewIfNeeded(
                    params={'backendNodeId': backend_node_id}, session_id=cdp_session.session_id
                )
                await asyncio.sleep(0.01)
            except Exception as e:
                error_str = str(e)
                if 'Node is detached from document' not in error_str:
                    logger.debug(f'Failed to scroll element into view: {e}')

            # Get object ID
            result = await cdp_client.send.DOM.resolveNode(
                params={'backendNodeId': backend_node_id}, session_id=cdp_session.session_id
            )
            assert 'object' in result and 'objectId' in result['object']
            object_id = result['object']['objectId']

            # Get coordinates
            coords = await self.browser_session.get_element_coordinates(backend_node_id, cdp_session)
            if coords:
                center_x = coords.x + coords.width / 2
                center_y = coords.y + coords.height / 2
                is_occluded = await self._check_element_occlusion(backend_node_id, center_x, center_y, cdp_session)
                if not is_occluded:
                    input_coordinates = {'input_x': center_x, 'input_y': center_y}

            # Focus element
            focused_successfully = await self._focus_element_simple(
                backend_node_id=backend_node_id, object_id=object_id,
                cdp_session=cdp_session, input_coordinates=input_coordinates,
            )

            # Handle date/time inputs with direct assignment
            requires_direct_assignment = self._requires_direct_value_assignment(element_node)
            if requires_direct_assignment:
                await self._set_value_directly(element_node, text, object_id, cdp_session)
                return input_coordinates

            # Clear existing text
            if clear:
                cleared = await self._clear_text_field(object_id=object_id, cdp_session=cdp_session)
                if not cleared:
                    logger.warning('Text field clearing failed, typing may append')

            # >>> HUMAN-LIKE TYPING <<<
            if is_sensitive:
                logger.debug('Typing <sensitive> with human dynamics')
            else:
                logger.debug(f'Typing "{text}" with human dynamics')

            # Handle contenteditable first-char bug
            _attrs = element_node.attributes or {}
            _is_contenteditable = _attrs.get('contenteditable') in ('true', '') or (
                _attrs.get('role') == 'textbox' and element_node.tag_name not in ('input', 'textarea')
            )
            _check_first_char = _is_contenteditable and len(text) > 0 and clear

            await self._type_text_human(text, cdp_session, cdp_session.session_id)

            # Check first char for contenteditable
            if _check_first_char:
                check_result = await cdp_session.cdp_client.send.Runtime.evaluate(
                    params={'expression': 'document.activeElement.textContent'},
                    session_id=cdp_session.session_id,
                )
                content = check_result.get('result', {}).get('value', '')
                if text[0] not in content:
                    logger.debug(f'First char dropped (leaf-start bug), retyping')
                    await self._type_char_with_events(text[0], cdp_session, cdp_session.session_id)

            # Trigger framework events
            await self._trigger_framework_events(object_id=object_id, cdp_session=cdp_session)

            # Read back value for verification
            if not is_sensitive:
                try:
                    await asyncio.sleep(0.05)
                    readback_result = await cdp_session.cdp_client.send.Runtime.callFunctionOn(
                        params={
                            'objectId': object_id,
                            'functionDeclaration': 'function() { return this.value !== undefined ? this.value : this.textContent; }',
                            'returnByValue': True,
                        },
                        session_id=cdp_session.session_id,
                    )
                    actual_value = readback_result.get('result', {}).get('value')
                    if actual_value is not None:
                        if input_coordinates is None:
                            input_coordinates = {}
                        input_coordinates['actual_value'] = actual_value
                except Exception:
                    pass

            # Auto-retry on concatenation mismatch
            if clear and not is_sensitive and input_coordinates and 'actual_value' in input_coordinates:
                actual_value = input_coordinates['actual_value']
                if (
                    isinstance(actual_value, str)
                    and actual_value != text
                    and len(actual_value) > len(text)
                    and (actual_value.endswith(text) or actual_value.startswith(text))
                ):
                    logger.info(f'Concatenation detected, auto-retrying')
                    try:
                        retry_result = await cdp_session.cdp_client.send.Runtime.callFunctionOn(
                            params={
                                'objectId': object_id,
                                'functionDeclaration': """
                                    function(newValue) {
                                        if (this.value !== undefined) {
                                            var desc = Object.getOwnPropertyDescriptor(
                                                HTMLInputElement.prototype, 'value'
                                            ) || Object.getOwnPropertyDescriptor(
                                                HTMLTextAreaElement.prototype, 'value'
                                            );
                                            if (desc && desc.set) { desc.set.call(this, newValue); }
                                            else { this.value = newValue; }
                                        } else if (this.isContentEditable) {
                                            this.textContent = newValue;
                                        }
                                        this.dispatchEvent(new Event('input', { bubbles: true }));
                                        this.dispatchEvent(new Event('change', { bubbles: true }));
                                        return this.value !== undefined ? this.value : this.textContent;
                                    }
                                """,
                                'arguments': [{'value': text}],
                                'returnByValue': True,
                            },
                            session_id=cdp_session.session_id,
                        )
                        retry_value = retry_result.get('result', {}).get('value')
                        if retry_value is not None:
                            input_coordinates['actual_value'] = retry_value
                    except Exception:
                        pass

            return input_coordinates

        except Exception as e:
            logger.error(f'Failed to input text: {e}')
            raise BrowserError(f'Failed to input text into element: {repr(element_node)}')

    async def _scroll_with_cdp_gesture(self, pixels: int) -> bool:
        """Override: Scroll with human-like inertia physics instead of instant scroll."""
        config = object.__getattribute__(self, '_human_config')

        if not config.enable_human_scroll:
            return await super()._scroll_with_cdp_gesture(pixels)

        try:
            cdp_session = await self.browser_session.get_or_create_cdp_session()
            cdp_client = cdp_session.cdp_client
            session_id = cdp_session.session_id

            # Get viewport dimensions
            if self.browser_session._original_viewport_size:
                viewport_width, viewport_height = self.browser_session._original_viewport_size
            else:
                layout_metrics = await cdp_client.send.Page.getLayoutMetrics(session_id=session_id)
                viewport_width = layout_metrics['layoutViewport']['clientWidth']
                viewport_height = layout_metrics['layoutViewport']['clientHeight']

            center_x = viewport_width / 2
            center_y = viewport_height / 2

            # Generate human-like scroll events
            scroll_dynamics = object.__getattribute__(self, '_scroll')
            events = scroll_dynamics.generate_scroll_events(pixels)

            # First move mouse to center of viewport
            await self._move_mouse_human(
                center_x + random.uniform(-50, 50),
                center_y + random.uniform(-50, 50),
                cdp_session, session_id,
            )

            # Dispatch scroll events
            for evt in events:
                if evt['delay'] > 0:
                    await asyncio.sleep(evt['delay'])

                await cdp_client.send.Input.dispatchMouseEvent(
                    params={
                        'type': 'mouseWheel',
                        'x': center_x,
                        'y': center_y,
                        'deltaX': 0,
                        'deltaY': evt['delta_y'],
                    },
                    session_id=session_id,
                )

            logger.debug(f'Human-scrolled {pixels}px with {len(events)} events')
            return True

        except Exception as e:
            logger.debug(f'Human scroll failed: {e}, falling back')
            return False
