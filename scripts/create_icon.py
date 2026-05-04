"""
Create a proper settings gear icon for WinSet using Python standard library.
Creates a recognizable gear/settings icon with proper transparency.
"""

import struct
import zlib
import os
from pathlib import Path
import math

def create_png(width, height, pixels):
    """Create a minimal PNG file from pixel data."""
    def chunk(chunk_type, data):
        c = chunk_type + data
        crc = struct.pack('>I', zlib.crc32(c) & 0xFFFFFFFF)
        return struct.pack('>I', len(data)) + c + crc

    signature = b'\x89PNG\r\n\x1a\n'

    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)  # 8-bit RGBA
    ihdr = chunk(b'IHDR', ihdr_data)

    raw_data = b''
    for y in range(height):
        raw_data += b'\x00'  # Filter byte
        for x in range(width):
            idx = (y * width + x) * 4
            raw_data += bytes(pixels[idx:idx+4])

    compressed = zlib.compress(raw_data)
    idat = chunk(b'IDAT', compressed)
    iend = chunk(b'IEND', b'')

    return signature + ihdr + idat + iend

def create_gear_icon(size):
    """Create a gear/settings icon."""
    pixels = [0] * (size * size * 4)
    center = size // 2
    outer_radius = int(size * 0.45)
    inner_radius = int(size * 0.35)
    hole_radius = int(size * 0.15)

    # Colors
    gear_color = (79, 195, 247, 255)  # #4fc3f7 - App accent color
    edge_color = (100, 200, 250, 255)  # Lighter edge

    # Gear parameters
    num_teeth = 8
    tooth_depth = int(size * 0.1)

    for y in range(size):
        for x in range(size):
            idx = (y * size + x) * 4
            dx = x - center
            dy = y - center
            dist = math.sqrt(dx*dx + dy*dy)
            angle = math.atan2(dy, dx)

            # Calculate if point is inside gear
            # Outer gear shape with teeth
            angle_normalized = (angle + math.pi) / (2 * math.pi)
            tooth_phase = (angle_normalized * num_teeth) % 1

            # Distance with tooth modulation
            current_outer = outer_radius
            if tooth_phase < 0.3 or tooth_phase > 0.7:
                current_outer += tooth_depth

            # Smooth the tooth transitions
            if tooth_phase < 0.15:
                # Rising edge
                factor = tooth_phase / 0.15
                current_outer -= tooth_depth * (1 - factor)
            elif tooth_phase > 0.85:
                # Falling edge
                factor = (1 - tooth_phase) / 0.15
                current_outer -= tooth_depth * (1 - factor)

            # Check if inside outer radius
            if dist <= current_outer and dist >= inner_radius:
                # Gear body
                # Add edge highlighting
                edge_dist = abs(dist - inner_radius) / (current_outer - inner_radius)
                if edge_dist < 0.2 or edge_dist > 0.8:
                    pixels[idx:idx+4] = list(edge_color)
                else:
                    pixels[idx:idx+4] = list(gear_color)
            elif dist < hole_radius:
                # Center hole
                pixels[idx:idx+4] = [0, 0, 0, 0]  # Transparent
            elif dist < inner_radius:
                # Inner area (transparent)
                # Add a subtle inner ring
                if dist > inner_radius - 2:
                    pixels[idx:idx+4] = list(gear_color)
                else:
                    pixels[idx:idx+4] = [0, 0, 0, 0]

            # Add "settings" details - small lines to represent configuration
            if hole_radius < dist < hole_radius + 3:
                # Inner circle line
                pixels[idx:idx+4] = list(edge_color)

    return pixels

def create_ico_file(output_path, sizes=[16, 32, 48, 64]):
    """Create an ICO file with multiple sizes."""
    icons = []

    for size in sizes:
        pixels = create_gear_icon(size)
        png_data = create_png(size, size, pixels)
        icons.append((size, size, png_data))

    header = struct.pack('<HHH', 0, 1, len(icons))

    directory = b''
    data_offset = 6 + 16 * len(icons)

    ico_data = header

    for size, _, png_data in icons:
        width = size if size < 256 else 0
        height = size if size < 256 else 0
        entry = struct.pack('<BBBBHHII',
            width, height, 0, 0, 1, 32,
            len(png_data), data_offset
        )
        directory += entry
        data_offset += len(png_data)

    ico_data += directory
    for _, _, png_data in icons:
        ico_data += png_data

    with open(output_path, 'wb') as f:
        f.write(ico_data)

    print(f"Icon created: {output_path}")
    print(f"File size: {os.path.getsize(output_path)} bytes")

if __name__ == "__main__":
    output_dir = Path(__file__).resolve().parent.parent / "docs"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "icon.ico"

    create_ico_file(str(output_path))
    print(f"\nWinSet settings gear icon created successfully at: {output_path}")
