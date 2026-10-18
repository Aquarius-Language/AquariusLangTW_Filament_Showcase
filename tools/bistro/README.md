# Bistro 轉換流程 / Bistro conversion pipeline

`assets/bistro/` 由 NVIDIA ORCA 的 **Amazon Lumberyard Bistro v5.2**（`BistroExterior.fbx` 與 622 張 DDS 紋理，約 1.7 GB）
轉換而成。轉換後是 glTF 2.0 格式，約 85 MB，可直接推送到 GitHub，不需要 Git LFS：

| 項目 | 原始 | 轉換後 |
| --- | --- | --- |
| 幾何 | FBX，2,832,120 個三角形，1,591 次繪製呼叫 | glTF + `EXT_meshopt_compression`，184 個 primitive，201 次繪製呼叫，分成 `bistro_00.bin` 與 `bistro_01.bin`，皆小於 40 MB |
| 紋理 | 622 張 2048² DDS（BC 壓縮） | 406 張 ≤1024² KTX2/ETC1S（`KHR_texture_basisu`），共約 27 MB |
| 材質 | Falcor 慣例的 BaseColor／Specular(ORM)／Normal(DirectX)／Emissive | glTF metallic-roughness：ORM 紋理直接共用；法線轉為 OpenGL 慣例；自發光使用 `KHR_materials_emissive_strength` |
| 燈光 | 只有一盞烘焙用的太陽光 | 77 盞路燈、燈籠、壁燈、立面投射燈與串燈，從發光燈具的位置自動產生（`data/bistro_lights.aqua`） |

Every file stays far below GitHub's 100 MB hard limit and below the 50 MB warning size. The GPU-compressed
KTX2 textures use about 4–8× less memory than PNG or JPEG. Merging meshes that share a material cuts the draw
calls by 8×. Together these offset the extra texture transcoding and meshopt decoding that happen at load time.

每個檔案都遠低於 GitHub 的 100 MB 上限與 50 MB 警告值。KTX2 是 GPU 壓縮紋理，佔用的記憶體比 PNG 或 JPEG
少約 4–8 倍。共用材質的網格會合併，繪製呼叫因此減為八分之一。這兩項足以抵銷載入時紋理轉碼與 meshopt
解碼的額外成本。

## 步驟 / Steps

Tools: [FBX2glTF 0.13.1](https://github.com/godotengine/FBX2glTF), [gltfpack 1.3](https://github.com/zeux/meshoptimizer),
`basisu` 2.10 (built from `filament-1.78.0/third_party/basisu`), Python 3 with Pillow and NumPy.
Every step can be resumed and fits within a few minutes.

```bash
export BISTRO_WORK=/tmp/bistro BASISU=/path/to/basisu
mkdir -p $BISTRO_WORK/ext $BISTRO_WORK/fbxtmp
# 1. FBX → glTF (geometry, node hierarchy, string-light wind animation)
FBX2glTF -i Bistro_v5_2/BistroExterior.fbx -o $BISTRO_WORK/ext/bistro --pbr-metallic-roughness \
  --long-indices auto -k position -k normal -k tangent -k uv0 --fbx-temp-dir $BISTRO_WORK/fbxtmp
# 2. DDS → PNG ≤ 1024 px, DirectX → OpenGL normals
python3 tools/bistro/tex.py Bistro_v5_2/Textures 1024
# 3. PNG → KTX2 (ETC1S; normal/ORM maps linear); repeat until "left 0"
python3 tools/bistro/encode.py 600
# 4. PBR glTF referencing the KTX2 textures; removes the baked camera and sun
python3 tools/bistro/build_gltf.py
# 5. Merge meshes and compress the geometry (float attributes kept: -noq)
mkdir -p $BISTRO_WORK/out && gltfpack -i $BISTRO_WORK/fixed/bistro.gltf -o $BISTRO_WORK/out/bistro.gltf -cc -noq
# 6. Split the binary buffer into parts < 40 MB
python3 tools/bistro/split_bin.py $BISTRO_WORK/out/bistro.gltf 40
cp $BISTRO_WORK/out/* assets/bistro/ && cp Bistro_v5_2/LICENSE.txt assets/bistro/
# 7. Regenerate the light list from the emissive fixtures
(cd $BISTRO_WORK/ext/bistro_out && python3 $OLDPWD/tools/bistro/gen_lights.py && cp bistro_lights.aqua $OLDPWD/data/)
```

授權：Bistro 採 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)，© Amazon Lumberyard，取自
[NVIDIA ORCA](https://developer.nvidia.com/orca/amazon-lumberyard-bistro)，見 `assets/bistro/LICENSE.txt`。
