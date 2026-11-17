# airportmoive
how to build an airport

## 维拉娜机场扩建宣传片试剪

本版共 75 秒，包含建筑剖面、BIM 碰撞调整、登机口变更、航显和二维广播覆盖。

### 重新渲染

准备 Python 3、Pillow 9.1+、含 libx264 的 FFmpeg、Noto Sans CJK Regular/Bold 字体和 Blender。将项目素材包 `Velana_Film_Materials.zip` 解压并保留目录结构。

```sh
python -m pip install "Pillow>=9.1"
blender --background --threads 4 --python-exit-code 1 --python build_bim.py -- ./output/bim
python render.py --materials ./Velana_Film_Materials --bim ./output/bim --output ./output
```

`--materials` 指向包含 `02_Construction` 和 `03_ELV_IT` 的目录。脚本读取其中的总剖面 PNG、候机区照片和二维广播覆盖图。若已有 `Clash.png` 和 `Resolved.png`，将它们所在目录传给 `--bim` 即可。

Linux 默认字体路径为 `/usr/share/fonts/opentype/noto`。使用其他路径时，通过 `--fonts` 指向包含 `NotoSansCJK-Regular.ttc` 和 `NotoSansCJK-Bold.ttc` 的目录。

成片为 `output/Velana_Film_Trial_Cut.mp4`，1280×720，25 fps。字幕、镜头时间和提示音可在 `render.py` 中修改。BIM 节点和广播覆盖使用示意数据，项目素材与 MP4 单独存放。

## 6 分钟五幕初剪

`full_film.py` 按素材包里的 38 镜索引编排全片，并将图纸、模型、字幕和来源放在独立区域。沿用上面的 Blender 渲染步骤生成 BIM 对照帧，再运行：

```sh
python -m pip install "Pillow>=9.1" numpy
python full_film.py --materials ./Velana_Film_Materials --bim ./output/bim --output ./output/Velana_Full_Rough_Cut.mp4
```

输出为 1280×720、24 fps 的带章节 MP4，包括中文字幕、临时氛围音和提示音。字幕及流程演示文案位于 `full_film.py`。
