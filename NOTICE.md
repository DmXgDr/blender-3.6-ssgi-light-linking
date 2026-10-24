# 来源、署名与许可

这是 Blender 的非官方修改构建，不代表 Blender Foundation 的发布或支持。

- Blender 官方基线：3.6.2，`e53e55951e7a81572d82d25f5d190fe5b130bdf3`，https://github.com/blender/blender 。
- SSGI Native 1.17a：原作者 `0451`；恢复自公开归档 https://github.com/illusionyy/goo-blender/tree/blender-v3.6.2-ssgi ，归档提交 `931de149733bb8e471bfe000c5159bcea79406e8`。原始发布补丁下载已失效，此处使用第三方源码归档；不宣称与所有流传的预编译 SSGI 包完全相同。
- 灯光/阴影链接移植与修复最终源码：`112f061a999b`。以 Blender 4.5 的原生数据结构和交互为参考，加入 EEVEE Legacy 专用实现。
- 色彩管理使用 Blender 3.6.2 官方 OCIO 配置和 LUT，保留上游作者声明及 `ocio-license.txt`。

Blender 源码的许可见 `COPYING` 及各文件 SPDX 标识；分发依赖与字体等见程序包 `license/`。Python 插件、OCIO、第三方库和其他资产按各自原有许可证分发，保留其署名与许可文本，不统一改写为本项目许可。

完整修改后 Blender 源码位于 `blender/`，完整差异位于 `patches/`，公开发布另附源码 ZIP。第三方依赖的版本/下载位置及构建方式见构建说明。
