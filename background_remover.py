"""
Background Removal - rembg with silueta model
silueta is the fastest/smallest rembg model, accurate results.
"""

import os
import gc
from PIL import Image
from rembg import remove, new_session
from io import BytesIO

_session = None

def get_session():
    global _session
    if _session is None:
        _session = new_session("silueta")  # fastest accurate model in rembg
    return _session


def remove_background(input_path, output_path, add_background_color=None):
    try:
        input_size = os.path.getsize(input_path)

        with open(input_path, "rb") as f:
            input_bytes = f.read()

        output_bytes = remove(input_bytes, session=get_session())
        gc.collect()

        result = Image.open(BytesIO(output_bytes)).convert("RGBA")

        if add_background_color:
            if isinstance(add_background_color, str):
                add_background_color = tuple(int(x.strip()) for x in add_background_color.split(","))
            bg = Image.new("RGB", result.size, add_background_color)
            bg.paste(result, mask=result.split()[3])
            bg.save(output_path, format="PNG", optimize=True, compress_level=9)
        else:
            result.save(output_path, format="PNG", optimize=True, compress_level=9)

        del result
        gc.collect()

        return {
            "success": True,
            "input_size": input_size,
            "output_size": os.path.getsize(output_path),
            "output_path": output_path,
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        gc.collect()
        return {"success": False, "error": str(e)}


def process_batch_background_removal(input_paths, output_dir, add_background_color=None):
    get_session()
    results = []
    for input_path in input_paths:
        filename = os.path.basename(input_path)
        name, _ = os.path.splitext(filename)
        output_path = os.path.join(output_dir, f"{name}_no_bg.png")
        result = remove_background(input_path, output_path, add_background_color)
        result["filename"] = filename
        results.append(result)
    return results
