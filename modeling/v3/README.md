# 小小萌 V3 制作工作区

本轮继续头部与发型工程，重建身体、服装、手部和鞋履。最终仍按原创立绘的实际模型截图对照要求制作；此目录保存制作源代码。

## 当前模型快照

以下图片由当前 Blender 三维工程直接渲染，随制作更新同步提交。

| 正面 | 四分之三 | 背面 |
| --- | --- | --- |
| ![正面](previews/front.png) | ![四分之三](previews/quarter.png) | ![背面](previews/back.png) |

[快照来源与渲染时间](previews/snapshot.json)

## 当前制作内容

- 调整眼睑开口与睫毛，减轻鼻唇凸起，单独设置脸部明暗。
- 减薄前发束，补发根包覆，增加后发分层、不同弯向与发尾。
- 改为非对称开襟和衣摆轮廓，修改内搭领口、袖子和裤装褶皱。
- 保持衣身与袖子连接，单独标记折返袖口的白色面料；补充帽口与衣片接缝、扣件和袖章。
- 调整鞋底与鞋面的衔接；衣摆印花使用设定图中的细节图案，并增加贴合网格密度。

眼神、发型轮廓、领帽裁片和服装垂坠仍在继续修整。这里的源码与快照保存制作进度。

## 参考资料

仓库中保存了后续角色设定图。最初的 P1 原始立绘没有随上次工作归档保存为本地文件，后续按 P1 做精确截图对齐需要恢复该图片。

## 重建（Blender 4.3.2）

在本目录执行：

```sh
blender -b --factory-startup -t 4 --python-exit-code 1 --python tools/build_head.py -- --with-hair
blender -b models/head-work.blend -t 4 --python-exit-code 1 --python tools/build_full.py --python tools/inspect_surfaces.py
blender -b models/character-geometry.blend -t 4 --python-exit-code 1 --python tools/stylize_work.py
```

首个脚本会从仓库的 `assets/xiaoxiaomeng-character-model-sheet.png` 准备本地参考文件。网格、图像与工作工程输出至 `models/`，真实三维检查图输出至 `renders/`。最后一个脚本在完成三视角渲染并保存工程后，自动将快照和来源记录同步到 `previews/`，供根 README 和本页显示。每次制作更新须将新的 `previews/` 一起提交。`models/` 和 `renders/` 保留在制作环境中，源码提交不生成最终三格式交付。

当前保存的原生工作工程为 `character-geometry.blend` 和 `character-toon-work.blend`。造型、原图对齐、最终 UV、绑定与三格式导出仍继续在后续步骤完成。
