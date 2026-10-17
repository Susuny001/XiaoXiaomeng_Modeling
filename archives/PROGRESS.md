# 小小萌工作归档

状态：按用户要求暂停制作，保留当前进度。

## 暂停点

- 已重新建立连续的头部控制网格、眼窝开口及眼睑环线，并塑造鼻唇、脸颊和下颌转折。
- 已重新制作非对称刘海、侧发、后发、挑染、发夹和发带。
- 当前工程为头部与发型制作阶段；身体、服装、鞋履和最终材质尚待后续制作。
- 后续仍以真实三维模型截图对照原创立绘，完成造型对照后再做最终三格式导出和预览器。

## 工程文件

- `models/head-work.blend`：当前 Blender 4.3.2 工作工程，已打包眼睛绘制图和参考图。
- `models/head-work.blend1`：上一次保存的工程备份。
- `tools/build_head.py`：头部控制网格及眼睑制作脚本。
- `tools/build_hair.py`：发束、挑染、发夹与发带制作脚本。
- `assets/character-sheet.png`：已保存的角色设定图。
- `renders/`：当前工程的真实多视角渲染和参考图检查视图。
- `research/`：已读取的 MToon 材质规范资料。

## 继续时

在解压目录执行：

```sh
blender -b --factory-startup -t 4 --python tools/build_head.py -- --with-hair
```

也可直接用 Blender 打开 `models/head-work.blend` 继续编辑。原创 P1 立绘仍在原会话附件中；本地保存的是后续设定图，继续进行原始立绘精确对照时需恢复 P1 原文件。

该压缩包是工作进度归档，保存当前工程和重建脚本。
