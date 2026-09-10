# SPDX-License-Identifier: Apache-2.0
"""fit.layout_mode: "slots" — 등폭 슬롯을 연결요소로 다시 자르거나(tighten) 컴포넌트별
격자 검출/재정합/접지로 다시 앉히지(register_row_frames/ground) 않고, 행 공통 세로
절단 범위·행 공통 배율·고정 위치로만 배치하는지 고정한다.

배경(조사): Images 2.5 는 요청한 프레임 수를 이미 같은 자리·거의 같은 크기로
나눠 그린다(4체 모두 상단/높이 일치, 좌우 ≤수px). 그런데 컴포넌트 방식(기존
"components" — 연결요소로 윤곽까지 타이트하게 자른 뒤 프레임별 독립 격자 검출
→ register_row_frames → 프레임별 접지)이 이 정렬을 버리고 스스로 코마 간
높이/좌측 흔들림을 만들었다. 이 테스트의 합성 시트는 4 슬롯 모두 세로 위치·
크기(상단/하단)는 완전히 동일하게, 가로 크기만 한 코마(index 2)를 수 % 크게
그려 — "slots" 는 그래도 전 코마의 상단·하단이 정확히 같아야 하고, 기존
"components" 경로는 이 옵션을 켜지 않으면 그대로(회귀 없이) 동작해야 한다.
"""
import json

from PIL import Image

import sprite_gen.frames.extract as extract_module
from test_pitch_ground_truth import _logical_art
from test_pitch_runlen_crosscheck import _upscale_axes

MAGENTA = (255, 0, 255)
CELL = 64
SAFE_MARGIN = 4
ROWS = 40  # 전 코마 공통 논리 행 수 — 물리 높이가 코마마다 완전히 같아야 하는 전제
COLS = [18, 18, 19, 18]  # index 2 만 논리 폭이 커서 "크기만 수% 다름" 을 만든다
BLOCK = 8.0  # 논리 픽셀 -> 물리 픽셀 배율(전 코마 동일 — AI 가 같은 블록 크기로 그렸다는 전제)
SLOT_W = 200
TOP_PAD = 40
BOTTOM_PAD = 60


def _build_strip(run_dir):
    frames = [_upscale_axes(_logical_art(cols, ROWS, seed=7 + i), BLOCK, BLOCK)
              for i, cols in enumerate(COLS)]
    content_h = frames[0].height
    assert all(f.height == content_h for f in frames), "전제: 전 코마 물리 높이가 완전히 같아야 한다"
    strip = Image.new("RGB", (SLOT_W * len(frames), TOP_PAD + content_h + BOTTOM_PAD), MAGENTA)
    for i, frame in enumerate(frames):
        left = i * SLOT_W + (SLOT_W - frame.width) // 2
        strip.paste(frame, (left, TOP_PAD))
    (run_dir / "raw").mkdir(parents=True)
    strip.save(run_dir / "raw" / "idle.png")


def _make_request(layout_mode):
    fit = {"pixel_unfake": True}
    if layout_mode is not None:
        fit["layout_mode"] = layout_mode
    return {
        "version": 1, "kind": "sprite-gen-request", "engine": "component-row",
        "character": {"id": "slotbot", "description": "slot layout fixture", "base_image": None},
        "cell": {"shape": "square", "width": CELL, "height": CELL,
                 "safe_margin_x": SAFE_MARGIN, "safe_margin_y": SAFE_MARGIN,
                 "size": CELL, "safe_margin": SAFE_MARGIN},
        "chroma_key": {"name": "magenta", "hex": "#FF00FF", "rgb": [255, 0, 255], "selection": "fallback"},
        "states": {"idle": {"frames": len(COLS), "fps": 8, "loop": True,
                            "action": "synthetic slot layout fixture"}},
        "fit": fit,
    }


def _run(tmp_path, name, layout_mode):
    run_dir = tmp_path / name
    _build_strip(run_dir)
    (run_dir / "sprite-request.json").write_text(
        json.dumps(_make_request(layout_mode), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    assert extract_module.run(run_dir=run_dir) == 0
    manifest = json.loads((run_dir / "frames" / "frames-manifest.json").read_text())
    row = next(r for r in manifest["rows"] if r["state"] == "idle")
    bboxes = []
    for rel in row["files"]:
        with Image.open(run_dir / rel) as im:
            bboxes.append(im.convert("RGBA").getbbox())
    return row, bboxes


def test_slots_keeps_every_frame_top_and_bottom_identical(tmp_path):
    row, bboxes = _run(tmp_path, "slots", "slots")
    assert row["method"] == "slots"
    assert len(bboxes) == len(COLS)
    assert all(b is not None for b in bboxes), f"빈 프레임이 있으면 안 된다: {bboxes}"
    tops = [b[1] for b in bboxes]
    bottoms = [b[3] for b in bboxes]
    assert len(set(tops)) == 1, f"slots 는 전 코마 상단이 같아야 한다: {tops}"
    assert len(set(bottoms)) == 1, f"slots 는 전 코마 하단이 같아야 한다: {bottoms}"
    lefts = [b[0] for b in bboxes]
    assert max(lefts) - min(lefts) <= 2, f"slots 는 좌측 편차가 작아야 한다(≤2px): {lefts}"


def test_slots_is_opt_in_default_stays_components(tmp_path):
    row, bboxes = _run(tmp_path, "default", None)
    assert row["method"] == "components"
    assert len(bboxes) == len(COLS)


def test_components_mode_still_extracts_all_frames_when_declared_explicitly(tmp_path):
    row, bboxes = _run(tmp_path, "components", "components")
    assert row["method"] == "components"
    assert len(bboxes) == len(COLS)
    assert all(b is not None for b in bboxes)
