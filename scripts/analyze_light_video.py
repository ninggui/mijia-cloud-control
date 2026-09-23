#!/usr/bin/env python3
"""从视频里测灯的亮灭曲线（纯 stdlib + ffmpeg，不需要 PIL/numpy）

做法：
1. ffmpeg 把视频降采样成 32x18 灰度原始帧（默认 10 fps）
2. 把画面切成网格，挑"亮度方差最大"的格子（= 灯所在的区域）
3. 输出该区域的亮度曲线 + 每次上升/下降的耗时（= 实际渐变时长）

用法：
  python3 analyze_light_video.py --video /path/clip.mp4 [--fps 10] [--grid 4x3] [--json out.json]
"""
import argparse
import json
import subprocess
import sys

W, H = 32, 18


def dump_gray(video, fps):
    cmd = ["ffmpeg", "-v", "error", "-i", video, "-vf", f"fps={fps},scale={W}:{H}",
           "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    p = subprocess.run(cmd, capture_output=True)
    if p.returncode != 0:
        print("ffmpeg 失败:", p.stderr.decode()[:300])
        sys.exit(1)
    data = p.stdout
    n = len(data) // (W * H)
    return [data[i * W * H:(i + 1) * W * H] for i in range(n)]


def cell_mean(frame, cx, cy, gx, gy):
    x0, x1 = cx * W // gx, (cx + 1) * W // gx
    y0, y1 = cy * H // gy, (cy + 1) * H // gy
    s = c = 0
    for y in range(y0, y1):
        row = frame[y * W:(y + 1) * W]
        for x in range(x0, x1):
            s += row[x]
            c += 1
    return s / max(c, 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--fps", type=float, default=10)
    ap.add_argument("--grid", default="4x3")
    ap.add_argument("--json")
    a = ap.parse_args()
    gx, gy = (int(v) for v in a.grid.split("x"))

    frames = dump_gray(a.video, a.fps)
    if not frames:
        print("没取到帧")
        sys.exit(1)
    series = []
    for cx in range(gx):
        for cy in range(gy):
            vals = [cell_mean(f, cx, cy, gx, gy) for f in frames]
            m = sum(vals) / len(vals)
            var = sum((v - m) ** 2 for v in vals) / len(vals)
            series.append((var, cx, cy, vals))
    series.sort(reverse=True, key=lambda x: x[0])
    var, cx, cy, vals = series[0]
    print(f"视频: {a.video} | 帧数 {len(frames)} | {a.fps}fps | 选中区域 格({cx},{cy}) 方差 {var:.0f}")
    print(f"亮度范围: min {min(vals):.0f} / max {max(vals):.0f} / 均值 {sum(vals)/len(vals):.0f}")

    lo = min(vals) + (max(vals) - min(vals)) * 0.2
    hi = min(vals) + (max(vals) - min(vals)) * 0.8
    state = "low" if vals[0] < lo else ("high" if vals[0] > hi else "mid")
    mark = None
    events = []
    for i, v in enumerate(vals):
        t = i / a.fps
        if state != "high" and v >= hi:
            state = "high"
            mark = t
        elif state == "high" and v <= lo:
            state = "low"
            if mark is not None:
                events.append(("亮", mark, t - mark))
                mark = None
        elif state == "low" and v >= hi:
            state = "high"
            mark = t
    print("\n时间(s)  亮度   曲线")
    step = max(1, len(vals) // 60)
    for i in range(0, len(vals), step):
        bar = "#" * int(vals[i] / 255 * 40)
        print(f"{i/a.fps:6.2f} {vals[i]:6.1f}  {bar}")

    if events:
        print("\n每次亮起持续时长:")
        for name, t, dur in events[:20]:
            print(f"  起 {t:6.2f}s -> 持续 {dur:5.2f}s")
    if a.json:
        json.dump({"cell": [cx, cy], "fps": a.fps, "vals": vals, "events": events}, open(a.json, "w"))
        print(f"\n原始数据: {a.json}")


if __name__ == "__main__":
    main()
