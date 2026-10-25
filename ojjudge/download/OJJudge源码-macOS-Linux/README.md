# OJJudge 评测软件

本地 OI（信息学竞赛）评测工具，用图形界面一键评测 C++ 题解。

## 功能

- **单题评测**：一个源码 + 一个数据目录，一键出分（AC/WA/TLE、得分、用时、期望/实际）。
- **多题评测**：添加多道题，一键全部评测，结果按题分组汇总（评测异常不中断后续题目）。
- **对拍**：主程序 vs 暴力/标程，用随机数据找 bug；遇到错误跑完全部轮、一次性汇总。
- **造数据**：自动生成随机 `.in` 与 `.out`。
- **随机数据**：填输入格式/范围/数量 + AC 代码，自动生成可测数据（无需手写生成器）。
- **多编程语言**：C++ / Python / Java 一键切换（g++ 编译 / 解释器直跑 / javac + java）。
- **界面语言切换**：底栏最右侧「界面: 中文 / English」，一键把标签页、按钮、表头、分区标题与状态提示整体切成英文，切回中文完全还原。
- **自动导入**：启动时自动读取 exe 同目录的 `题目导入.json`，填入多题列表。
- **记录页**：评测记录自动保存（单题/多题/对拍/造数据/随机数据），软件内可回看历史；内置改动日志。

## 使用

- Windows 用户建议直接下载 `OJJudge评测.exe`（免安装，无需 Python 环境）。
- 运行 `OJJudge评测.exe`（Windows）。
- 默认编译器：`C:\mingw64\bin\g++.exe`（可在界面里改）。
- macOS / Linux：直接 `python3 ojjudge.py`，并把界面里的编译器路径改成本机的 `clang++`（macOS）或 `g++`（Linux）。
- 评测临时文件只产生于数据目录内（`<题名>.in` / `<题名>.out`），完成后自动清理。

## ⚠️ 运行源码版的前提：Python 必须带 tkinter

源码版用 Python 3 标准库 tkinter 做界面，**不是所有 Python 发行版都带它**：

- **Windows**：装 [python.org 官方版 Python](https://www.python.org/downloads/)（自带 tkinter）。如果 `python ojjudge.py` 报 `No module named 'tkinter'`，说明当前 Python 不带 tkinter——它不能用 pip 装，只能换官方版，或用 exe。
- **macOS**：用 python.org 官方版（自带 tkinter）；Homebrew 的 python 需先 `brew install python-tk`。
- **Linux（Debian/Ubuntu）**：`sudo apt install python3-tk`。

检测方法：`python -c "import tkinter"` 不报错即可跑。

## 数据约定

- 数据目录下放 `*.in`（输入）与同名 `.out`（优先）/ `.ans`（期望输出）。
- 评测同时支持两种写法：`freopen("<题名>.in/.out")` 文件读写，以及 `cin/cout` 标准输入输出（评测时自动喂 stdin、捕获 stdout）。

## 使用说明书

完整功能与操作说明见官网「使用说明」页：<https://huake-counter.app.workbuddy.host/guide.html>

## 技术

- Python 3 + tkinter（ttk 美化），PyInstaller 打包为单文件 exe。
- 评测线程安全：工作线程不碰界面控件，通过队列由主线程刷新。

## 改动记录

见软件内「记录」→「改动日志」。
