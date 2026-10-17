# 小小萌 · 角色模型交付

以原创小小萌立绘与已交付设定图为参考制作的风格化三维角色。未展示的背部、衣内与鞋底按连续结构补全；此模型是依据图片进行的三维设计延展，并非三维扫描。

## 文件

| 文件 | 用途 |
| --- | --- |
| [models/xiaoxiaomeng.glb](models/xiaoxiaomeng.glb) | 浏览器、引擎、三维查看器；内嵌 PBR 材质与织物法线图 |
| [models/xiaoxiaomeng.fbx](models/xiaoxiaomeng.fbx) | 导入常见建模/动画软件；基础变形骨架，嵌入纹理 |
| [models/xiaoxiaomeng.blend](models/xiaoxiaomeng.blend) | Blender 4.3.2 原生可编辑工程；按部件分集合，保留细分等修改器、灯光、相机与打包参考图 |
| [index.html](index.html) / `viewer/` | 自带依赖的交互预览器，无需账号或远程 CDN |
| [renders/](renders/) | 角色全身、正面、背面、面部以及浏览器实机截图 |
| [assets/xiaoxiaomeng-character-model-sheet.png](assets/xiaoxiaomeng-character-model-sheet.png) | 原先交付的角色设定图 |

## 打开预览器

下载完整交付 ZIP 并**解压整个文件夹**，不要只下载 `index.html`。

**最方便：双击 `PREVIEW.html`。** 这个文件内嵌整个 GLB、材质和查看器代码，不需要安装 Python，不访问远程 CDN，可以离线旋转查看。第一次打开会解析模型，稍候即可。

如果需要通过本地服务器运行分文件版本：

1. 安装 Python 3（如电脑已有则无需重复安装）。
2. Windows 双击 `START_PREVIEW.bat`；macOS / Linux 在解压目录运行 `sh START_PREVIEW.sh`。也可直接运行 `python3 START_PREVIEW.py`。
3. 启动器自动打开浏览器。保持终端窗口开启，结束时按 Ctrl+C。

预览器支持拖动旋转、滚轮缩放、右键平移；正/侧/背视角；透视与正交；自动转台；材质/素模/线框；头发/外套/配件/鞋履显隐；骨架查看；保存当前画面以及三个格式下载。依赖已存放于 `viewer/vendor`，启动后不需要下载外部 JavaScript。

不要双击 HTML 通过 `file://` 打开：浏览器会限制模型读取。也可以在项目目录运行 `python3 -m http.server 8080`，然后在浏览器访问该服务器。

## 模型结构

- 使用米制坐标。原生 Blender 工程 Z 向上、角色面向 -Y；GLB 自动转换为 Y 向上。
- 约 1.78 米高的 A 姿态。原画没有实际身高，数值为制作约定，可以整体等比缩放。
- 分层脸部与眼睛：成型下颌与面颊、弧面杏仁眼、金黄绿虹膜、径向虹膜纤维、瞳孔、高光、上下眼线、鼻唇与耳部。
- 成束头发：前刘海、两侧挑染、侧发、后脑层、长后发、双交叉发夹、绿色布带与缝线。
- 服装：开襟白外套、黑色内衬、连帽、独立领片、袖口、分片接缝、拉链齿、抽绳、金属扣眼与绳头、衣摆印花、单侧上臂袖标。
- 裤装与鞋：工装裤与连续布褶、口袋、裤腰、裤袢、右侧工装袋及黄绿垂带；分层鞋底、鞋面、鞋舌、独立鞋带和金属孔、蝴蝶结、鞋后提带及底部防滑块。
- 34 根基础 FK 骨骼，包含躯干、四肢、手指、脚与后发；每个模型网格有权重。
- PBR 材质、UV 坐标、内嵌的织物微表面法线图。UV 使用按表面投射的重叠坐标，适合当前平铺材质；它不是为手绘贴图或独占烘焙整理的无重叠 UV 图集。

## 实际适用范围

这是分部件制作、可继续精修的风格化角色模型，针对静态展示、观察、继续建模及基础 FK 姿态。没有面部表情形态键、口腔内部、IK 操作器、动作库、动态头发/布料模拟，也未做游戏低模优化或复杂动作碰撞修正。服装与发束仍是独立网格，不应将基础骨架等同于完成商业动画角色绑定。

## 可复现与验证

```sh
# 完整重建（Blender 4.3.2）
blender -b --factory-startup -t 4 --python tools/build_character.py
# 只建模并导出，不渲染
blender -b --factory-startup -t 4 --python tools/build_character.py -- --no-render
# 重新渲染已保存工程
blender -b models/xiaoxiaomeng.blend -t 4 --python tools/render_character.py
# 独立重导出
blender -b models/xiaoxiaomeng.blend -t 4 --python tools/export_character.py
# 三种格式重新载入、尺寸/骨架/权重与关节变形检查
blender -b --factory-startup -t 4 --python tools/validate_models.py
```

`tools/validate_viewer.py` 是 Playwright 浏览器验收脚本，需要先在 8002 端口启动项目服务器。`tools/validate_glb.cjs` 使用 Khronos `gltf-validator` 检查 GLB。

实测结果记录在 `models/roundtrip-validation.json`、`models/gltf-validation.json` 和 `viewer/acceptance.json`。模型统计见 `models/manifest.json`。不把缺失功能当作已测试功能。

GLB 的 Khronos 格式校验：0 错误、0 警告（信息项为未使用 UV / 切线属性）。三格式回读均为 510 个角色网格、34 根骨骼，膝关节变形结果一致。浏览器因为多材质拆分显示 512 个绘制部件，约 62.2 万三角面。

单文件预览的隔离测试见 `viewer/offline-acceptance.json`：仅允许读取 HTML 文档本身，其余网络请求全部阻止，模型和操作仍能正常加载。本环境的受管 Chromium 禁止 `file://` 导航，因此这里没有把本机直接双击 HTML 当成已执行的测试。

## 第三方依赖

Three.js 0.170.0，MIT 许可，随附 `viewer/vendor/THREE-LICENSE.txt`。角色模型由本仓库脚本构建，没有使用第三方角色网格。小小萌是用户 Susuny001 的原创角色。
