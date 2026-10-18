# AquariusLangTW Filament Showcase — 星泉 Filament 展示

使用 [Aqua_Filament](../Aqua_Filament) 以 Google Filament 1.78.0 重現 Filament 官方展示的五個場景，
完全以 AquariusLang 星泉撰寫。

Five Filament 1.78.0 showcase scenes recreated in AquariusLang with the Aqua_Filament library.

| # | 場景 / Scene | 檔案 | 內容 |
| --- | --- | --- | --- |
| 1 | 夜晚的 Bistro 街道 / Bistro night street | `scenes/night_street.aqua` | Amazon Lumberyard Bistro、77 盞點光源與聚光燈、月光陰影、泛光、SSAO、TAA、霧 |
| 2 | 停車場材質球 / Material balls in a parking garage | `scenes/materials.aqua`（`"garage"`） | 30 種 PBR 材質（8 種貼圖材質＋22 種參數材質）、parking_garage IBL、陰影接收地面 |
| 3 | 石板街材質球 / Material balls on a cobblestone street | `scenes/materials.aqua`（`"street"`） | 同上，使用 venetian_crossroads IBL |
| 4 | 飛行頭盔 / Flight Helmet | `scenes/flight_helmet.aqua` | Khronos FlightHelmet glTF（KTX2）、flower_road IBL、景深 |
| 5 | 螢幕空間折射 / Screen-space refraction Suzanne | `scenes/refraction.aqua` | Suzanne（monkey.filamesh）、折射材質（吸收、厚度、IOR）、pillars IBL |

## 操作 / Controls

| 按鍵 | 功能 |
| --- | --- |
| `1`–`5`、`N` / `P` | 切換場景（下一個／上一個） |
| 滑鼠左鍵拖曳、右鍵拖曳、滾輪 | 旋轉、平移、縮放（場景 2–5，軌道相機） |
| 滑鼠拖曳＋`W A S D Q E` | 飛行相機（場景 1） |
| `L` / `B` | 場景 1：開關街燈／泛光 |
| `R` | 場景 2、3：材質球自轉 |
| `F` | 場景 4：開關景深 |
| `Space` / `C` | 場景 5：暫停旋轉／更換玻璃顏色 |
| `Esc` | 離開 |

視窗標題會顯示目前場景與幀率。The window title shows the current scene and the frame rate.

## 執行 / Run

需要 AquariusLangTW 的 `aqua` 工具，並把 Aqua_Filament 放在同一層資料夾（`../Aqua_Filament`）。
Requires the AquariusLangTW `aqua` CLI, with Aqua_Filament checked out next to this folder.

```powershell
aqua bottle restore --project .                       # 解析 Aqua_Filament 相依 / resolve the dependency
aqua build . --target windows -o dist\showcase.exe    # Windows x64
aqua build . --target linux -o dist/showcase          # Linux x64（X11 / XWayland）
aqua build . --target web -o dist\web                 # 網頁 WebGL 2；請用 localhost 或 HTTPS 開啟
node tools/serve_web.mjs                              # 本機網頁：Edge 獨立設定檔＋Vulkan / local Edge + Vulkan
```

注意事項 / Notes：

- **網頁版會在啟動時預先下載所有資產**，包括約 85 MB 的 Bistro，第一次開啟較慢。Bistro 在網頁版的
  WebGL 2 上很吃效能，建議使用獨立顯示卡。
- 主程式 wasm 的大小依目標平台而異，資產會內嵌在桌面版執行檔中，並受星泉 256 MiB 上限限制。若要再加入大型資產，
  請考慮從執行期資料夾載入。
- 修改 `../Aqua_Filament` 後若出現「already cached with different contents」或「does not match locked」，
  請執行 `aqua bottle cache remove Aqua_Filament 1.0.0` 並刪除 `aqua.lock.json`。
- 自動截圖測試：`aqua build . --platform windows -o dist\app.wasm` 之後執行 `aqua run dist\app.wasm --entry tests/capture.aqua`，
  會輸出五張 `capture_*.png`。網頁版 `tests/capture_web.aqua` 同樣驗證五個場景，包含 Bistro。

Aqua_Filament 1.0.1 修正 Windows 高 DPI 下視口遭裁切的問題；已在 250% 縮放驗證固定、軌道與飛行相機。

