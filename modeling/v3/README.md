# 小小萌 V3 制作工作区

本轮继续头部与发型工程，重建身体、服装、手部和鞋履。最终仍按原创立绘的实际模型截图对照要求制作；此目录保存制作源代码。

## 当前制作内容

- 收窄脸部和眼距，修正头部朝向，调整右侧刘海遮挡。
- 衣身、袖窿、袖子和折返袖口共用控制网格边界。
- 裤腰、骨盆、裆部和两条裤腿连接成连续表面，裤脚使用局部方向性折叠。
- 手掌、四指和拇指连接；鞋底、鞋面、鞋舌和鞋带按低帮轮廓重建。
- 增加内衬层次、腰口、衣摆印花贴合、卡通明暗和反向外壳轮廓线。

## 参考资料

仓库中保存了后续角色设定图。最初的 P1 原始立绘没有随上次工作归档保存为本地文件，后续按 P1 做精确截图对齐需要恢复该图片。

## 重建（Blender 4.3.2）

在本目录执行：

```sh
blender -b --factory-startup -t 4 --python-exit-code 1 --python tools/build_head.py -- --with-hair
blender -b models/head-work.blend -t 4 --python-exit-code 1 --python tools/build_full.py --python tools/inspect_surfaces.py
blender -b models/character-geometry.blend -t 4 --python-exit-code 1 --python tools/stylize_work.py
```

首个脚本会从仓库的 `assets/xiaoxiaomeng-character-model-sheet.png` 准备本地参考文件。网格、图像与工作工程输出至 `models/`，真实三维检查图输出至 `renders/`。这两个输出目录保留在制作环境中，源码提交不生成最终三格式交付。

当前保存的原生工作工程为 `character-geometry.blend` 和 `character-toon-work.blend`。造型、原图对齐、最终 UV、绑定与三格式导出仍继续在后续步骤完成。
