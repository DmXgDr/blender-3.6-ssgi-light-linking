# Blender 3.6 SSGI：EEVEE 灯光链接与阴影链接

基于 **Blender 3.6.2 + SSGI Native 1.17a** 的非官方 Windows x64 构建，保留 EEVEE Legacy，加入原生灯光链接和阴影链接。

版本 **R4**，程序源码修订 `112f061a999b`。

[下载便携版](https://github.com/DmXgDr/blender-3.6-ssgi-light-linking/releases/latest) · [中文使用说明](docs/使用说明.md) · [配置说明](docs/配置说明.md) · [验证范围](docs/验证记录.md) · [构建说明](docs/构建说明.md) · [来源与许可](NOTICE.md)

## 下载与启动

1. 在 Releases 下载 `Blender-3.6.2-SSGI-LightLinking-R4-Windows-x64.zip`，完整解压。
2. 双击根目录 **blender.exe**，或 **Start-Blender.cmd**。无需安装。
3. 默认读取当前使用者的 `%APPDATA%\Blender Foundation\Blender\3.6\`，包括已有偏好、启动文件和用户插件。

默认与电脑上的普通 Blender 3.6 共用用户配置。保存偏好或启动文件会写入这个共享目录。若需完全独立配置，可自行创建包内 `3.6/config` 后启动；详见配置说明。

使用 Blender 3.6 官方色彩管理，包含 Standard、Filmic 等显示变换。

## 主要功能

- 物体/集合级灯光链接与阴影链接，包含、排除及共享集合。
- 原生属性面板、大纲拖放、排序、撤销/重做。
- `Ctrl+L` 将活动灯的灯光链接、阴影链接或两者共享给选中的其他灯。
- EEVEE 独立 Shadow 通道适配。
- Screen Space Ray Tracing / SSGI 高光链接修复与历史缓存刷新。
- 修复连续渲染时未初始化的 SSGI 缓冲导致异常高亮、画面发白的问题。
- 物体体积雾的直接受光链接，支持独立重叠体积。
- 链接列表保留对象/集合实际名称，不再把英文数据名称误翻译。

## 已知范围

- 仅面向 EEVEE Legacy；**Cycles 未编入**。
- 不支持把发光网格作为具有同等链接能力的灯光。
- 体积受光链接已实现；体积作为遮挡介质的独立阴影链接没有新增。
- 排除直接光不等于排除世界光、自发光、其他灯、AO 或所有间接反弹。
- 关系掩码存在容量限制，超限应减少独立关系组合；不是简单的物体/灯光数量上限。
- 新合成器节点、辉光一致性改造尚未实现。

建议将使用新功能的工程另存副本。普通官方 3.6 不包含这些功能，不能依靠它完整保留自定义链接设置。

## 源码

`blender/` 为修改后的完整 Blender 源码快照（含分发所用的 Python 插件源码），`patches/` 保留相对官方 3.6.2 的差异及 SSGI 来源补丁。构建工具、依赖来源和发布处理见构建说明。
