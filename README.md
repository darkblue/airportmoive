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

## V2 实景版

在 `design-stills` 中放置建筑设计报告 `word/media/` 原图。将 image13、image19、image22、image26、image45 转为同名 JPG。其他可选素材可从 1PAX 的机场项目相册选取，按用途命名。第三方照片按项目审阅使用，发布时需确认授权。

- [gates.jpg](https://cdn.prod.website-files.com/698a41cf3248593467beb7ef/69de2b15ab157f08dbb2f4d9_DSC02714.webp)
- [checkin.jpg](https://cdn.prod.website-files.com/698a41cf3248593467beb7ef/69de2b47dd18dd0f69f866bf_DJI_20250716230928_0001_D.webp)
- [ceiling.jpg](https://cdn.prod.website-files.com/698a41cf3248593467beb7ef/69b6a110415b59c2d8fefea6_DSC02807.webp)
- [lobby.jpg](https://cdn.prod.website-files.com/698a41cf3248593467beb7ef/69c3d1baf4035be5135b8348_SA102834.webp)
- [aerial.jpg](https://cdn.prod.website-files.com/698a41cf3248593467beb7ef/69b6a110803ab42ed751c173_DJI_20250731110904_0183_D.webp)
- [terminal.jpg](https://cdn.prod.website-files.com/698a41cf3248593467beb7ef/69d620e795a4130c5cac9436_velana_night.webp)
- [facade.jpg](https://cdn.prod.website-files.com/698a41cf3248593467beb7ef/69de304c963fc3c2ecf42afe_DSC03539.webp)

```sh
VELANA_DESIGN_STILLS=./design-stills python editorial_cut.py --materials ./Velana_Film_Materials --bim ./output/bim --output ./output/Velana_Full_Edit_V2.mp4
```

## 6 分钟 Blueprint 版

沿用原项目素材包中的 38 镜索引。从地图素材包 `Velana_Map_Assets.zip` 取出 `world_land.geojson` 和 `local_geometry.json`，放在同一个目录。需要 Python 3、Pillow、NumPy、FFmpeg、Inkscape 和 Noto Sans CJK 字体。

```sh
python blueprint_film.py --materials ./Velana_Film_Materials --data ./Velana_Map --output ./output/Velana_Full_Blueprint.mp4
```

地图为 Natural Earth 和 OpenStreetMap 矢量数据的连续放大镜头。工程图、运行流程和资产记录为影视重绘。
