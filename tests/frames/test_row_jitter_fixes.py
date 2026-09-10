# SPDX-License-Identifier: Apache-2.0
"""세 옵트인 옵션(fit.pitch_policy / registration_reference / temporal_stabilize)이
행(같은 state) 안의 프레임 간 1px 단위 지터를 실제로 줄이는지 고정한다.

배경: 코마별 독립 격자 검출·프레임0 고정 정합·프레임별 조용한 지터는 조사
"idle 4코마 ブレ"의 원인이었다 — pitch_hint/family 관용도(비율 1.1) 안의 수 %
측정차가 own 채택돼 프레임마다 다른 논리 높이로 스냅되고, register_row_frames 는
frame-0 이 outlier 면 나머지 전부를 그쪽으로 끌고 갔다. 세 옵션 모두 기본값(off)에서는
기존 동작과 완전히 같다 — 그 회귀 가드는 test_pitch_ground_truth.py / 골든 테스트가 맡는다.
"""
import json

import pytest
from PIL import Image

import sprite_gen.frames.extract as extract_module
from sprite_gen.frames.extract import register_row_frames, temporal_stabilize
from test_pitch_ground_truth import _logical_art
from test_pitch_runlen_crosscheck import _upscale_axes

MAGENTA = (255, 0, 255)


# --- (a) fit.pitch_policy: 행 전체 공유 피치·위상 ---------------------------

_TARGET_BODY_H = 288  # 전 프레임 공통 물리 높이(px) — 프레임 간 세로 피치 차만 관측한다


