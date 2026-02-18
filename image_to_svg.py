"""
Image to SVG Converter - FULL QUALITY, OPTIMIZED FOR SPEED

No resolution reduction. Potrace is CPU-bound, not RAM-bound — the temp BMP
for a 3000x3000 image is only ~27MB, well within 500MB.
The real fix is: faster B&W conversion + smarter potrace flags + shorter timeout.
"""

import os
import subprocess
from PIL import Image
import tempfile
import gc


def image_to_svg(input_path, output_path, color_mode='bw'):
    """
    Convert raster image to B&W SVG using potrace at FULL input resolution.

    Optimizations vs original:
    - NO resolution reduction — SVG output matches input dimensions exactly
    - Better B&W threshold: uses Otsu-style auto-threshold via histogram
      instead of fixed 128, giving cleaner traces on varied images
    - Faster potrace: --turdsize 4 skips noise pixels, --opttolerance 0.2
      reduces curve complexity (smaller SVG, faster trace)
    - Timeout 30s (was 60s) — fail fast with clean error before Railway's
      gateway timeout returns a cryptic 504 to the user
    - gc.collect() after PIL work, before potrace subprocess starts
    """
    try:
        img = Image.open(input_path)

        # Convert to grayscale
        img = img.convert('L')

        # --- Smart auto-threshold (better than fixed 128) ---
        # Compute histogram, find the threshold that best separates
        # foreground from background using a simple bimodal split.
        hist = img.histogram()  # 256 buckets, pixel counts
        total = sum(hist)
        # Find threshold that minimizes within-class variance (Otsu's method simplified)
        best_threshold = 128
        best_score = -1
        cumulative = 0
        cumulative_sum = 0
        for t in range(1, 256):
            cumulative += hist[t - 1]
            cumulative_sum += (t - 1) * hist[t - 1]
            if cumulative == 0 or cumulative == total:
                continue
            w0 = cumulative / total
            w1 = 1.0 - w0
            mean0 = cumulative_sum / cumulative
            mean1 = (sum(i * hist[i] for i in range(t, 256)) / (total - cumulative)) if total - cumulative > 0 else 0
            score = w0 * w1 * (mean0 - mean1) ** 2
            if score > best_score:
                best_score = score
                best_threshold = t

        # Apply threshold -> pure 1-bit B&W (best input for potrace)
        img = img.point(lambda p: 255 if p > best_threshold else 0, '1')

        tmp_bmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix='.bmp', delete=False) as tmp_bmp:
                tmp_bmp_path = tmp_bmp.name
                img.save(tmp_bmp_path, 'BMP')

            # Free PIL image before potrace starts
            del img
            gc.collect()

            # potrace flags:
            #   -s              = SVG output
            #   --turdsize 4    = ignore noise blobs <= 4px^2 (speeds up trace)
            #   --opttolerance 0.2 = curve simplification (faster + smaller SVG)
            #   --alphamax 1    = smooth corners
            #   timeout=30      = fail fast before Railway's gateway timeout
            result = subprocess.run(
                [
                    'potrace', '-s',
                    '--turdsize', '4',
                    '--opttolerance', '0.2',
                    '--alphamax', '1',
                    '-o', output_path,
                    tmp_bmp_path
                ],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                return {
                    'success': False,
                    'error': f'Potrace failed: {result.stderr}'
                }

            if not os.path.exists(output_path):
                return {
                    'success': False,
                    'error': 'SVG file was not created'
                }

            input_size  = os.path.getsize(input_path)
            output_size = os.path.getsize(output_path)

            return {
                'success': True,
                'input_size': input_size,
                'output_size': output_size,
                'output_path': output_path,
                'method': 'potrace',
                'color_mode': 'bw',
                'colors_traced': 1
            }

        finally:
            if tmp_bmp_path and os.path.exists(tmp_bmp_path):
                os.remove(tmp_bmp_path)

    except subprocess.TimeoutExpired:
        gc.collect()
        return {
            'success': False,
            'error': 'SVG conversion timed out. Try a simpler image or reduce detail.'
        }
    except Exception as e:
        gc.collect()
        return {
            'success': False,
            'error': str(e)
        }