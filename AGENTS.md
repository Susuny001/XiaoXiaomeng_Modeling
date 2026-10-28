# 项目协作要求

- 用户要求每次更新都将当前模型的预览图放到根 `README.md`，同时保持 `modeling/v3/README.md` 的预览同步。
- 修改模型、材质或相机后，从本次真实 Blender 工程或三维预览器生成正面、四分之三和背面快照；将 `modeling/v3/previews/` 的新图片与来源记录随本轮更新一起提交。
- `modeling/v3/tools/stylize_work.py` 会在渲染并保存工程后自动刷新 `previews/`。发布前检查 README 中三张图均能显示、且对应当前工程。
- 二维生成图不能替代真实模型快照；制作进度与最终模型交付按 `MODELING_REVIEW.md` 的对照流程区分。