在這台雙 GPU Windows 電腦上，Edge 的 Direct3D 11 WebGL 路徑會在 Bistro 啟動時中斷 GPU 程序，
後續顯示 `base_lit_masked` 連結失敗及 `CONTEXT_LOST_WEBGL`。Intel 與 NVIDIA 的 Direct3D 路徑皆可重現；
NVIDIA Vulkan 與 SwiftShader 可完整通過五個場景。`node tools/serve_web.mjs` 以獨立 Edge 設定檔
選用 Vulkan，保留硬體加速與所有場景效果。這不會更改 Edge 的全域 ANGLE 設定。
此啟動器需要 Node.js 與 Microsoft Edge；`--no-open` 可只啟動本機伺服器。
Windows 也可直接執行專案根目錄的 `run-web.cmd`。

Windows 250% scaling now uses a matching WGL driver-thread DPI mode, so the full camera viewport is visible.
For the browser GPU-process failure reproduced here on Direct3D 11, run `node tools/serve_web.mjs` to use
hardware Vulkan in a separate Edge profile. The website still renders through WebGL 2.

網頁回歸測試（需要 Playwright，或以 `NODE_PATH` 指向既有安裝）：

```powershell
$env:WEBGL_ANGLE = "vulkan"
node tests/verify_web.cjs
```

測試會啟動暫時的 localhost 伺服器，驗證五張截圖、完成狀態與繪圖環境未中斷，並把截圖寫入 `tests/artifacts/`。

## 資產與 Git（不需要 LFS）/ Assets and Git without LFS

所有資產都已拆成可直接推送到 GitHub 的大小：每個檔案都小於 40 MB，遠低於 50 MB 警告值與 100 MB 上限。
不需要 Git LFS。

| 資料夾 | 大小 | 來源與處理 | 授權 |
| --- | --- | --- | --- |
| `assets/bistro/` | 約 85 MB，409 個檔案 | NVIDIA ORCA Amazon Lumberyard Bistro v5.2：約 1.7 GB 的 FBX＋DDS 轉成 glTF＋meshopt＋KTX2，二進位緩衝區拆成兩個小於 40 MB 的檔案。詳見 [`tools/bistro/README.md`](tools/bistro/README.md) | CC BY 4.0，© Amazon Lumberyard |
| `assets/helmet/` | 約 19 MB | Khronos glTF-Sample-Assets 的 FlightHelmet（與 Filament 隨附的同一模型）：PNG 轉成 KTX2/BasisU（法線使用 UASTC），幾何以 gltfpack meshopt 壓縮 | CC0 |
| `assets/environments/` | — | Poly Haven HDRI（parking_garage、venetian_crossroads、pillars、flower_road、studio_small_02），以 Filament `cmgen` 產生 IBL 與天空盒 KTX | CC0 |
| `assets/textures/` | — | Poly Haven／ambientCG PBR 材質，打包成 baseColor、normal、ORM，再轉成 KTX2 | CC0 |
| `assets/meshes/` | — | Filament 範例的 `material_sphere` 與 `monkey`（Suzanne），以 `filamesh` 產生 | Apache-2.0／Blender CC0 |

Bistro is too large for GitHub in its original form. The model is converted rather than downscaled, so
performance is preserved:

- Meshes that share a material are merged, cutting draw calls from 1,591 to 201.
- Geometry keeps full-precision floats and is compressed with meshopt, which is lossless for float attributes.
- Textures are GPU-compressed KTX2 at up to 1024², using 4–8× less memory than PNG or JPEG.

All tooling is in `tools/`: `build_assets.sh` builds the IBLs, meshes, textures and helmet, and `tools/bistro/`
holds the Bistro pipeline and `gen_lights.py`, which regenerates `data/bistro_lights.aqua`.

## 專案結構 / Layout

```
aqua.toml            Bottle 設定（相依 Aqua_Filament ≥1.0.0 <2.0.0；assets 目錄）
main.aqua            場景切換、標題列幀率
scenes/              五個場景模組（建立 / 更新 / 名稱）
data/                Bistro 光源列表
tests/               截圖測試（桌面 / 網頁）
tools/               資產轉換腳本
assets/              已轉換的資產
```

## 授權 / License

程式碼採 MIT；資產授權見上表，以及各資產資料夾中的 LICENSE、CC0.html 檔案。