def _pitch_policy_run(root, row_counts, x_scale=16.0, pitch_policy="own"):
    """물리 높이는 전 프레임 동일(288px)이지만, 프레임마다 논리 행 수(=세로 피치)가
    몇 % 씩 다른 픽스처 — "AI 가 프레임마다 블록을 살짝 다른 굵기로 그렸다"는
    조사 원인(idle 4코마 y피치 5.52/5.52/5.38/5.52)의 최소 재현. 가로 피치는 전
    프레임 동일(16.0)로 고정해 세로 격자 스냅차만 관측한다."""
    run_dir = root / "run"
    (run_dir / "raw").mkdir(parents=True)
    frames = []
    for rows in row_counts:
        art = _logical_art(width=14, height=rows, seed=7)
        frames.append(_upscale_axes(art, x_scale, _TARGET_BODY_H / rows))
    gap = 30
    total_w = sum(f.width for f in frames) + gap * (len(frames) + 1)
    max_h = max(f.height for f in frames)
    strip = Image.new("RGB", (total_w, max_h + gap * 2), MAGENTA)
    x = gap
    for f in frames:
        strip.paste(f, (x, gap))
        x += f.width + gap
    strip.save(run_dir / "raw" / "idle.png")
    request = {
        "version": 1, "kind": "sprite-gen-request", "engine": "component-row",
        "character": {"id": "jitterbot", "description": "pitch policy fixture", "base_image": None},
        "cell": {"shape": "square", "width": 220, "height": 220, "safe_margin_x": 8, "safe_margin_y": 8,
                 "size": 220, "safe_margin": 8},
        "chroma_key": {"name": "magenta", "hex": "#FF00FF", "rgb": [255, 0, 255], "selection": "fallback"},
        "states": {"idle": {"frames": len(frames), "fps": 8, "loop": True,
                            "action": "synthetic pitch policy fixture"}},
        "fit": {"pixel_unfake": True, "logical_height": 220, "pitch_policy": pitch_policy},
    }
    (run_dir / "sprite-request.json").write_text(
        json.dumps(request, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return run_dir


def _frame_heights(run_dir):
    manifest = json.loads((run_dir / "frames" / "frames-manifest.json").read_text(encoding="utf-8"))
    row = next(r for r in manifest["rows"] if r["state"] == "idle")
    heights = []
    for rel in row["files"]:
        with Image.open(run_dir / rel) as im:
            bbox = im.convert("RGBA").getbbox()
        heights.append(bbox[3] - bbox[1])
    return heights


def test_pitch_policy_consensus_removes_per_frame_height_jitter(tmp_path):
    # family 비율(1.1) 이내의 세로 피치 차이 — 3프레임은 18행, 1프레임만 19행.
    row_counts = [18, 18, 19, 18]

    own_dir = _pitch_policy_run(tmp_path / "own", row_counts, pitch_policy="own")
    assert extract_module.run(run_dir=own_dir) == 0
    own_heights = _frame_heights(own_dir)
    assert len(set(own_heights)) > 1, (
        f"전제: 기본(own) 모드는 프레임마다 다른 세로 피치를 그대로 채택해 높이가 갈려야 한다 "
        f"({own_heights})")

    consensus_dir = _pitch_policy_run(tmp_path / "consensus", row_counts, pitch_policy="consensus")
    assert extract_module.run(run_dir=consensus_dir) == 0
    consensus_heights = _frame_heights(consensus_dir)
    assert len(set(consensus_heights)) == 1, (
        f"fit.pitch_policy=consensus 는 행 전체가 같은 피치·위상을 써서 높이가 전부 같아야 한다 "
        f"({consensus_heights})")


def test_pitch_policy_rejects_unknown_value(tmp_path):
    run_dir = _pitch_policy_run(tmp_path / "bad", [18, 18], pitch_policy="mystery")
    with pytest.raises(SystemExit):
        extract_module.run(run_dir=run_dir)


# --- (b) fit.registration_reference: 프레임 0 고정 대신 합집합 기준 -------------
#
# 블록을 프레임마다 다른 모서리에 노치를 파 살짝 다른 모양으로 만든다 — 완전히
# 같은 모양(사각형)이면 자기 위치 매칭과 상대 위치 매칭의 점수가 정확히 동점이 나
# 결과가 for 루프 순회 순서에 우연히 의존하게 된다. 실제 포즈 실루엣은 프레임마다
# 미세하게 달라 이런 완전 동점이 나지 않는다 — 노치는 그 비대칭을 흉내낸다.

_BLOCK_COLOR = (200, 80, 80, 255)
_ANCHOR_COLOR = (5, 5, 5, 255)
_FRAME_W, _FRAME_H = 60, 20
_BLOCK_W, _BLOCK_H = 10, 13  # 상체 65% (0..12) 안에 완전히 들어가는 높이
_NOTCH = 3
_MID_ROW = 6  # 두 노치(위쪽 tl, 아래쪽 br) 모두 침범하지 않는 행 — 참 위치 지표
_TRUTH_X, _OUTLIER_X = 10, 40


def _shift_frame(block_x, notch_corner):
    """가로 앵커 두 점(0, W-1, 상체 영역 밖)으로 bbox 폭을 프레임마다 동일하게 고정하고,
    노치 있는 블록을 block_x 위치에 그린다 — getbbox 크롭이 프레임 간 절대 좌표를
    지우지 않게 한다."""
    img = Image.new("RGBA", (_FRAME_W, _FRAME_H), (0, 0, 0, 0))
    px = img.load()
    px[0, _FRAME_H - 1] = _ANCHOR_COLOR
    px[_FRAME_W - 1, _FRAME_H - 1] = _ANCHOR_COLOR
    for y in range(_BLOCK_H):
        for x in range(block_x, block_x + _BLOCK_W):
            local_x, local_y = x - block_x, y
            if notch_corner == "tl" and local_x < _NOTCH and local_y < _NOTCH:
                continue
            if notch_corner == "br" and local_x >= _BLOCK_W - _NOTCH and local_y >= _BLOCK_H - _NOTCH:
                continue
            px[x, y] = _BLOCK_COLOR
    return img


def _block_left(image, row=_MID_ROW):
    px = image.load()
    for x in range(image.width):
        if px[x, row][:3] == _BLOCK_COLOR[:3]:
            return x
    raise AssertionError("block not found in registered frame")


def test_registration_reference_first_drags_agreeing_frames_to_the_outlier():
    outlier = _shift_frame(_OUTLIER_X, "br")
    truth_a = _shift_frame(_TRUTH_X, "tl")
    truth_b = _shift_frame(_TRUTH_X, "tl")

    registered = register_row_frames([outlier, truth_a, truth_b], slack_x=35, slack_y=2, reference="first")
    outlier_x, a_x, b_x = (_block_left(f) for f in registered)

    assert a_x == outlier_x and b_x == outlier_x, (
        "frame-0(outlier) 가 기준이면 서로 동의하는 나머지 프레임들이 outlier 위치로 끌려간다 "
        f"(outlier={outlier_x}, a={a_x}, b={b_x})")


def test_registration_reference_union_keeps_agreeing_frames_at_their_own_position():
    outlier = _shift_frame(_OUTLIER_X, "br")
    truth_a = _shift_frame(_TRUTH_X, "tl")
    truth_b = _shift_frame(_TRUTH_X, "tl")

    registered = register_row_frames([outlier, truth_a, truth_b], slack_x=35, slack_y=2, reference="union")
    outlier_x, a_x, b_x = (_block_left(f) for f in registered)

    assert a_x == b_x == _TRUTH_X, (
        "fit.registration_reference=union 은 서로 동의하는 프레임들을 자기 위치에 그대로 남겨야 한다 "
        f"(a={a_x}, b={b_x}, expected={_TRUTH_X})")
    assert a_x != outlier_x, "union 기준에서도 다수 프레임이 outlier 쪽으로 끌려가면 안 된다"


def test_registration_reference_rejects_unknown_value():
    frames = [_shift_frame(_TRUTH_X, "tl"), _shift_frame(_TRUTH_X, "tl")]
    with pytest.raises(SystemExit):
        register_row_frames(frames, reference="mystery")


# --- (c) fit.temporal_stabilize: threshold 이하 소수 프레임의 픽셀 고정 ---------

def _flat_frame(size, color):
    return Image.new("RGBA", size, color)


def test_temporal_stabilize_snaps_a_lone_outlier_pixel():
    red, blue, white = (200, 40, 40, 255), (40, 40, 200, 255), (255, 255, 255, 255)
    frames = [_flat_frame((4, 4), white) for _ in range(4)]
    for f in frames:
        f.putpixel((1, 1), red)
    frames[2].putpixel((1, 1), blue)  # 한 프레임만 다른 색 — 소수(1) <= threshold(1)
    # 2:2 로 갈리는 좌표 — 진짜 교대 동작 흉내. threshold=1 로는 건드리면 안 된다.
    frames[0].putpixel((2, 2), red)
    frames[1].putpixel((2, 2), red)
    frames[2].putpixel((2, 2), blue)
    frames[3].putpixel((2, 2), blue)
    originals = [f.copy() for f in frames]

    stabilized = temporal_stabilize(frames, threshold=1)

    assert [f.getpixel((1, 1)) for f in stabilized] == [red] * 4, "소수(1장) 지터는 다수로 스냅돼야 한다"
    assert [f.getpixel((2, 2)) for f in stabilized] == [
        f.getpixel((2, 2)) for f in originals
    ], "과반이 아닌(2:2) 좌표는 실제 동작일 수 있으므로 건드리면 안 된다"
    assert [f.getpixel((0, 0)) for f in stabilized] == [white] * 4, "배경은 그대로여야 한다"
    # 입력을 제자리에서 바꾸지 않는다.
    assert frames[2].getpixel((1, 1)) == blue


def test_temporal_stabilize_threshold_zero_is_a_no_op():
    frames = [_flat_frame((3, 3), (0, 0, 0, 0)) for _ in range(4)]
    frames[1].putpixel((0, 0), (10, 10, 10, 255))
    result = temporal_stabilize(frames, threshold=0)
    assert result is frames
