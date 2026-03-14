# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

基于 [browser-use](https://github.com/browser-use/browser-use) 项目的改进版本，核心目标是让浏览器自动化操作更像真人，难以被反自动化检测系统识别。

关键改进方向：
- **自动化特征隐藏**：消除 WebDriver、CDP 等浏览器自动化指纹
- **真实鼠标操作**：模拟人类鼠标移动轨迹（贝塞尔曲线、随机偏移、加速减速）
- **人类化点击**：点击位置随机偏移、按压时长变化、双击/拖拽等
- **键盘事件模拟**：真实的按键间隔、打字节奏、偶尔的修正行为
- **行为模式**：随机滚动、停顿、阅读时间等拟人化行为

## Environment Setup

- **Proxy**: Local proxy at `127.0.0.1:7897` is required for network access. Run `cc.bat` to launch Claude Code with the proxy configured.
- **Language**: All user-facing communication should be in 简体中文 (Simplified Chinese).
