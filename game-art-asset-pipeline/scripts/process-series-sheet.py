import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw


def remove_edge_background(image: Image.Image, tolerance: int) -> Image.Image:
    rgba = np.array(image.convert("RGBA"))
    bgr = cv2.cvtColor(rgba[:, :, :3], cv2.COLOR_RGB2BGR)
    working = bgr.copy()
    flood_mask = np.zeros((bgr.shape[0] + 2, bgr.shape[1] + 2), dtype=np.uint8)
    flags = 4 | cv2.FLOODFILL_FIXED_RANGE | (255 << 8)
    corners = ((0, 0), (bgr.shape[1] - 1, 0), (0, bgr.shape[0] - 1), (bgr.shape[1] - 1, bgr.shape[0] - 1))
    for seed in corners:
        cv2.floodFill(working, flood_mask, seed, (0, 0, 0), (tolerance,) * 3, (tolerance,) * 3, flags)
    background = flood_mask[1:-1, 1:-1] == 255
    rgba[:, :, 3] = np.where(background, 0, 255).astype(np.uint8)
    rgba[background, :3] = 0
    return Image.fromarray(rgba, "RGBA")


def occupied_spans(occupied: np.ndarray, gap: int) -> list[tuple[int, int]]:
    indices = np.flatnonzero(occupied)
    if len(indices) == 0:
        return []
    spans = []
    start = previous = int(indices[0])
    for raw_value in indices[1:]:
        value = int(raw_value)
        if value - previous > gap:
            spans.append((start, previous + 1))
            start = value
        previous = value
    spans.append((start, previous + 1))
    return spans


def checkerboard(width: int, height: int, cell: int = 16) -> Image.Image:
    image = Image.new("RGBA", (width, height), (40, 44, 52, 255))
    draw = ImageDraw.Draw(image)
    for y in range(0, height, cell):
        for x in range(0, width, cell):
            if (x // cell + y // cell) % 2 == 0:
                draw.rectangle((x, y, min(x + cell - 1, width - 1), min(y + cell - 1, height - 1)), fill=(56, 61, 70, 255))
    return image


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract a horizontal series sheet into normalized transparent PNG assets.")
    parser.add_argument("--source", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--prefix", required=True)
    parser.add_argument("--count", type=int, required=True)
    parser.add_argument("--canvas", type=int, default=256)
    parser.add_argument("--max-extent", type=int, default=215)
    parser.add_argument("--anchor-y", type=int, default=20)
    parser.add_argument("--background-tolerance", type=int, default=72)
    parser.add_argument("--minimum-gap", type=int, default=12)
    parser.add_argument("--minimum-width", type=int, default=32)
    parser.add_argument("--content-top", type=int)
    parser.add_argument("--content-bottom", type=int)
    parser.add_argument("--review")
    parser.add_argument("--report")
    args = parser.parse_args()

    source_path = Path(args.source)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    source = Image.open(source_path).convert("RGBA")
    transparent = remove_edge_background(source, args.background_tolerance)
    alpha = np.array(transparent.getchannel("A"))
    top = 0 if args.content_top is None else args.content_top
    bottom = source.height if args.content_bottom is None else args.content_bottom
    column_occupied = np.any(alpha[top:bottom, :] > 0, axis=0)
    spans = [span for span in occupied_spans(column_occupied, args.minimum_gap) if span[1] - span[0] >= args.minimum_width]
    if len(spans) != args.count:
        raise RuntimeError(f"Expected {args.count} separated subjects, detected {len(spans)} spans: {spans}")

    subjects = []
    for left, right in spans:
        region = transparent.crop((left, top, right, bottom))
        bbox = region.getchannel("A").getbbox()
        if bbox is None:
            raise RuntimeError(f"Detected span {left}:{right} has no visible content")
        subjects.append(region.crop(bbox))

    max_width = max(subject.width for subject in subjects)
    max_height = max(subject.height for subject in subjects)
    common_scale = min(args.max_extent / max_width, args.max_extent / max_height)
    review_path = Path(args.review) if args.review else output_dir / f"{args.prefix}_review.png"
    review_path.parent.mkdir(parents=True, exist_ok=True)
    review = checkerboard(args.canvas * args.count, args.canvas)
    artifacts = []

    for index, subject in enumerate(subjects, 1):
        size = (max(1, round(subject.width * common_scale)), max(1, round(subject.height * common_scale)))
        resized = subject.resize(size, Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (args.canvas, args.canvas), (0, 0, 0, 0))
        position = (args.canvas // 2 - resized.width // 2, args.anchor_y)
        if position[1] + resized.height > args.canvas:
            raise RuntimeError(f"Subject {index} exceeds canvas after anchoring")
        canvas.alpha_composite(resized, position)
        output_path = output_dir / f"{args.prefix}_{index:02d}.png"
        canvas.save(output_path, "PNG", optimize=True)
        review.alpha_composite(canvas, ((index - 1) * args.canvas, 0))
        artifacts.append({"index": index, "path": str(output_path), "visibleSize": list(size), "visibleBbox": list(canvas.getchannel("A").getbbox()), "sha256": digest(output_path)})

    review.save(review_path, "PNG", optimize=True)
    report = {"source": str(source_path), "detectedSpans": spans, "commonScale": common_scale, "canvas": args.canvas, "maxExtent": args.max_extent, "anchorY": args.anchor_y, "review": str(review_path), "artifacts": artifacts}
    report_path = Path(args.report) if args.report else output_dir / f"{args.prefix}_processing.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
