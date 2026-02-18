"""
Background Removal Service - FULL QUALITY OUTPUT, LOW RAM INFERENCE

Strategy: Run AI inference on a downscaled copy (saves RAM), then upscale
the resulting MASK back to the original resolution and apply it to the
original full-res image. Output is always at the original input resolution.

This is how professional tools work — the AI only needs enough pixels to
understand shapes, not full resolution. The crisp edges come from the
original image, not from the AI output.

Model: u2netp (~4MB RAM) instead of u2net (~170MB RAM).
"""

from PIL import Image
from rembg import remove
from io import BytesIO
import os
import gc

_session = None

def get_rembg_session():
    """Load u2netp once and reuse. ~4MB vs u2net's ~170MB."""
    global _session
    if _session is None:
        from rembg import new_session
        _session = new_session("u2netp")
    return _session


def remove_background(input_path, output_path, add_background_color=None):
    """
    Remove background at FULL original resolution.

    How it works:
    1. Open original image, save original size
    2. Downscale to 1024px MAX for AI inference (low RAM)
    3. Run u2netp on the small copy -> get RGBA mask output
    4. Extract just the alpha (mask) channel from AI output
    5. Upscale mask back to ORIGINAL resolution (LANCZOS = smooth edges)
    6. Apply upscaled mask to the ORIGINAL full-res image
    7. Save at original resolution -> full quality output
    """
    try:
        # --- Step 1: Load original, record its size ---
        original_img = Image.open(input_path)
        original_size = original_img.size  # (width, height) — we restore to this

        # Flatten alpha for the original (we'll apply our own mask later)
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

        # --- Step 2: Downscale a COPY for AI inference only ---
        # AI inference RAM is the bottleneck. 1024px gives the model
        # more than enough detail to segment the subject accurately.
        INFERENCE_MAX = 1024
        inference_img = original_img.copy()
        if max(inference_img.size) > INFERENCE_MAX:
            ratio = INFERENCE_MAX / max(inference_img.size)
            inf_size = (int(inference_img.size[0] * ratio), int(inference_img.size[1] * ratio))
            inference_img = inference_img.resize(inf_size, Image.Resampling.LANCZOS)

        # --- Step 3: Run AI on the small copy ---
        inf_bytes = BytesIO()
        inference_img.save(inf_bytes, format='PNG')
        inf_bytes.seek(0)
        raw = inf_bytes.read()

        del inference_img
        inf_bytes.close()
        gc.collect()

        session = get_rembg_session()
        ai_output_bytes = remove(raw, session=session)
        del raw
        gc.collect()

        # --- Step 4: Extract the alpha mask from AI output ---
        ai_result = Image.open(BytesIO(ai_output_bytes))
        if ai_result.mode != 'RGBA':
            ai_result = ai_result.convert('RGBA')

        # Alpha channel = the mask (white=keep, black=remove)
        small_mask = ai_result.split()[3]  # 'A' channel only

        del ai_result
        gc.collect()

        # --- Step 5: Upscale mask to original resolution ---
        # LANCZOS gives smooth anti-aliased edges when upscaling the mask
        full_mask = small_mask.resize(original_size, Image.Resampling.LANCZOS)
        del small_mask
        gc.collect()

        # --- Step 6: Apply full-res mask to original full-res image ---
        original_img = original_img.convert('RGBA')
        original_img.putalpha(full_mask)
        del full_mask
        gc.collect()

        # --- Step 7: Save ---
        if add_background_color and isinstance(add_background_color, str):
            add_background_color = tuple(int(x.strip()) for x in add_background_color.split(','))

        if add_background_color:
            bg = Image.new('RGB', original_img.size, add_background_color)
            bg.paste(original_img, (0, 0), original_img)
            bg.save(output_path, format='PNG', optimize=True, compress_level=6)
        else:
            original_img.save(output_path, format='PNG', optimize=True, compress_level=6)

        input_size  = os.path.getsize(input_path)
        output_size = os.path.getsize(output_path)

        del original_img
        gc.collect()

        return {
            'success': True,
            'input_size': input_size,
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