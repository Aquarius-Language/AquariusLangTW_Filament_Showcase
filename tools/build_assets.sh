#!/usr/bin/env bash
# Regenerates every showcase asset except the Bistro (see tools/bistro/README.md) from the Filament 1.78.0
# source tree, the official Filament release tools and gltfpack/basisu. Every output file stays < 50 MB so the
# repository works on GitHub without Git LFS.
#   FILAMENT_SRC=/path/filament-1.78.0  FILAMENT_BIN=/path/filament-v1.78.0-linux/filament/bin \
#   GLTFPACK=gltfpack BASISU=basisu KHRONOS_FLIGHT_HELMET=/path/glTF-Sample-Assets/Models/FlightHelmet/glTF \
#   ./tools/build_assets.sh
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"; out="$root/assets"
: "${FILAMENT_SRC:?}" "${FILAMENT_BIN:?}"; GLTFPACK="${GLTFPACK:-gltfpack}"; BASISU="${BASISU:-basisu}"
env="$FILAMENT_SRC/third_party/environments"
# 1. Image-based lighting (cmgen): 256² prefiltered IBL + 512² (or 256² "small", soft) skyboxes.
for e in parking_garage venetian_crossroads pillars flower_road studio_small_02; do
  d="$out/environments/$e"; mkdir -p "$d"; tmp="$(mktemp -d)"
  (cd "$tmp" && "$FILAMENT_BIN/cmgen" -q -x a --format=ktx --size=256 --extract-blur=0.1 "$env/${e}_2k.hdr" \
             && "$FILAMENT_BIN/cmgen" -q -x b --format=ktx --size=512 "$env/${e}_2k.hdr")
  cp "$tmp/a/a_ibl.ktx" "$d/${e}_ibl.ktx"
  [ "$e" = studio_small_02 ] || cp "$tmp/b/b_skybox.ktx" "$d/${e}_skybox.ktx"
  [ "$e" = flower_road ] && cp "$tmp/a/a_skybox.ktx" "$d/${e}_skybox_small.ktx" && rm -f "$d/${e}_skybox.ktx"
  rm -rf "$tmp"
done
cp "$env/CC0.html" "$env/URL.txt" "$out/environments/"
# 2. Meshes (filamesh, uncompressed so every Filament decoder reads them).
mkdir -p "$out/meshes"
"$FILAMENT_BIN/filamesh" "$FILAMENT_SRC/assets/models/material_sphere/material_sphere.obj" "$out/meshes/material_sphere.filamesh"
"$FILAMENT_BIN/filamesh" "$FILAMENT_SRC/assets/models/monkey/monkey.obj" "$out/meshes/monkey.filamesh"
# 3. CC0 PBR texture sets: colour (sRGB ETC1S), normal (UASTC + zstd), ORM packed (R=AO, G=roughness, B=metal).
mkdir -p "$out/textures"; work="$(mktemp -d)"
python3 - "$FILAMENT_SRC/third_party/textures" "$work" <<'PY'
import os,sys,glob
from PIL import Image
src,out=sys.argv[1],sys.argv[2]
for d in sorted(glob.glob(src+'/*/')):
    n=os.path.basename(d.rstrip('/')); f=lambda k: f'{d}{n}_{k}.png'; S=1024
    Image.open(f('Color')).convert('RGB').resize((S,S),Image.LANCZOS).save(f'{out}/{n}_color.png')
    Image.open(f('Normal')).convert('RGB').resize((S,S),Image.LANCZOS).save(f'{out}/{n}_normal.png')
    ch=lambda k,v: Image.open(f(k)).convert('L').resize((S,S),Image.LANCZOS) if os.path.exists(f(k)) else Image.new('L',(S,S),v)
    Image.merge('RGB',(ch('AO',255),ch('Roughness',128),ch('Metallic',0))).save(f'{out}/{n}_orm.png')
PY
for p in "$work"/*_color.png; do "$BASISU" -ktx2 -mipmap -q 160 -comp_level 2 "$p" -output_file "$out/textures/$(basename "${p%.png}").ktx2" >/dev/null; done
for p in "$work"/*_orm.png; do "$BASISU" -ktx2 -mipmap -linear -q 160 -comp_level 2 "$p" -output_file "$out/textures/$(basename "${p%.png}").ktx2" >/dev/null; done
for p in "$work"/*_normal.png; do "$BASISU" -ktx2 -uastc -uastc_rdo_l 2.0 -ktx2_zstandard_level 18 -mipmap -linear "$p" -output_file "$out/textures/$(basename "${p%.png}").ktx2" >/dev/null; done
rm -rf "$work"; cp "$FILAMENT_SRC/third_party/textures/CC0.html" "$FILAMENT_SRC/third_party/textures/URL.txt" "$out/textures/"
# 4. Flight Helmet (CC0): the copy in the Filament tree is Draco-compressed; the identical Khronos sample is
#    repacked with meshopt geometry and KTX2 textures (UASTC normals).
if [ -n "${KHRONOS_FLIGHT_HELMET:-}" ]; then
  mkdir -p "$out/helmet"
  "$GLTFPACK" -i "$KHRONOS_FLIGHT_HELMET/FlightHelmet.gltf" -o "$out/helmet/FlightHelmet.gltf" -cc -noq -tc -tu normal -tl 2048
fi
find "$out" -type f -size +45M -print | sed 's/^/WARNING > 45 MB: /'
echo "Assets written to $out"
