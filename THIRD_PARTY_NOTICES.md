# 第三方声明

## 代码

本仓库中自行编写的应用代码、构建脚本与测试代码以 MIT 许可证发布，见 `LICENSE`。

## 字体

`src/common/senren-text.otf` 是 Noto Sans Mono CJK SC 的子集，按 **SIL Open Font License 1.1** 使用，许可证全文见 `licenses/NotoSansCJK-OFL.txt`。子集只保留本项目文本与界面实际使用的 3,542 个码点。

构建设置：`desubroutinize=True`、`hinting=False`，并把子程序全部内联；原因是设备端 FreeType 无法执行部分 CFF 全局子程序调用，会把这些字形画成空框。

## 原作资源

`src/common/images/`、`src/common/faces/`、`src/common/opening/`、`src/common/*.opus`、`src/common/story/` 与 `converted/` 中的文本、图像、音乐来自《千恋＊万花》（Yuzu-Soft）的本地正版安装，仅用于本项目在自己的设备上阅读。

这些资源**不随 MIT 许可转授权**，版权归原作者与发行方所有。仓库不含原作安装包、归档文件或游戏可执行程序；重新分发或商用前请自行取得授权。

## 工具链

构建使用 aiot-toolkit 1.1.0（Vela 应用编译与打包）。转换脚本另有使用到 GARbro 的 TLG 解码与 FreeMote 的 PSB 反编译工具，这些工具不包含在本仓库中，需自行安装。
