# 《千恋＊万花》· REDMI Watch 5 基础版 0.1.9

这是 **0.1.9** 的源码快照，由 OpenAI Codex 交付，为 0.1.10 之前的基础版正式版本。屏幕 432×514，包名 `com.codex.senren.rw5`。

- 安装包 **24,935,441 字节**，SHA-256 `5c0252d414263d9251afc10e561fe66f44d6001778c3f4f73637afc98a684e5b`
- 源码 ZIP 25,002,060 字节，3,124 个文件
- 正式版安装包与源码见 Releases 的 **v0.1.9**

## 本版内容

- 86 个剧情脚本、501 个控制节点、45,186 条中文文本、19 个选项、7 个结局。
- 标题菜单（五项左对齐）、标题原曲、序章 OP（108 秒 / 648 帧 / 6 fps / 固定位置）。
- 30 个存读档栏位、路线与章节目录、77 组 634 张 CG 鉴赏。
- 正文点击推进、拖动浏览；标准 24 px / 大字号 28 px；即时与逐字；慢／标准／快三档自动播放。
- 本版三项修复：32／26／24 安全区、逐字只显示首字符（原生列表复用问题）、67 句 72 处字面换行标记。

## 版本与开发者

| 版本 | 主要实现 |
| --- | --- |
| 0.1.0 – 0.1.9 | OpenAI Codex |
| 0.1.10 起 | DeepSeek Harness |

0.1.9 是 Codex 交付的最后正式版本。0.1.10 起在交接文档基础上继续，内容范围、图库结构、后日谈入口与字形渲染均在该阶段完成。

## 构建

```
npm install --prefix tools/compat-toolkit --ignore-scripts   # aiot-toolkit 1.1.0
node tools/build.cjs
node --test tests/*.test.cjs
python tools/audit-package.py
```

已有工具链时可设 `WATCH_COMPAT_TOOLKIT` 指向本地 `aiot-toolkit`。源码含已生成资源，可直接构建；原作安装目录不包含在仓库中。

## 说明

本快照只保留运行时源码、基础资源、构建脚本、测试与必要校验工具，不含原作归档、扩展补丁转换链、SDK、模拟器磁盘或私人签名密钥。

原作：[Yuzu-Soft 官方页面](https://www.yuzu-soft.com/products/senren/) · [Steam](https://store.steampowered.com/app/1144400/Senren_Banka/)。非官方移植，原作文本、图像、音乐与商标不随本项目许可转授权。

维护者：xuanyide（宣伊德）。
