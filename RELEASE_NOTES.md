# R4：标准配置目录便携包

基于 Blender 3.6.2 SSGI 灯光/阴影链接。R4 修复了连续渲染时 SSGI 读取未初始化显存、导致画面异常高亮的问题；已通过修复复现、SSRT 灯光/材质矩阵和体积链接回归。

## 下载

- **Blender-3.6.2-SSGI-LightLinking-R4-Windows-x64.zip**：完整解压后运行 blender.exe 或 Start-Blender.cmd。
- **Blender-3.6.2-SSGI-LightLinking-R4-Source.zip**：对应源码、补丁、构建/发布脚本与说明。
- **SHA256SUMS.txt**：下载完整性校验。

默认读取本机 `%APPDATA%\Blender Foundation\Blender\3.6\` 的已有配置。保存偏好将写入共享的 3.6 用户配置目录。

包含原生灯光/阴影链接、Ctrl+L 共享、拖放、独立 Shadow 通道、SSRT 高光与历史修复、体积直接受光链接和列表名称修复。使用 Blender 3.6 官方色彩管理。

支持 EEVEE Legacy；Cycles 和新版合成器功能未包含在此版本中。中文操作与验证范围见仓库文档。
