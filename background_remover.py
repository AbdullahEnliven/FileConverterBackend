"""
Background Removal Service - FULL QUALITY OUTPUT, LOW RAM INFERENCE

Strategy:
1. If input image is larger than 2MB, silently compress it first (quality
   preserved visually, just strips metadata and reduces file weight).
2. Run AI inference on a downscaled copy (saves RAM).
3. Upscale the mask back to original resolution and apply to original image.
   Output is always at the original input resolution — no quality loss.

Model: u2netp (~4MB RAM) instead of u2net (~170MB RAM).
"""

from PIL import Image
from rembg import remove
from io import BytesIO
import os
import gc

_session = None

MAX_INPUT_BYTES = 2 * 1024 * 1024  # 2MB threshold before compression kicks in


def get_rembg_session():
    """Load u2netp once and reuse. ~4MB vs u2net's ~170MB."""
    global _session
    if _session is None:
        from rembg import new_session
        _session = new_session("u2netp")
    return _session


def compress_image_to_limit(img, max_bytes=MAX_INPUT_BYTES):
    """
    Compress a PIL image (already loaded) to fit within max_bytes.
    Uses JPEG quality reduction in steps — stops as soon as it fits.
    Returns compressed image bytes (PNG for lossless alpha preservation).

    Strategy:
    - Try saving as JPEG at decreasing quality (95 -> 85 -> 75 -> 60 -> 45)
    - JPEG is used only for the AI INFERENCE copy — the original PIL image
      stays untouched so output quality is never affected.
    - If even quality=45 is still over limit, resize dimensions by 0.85x
    """
    qualities = [95, 85, 75, 60, 45]

    for quality in qualities:
        buf = BytesIO()
        # Save as JPEG for compression (AI doesn't need PNG for inference)
        img.save(buf, format='JPEG', quality=quality, optimize=True)
        if buf.tell() <= max_bytes:
            buf.seek(0)
            return buf.read()

    # Still too large — reduce dimensions progressively
    temp_img = img.copy()
    for _ in range(5):
        w, h = temp_img.size
        temp_img = temp_img.resize(
            (int(w * 0.85), int(h * 0.85)),
            Image.Resampling.LANCZOS
        )
        buf = BytesIO()
        temp_img.save(buf, format='JPEG', quality=60, optimize=True)
        if buf.tell() <= max_bytes:
            buf.seek(0)
            del temp_img
            return buf.read()

    # Fallback — return whatever we have
    buf.seek(0)
    del temp_img
    return buf.read()


def remove_background(input_path, output_path, add_background_color=None):
    """
    Remove background at FULL original resolution.

    How it works:
    1. Open original image, record original size
    2. If file > 2MB, compress a COPY for AI inference (original untouched)
    3. Downscale inference copy to 1024px MAX (low RAM)
    4. Run u2netp AI on the small compressed copy
    5. Extract alpha mask from AI output
    6. Upscale mask back to ORIGINAL resolution (smooth edges)
    7. Apply mask to the ORIGINAL full-res image
    8. Save at original resolution — full quality output
    """
    try:
        # --- Step 1: Load original ---
        original_img = Image.open(input_path)
        original_size = original_img.size

        # Normalise mode — flatten any existing alpha to RGB
        if original_img.mode in ('RGBA', 'LA', 'P'):
            original_rgb = Image.new('RGB', original_img.size, (255, 255, 255))
            if original_img.mode == 'P':
                original_img = original_img.convert('RGBA')
            if original_img.mode in ('RGBA', 'LA'):
                original_rgb.paste(original_img, mask=original_img.split()[-1])
            else:
                original_rgb.paste(original_img)
            original_img = original_rgb
        elif original_img.mode != 'RGB':
            original_img = original_img.convert('RGB')

        # --- Step 2 & 3: Build inference copy ---
        # Downscale to 1024px for AI (RAM savings)
        INFERENCE_MAX = 1024
        inference_img = original_img.copy()
        if max(inference_img.size) > INFERENCE_MAX:
            ratio = INFERENCE_MAX / max(inference_img.size)
            inf_size = (int(inference_img.size[0] * ratio), int(inference_img.size[1] * ratio))
            inference_img = inference_img.resize(inf_size, Image.Resampling.LANCZOS)

        # Check size and compress if needed BEFORE sending to AI
        input_file_size = os.path.getsize(input_path)
        if input_file_size > MAX_INPUT_BYTES:
            print(f"[INFO] Input image {input_file_size/1024/1024:.1f}MB > 2MB — compressing inference copy")
            raw = compress_image_to_limit(inference_img, MAX_INPUT_BYTES)
            del inference_img
        else:
            # Under 2MB — just encode as PNG normally
            buf = BytesIO()
            inference_img.save(buf, format='PNG')
            buf.seek(0)
            raw = buf.read()
            del inference_img
            buf.close()

        gc.collect()

        # --- Step 4: Run AI inference ---
        session = get_rembg_session()
        ai_output_bytes = remove(raw, session=session)
        del raw
        gc.collect()

        # --- Step 5: Extract alpha mask ---
        ai_result = Image.open(BytesIO(ai_output_bytes))
        if ai_result.mode != 'RGBA':
            ai_result = ai_result.convert('RGBA')
        small_mask = ai_result.split()[3]
        del ai_result
        gc.collect()

        # --- Step 6: Upscale mask to original resolution ---
        full_mask = small_mask.resize(original_size, Image.Resampling.LANCZOS)
        del small_mask
        gc.collect()

        # --- Step 7: Apply mask to original full-res image ---
        original_img = original_img.convert('RGBA')
        original_img.putalpha(full_mask)
        del full_mask
        gc.collect()

        # --- Step 8: Save ---
        if add_background_color and isinstance(add_background_color, str):
            add_background_color = tuple(int(x.strip()) for x in add_background_color.split(','))

        if add_background_color:
            bg = Image.new('RGB', original_img.size, add_background_color)
            bg.paste(original_img, (0, 0), original_img)
            bg.save(output_path, format='PNG', optimize=True, compress_level=9)
        else:
            original_img.save(output_path, format='PNG', optimize=True, compress_level=9)

        output_size = os.path.getsize(output_path)
        del original_img
        gc.collect()

        return {
            'success': True,
            'input_size': input_file_size,
            'output_size': output_size,
            'output_path': output_path
        }

    except Exception as e:
        import traceback
        print(f"[ERROR] Background removal failed: {e}")
        traceback.print_exc()
        gc.collect()
        return {
            'success': False,
            'error': str(e)
        }


def process_batch_background_removal(input_paths, output_dir, add_background_color=None):
    """Process multiple images — model session reused for speed."""
    get_rembg_session()
    results = []
    for input_path in input_paths:
        filename = os.path.basename(input_path)
        name, _ = os.path.splitext(filename)
        output_path = os.path.join(output_dir, f"{name}_no_bg.png")
        result = remove_background(input_path, output_path, add_background_color)
        result['filename'] = filename
        results.append(result)
    return results
