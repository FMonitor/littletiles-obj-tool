from __future__ import annotations

from pathlib import Path

from littletiles_obj_tool.constants import FACE_QUADS
from littletiles_obj_tool.models import LTBox, LTModel, LTTile
from littletiles_obj_tool.nbt_tags import signed_int32
from littletiles_obj_tool.new_format import iter_boxes
from littletiles_obj_tool.utils import color_to_opacity, color_to_rgb, sanitize_name


def write_obj(model: LTModel, output_obj: Path) -> None:
    output_obj.parent.mkdir(parents=True, exist_ok=True)
    output_mtl = output_obj.with_suffix(".mtl")
    vertices: list[tuple[float, float, float]] = []
    vertex_index: dict[tuple[float, float, float], int] = {}
    faces_out: list[str] = []
    materials: dict[str, tuple[float, float, float]] = {}

    def add_vertex(point: tuple[int, int, int]) -> int:
        coord = tuple(round(v / model.grid, 8) for v in point)
        if coord not in vertex_index:
            vertex_index[coord] = len(vertices) + 1
            vertices.append(coord)
        return vertex_index[coord]

    for tile, box in iter_boxes(model):
        corners = box.corners()
        material = f"{sanitize_name(tile.block)}_{tile.color}"
        materials.setdefault(material, color_to_rgb(tile.color))
        faces_out.append(f"usemtl {material}")
        for quad in FACE_QUADS.values():
            polygon = dedupe_polygon([corners[i] for i in quad])
            if len(polygon) < 3:
                continue
            first = add_vertex(polygon[0])
            for i in range(1, len(polygon) - 1):
                tri = (polygon[0], polygon[i], polygon[i + 1])
                if triangle_area(tri) == 0:
                    continue
                v2 = add_vertex(tri[1])
                v3 = add_vertex(tri[2])
                faces_out.append(f"f {first} {v2} {v3}")

    obj_lines = [f"mtllib {output_mtl.name}"]
    obj_lines.extend(f"v {x} {y} {z}" for x, y, z in vertices)
    obj_lines.extend(faces_out)
    output_obj.write_text("\n".join(obj_lines) + "\n", encoding="utf-8")

    mtl_lines = []
    for material, (r, g, b) in materials.items():
        color_value = int(material.rsplit("_", 1)[1])
        mtl_lines.append(f"newmtl {material}")
        mtl_lines.append(f"Kd {r:.6f} {g:.6f} {b:.6f}")
        mtl_lines.append("Ka 0.000000 0.000000 0.000000")
        mtl_lines.append("Ks 0.000000 0.000000 0.000000")
        mtl_lines.append(f"d {color_to_opacity(color_value):.6f}")
        mtl_lines.append("")
    output_mtl.write_text("\n".join(mtl_lines), encoding="utf-8")


def dedupe_polygon(points: list[tuple[int, int, int]]) -> list[tuple[int, int, int]]:
    result: list[tuple[int, int, int]] = []
    for point in points:
        if not result or result[-1] != point:
            result.append(point)
    if len(result) > 1 and result[0] == result[-1]:
        result.pop()
    return result


def triangle_area(points: tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]) -> float:
    (ax, ay, az), (bx, by, bz), (cx, cy, cz) = points
    ab = (bx - ax, by - ay, bz - az)
    ac = (cx - ax, cy - ay, cz - az)
    cross = (
        ab[1] * ac[2] - ab[2] * ac[1],
        ab[2] * ac[0] - ab[0] * ac[2],
        ab[0] * ac[1] - ab[1] * ac[0],
    )
    return abs(cross[0]) + abs(cross[1]) + abs(cross[2])


def read_obj(path: Path) -> list[tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]]:
    vertices: list[tuple[float, float, float]] = []
    triangles: list[tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("v "):
            _, x, y, z = line.split()[:4]
            vertices.append((float(x), float(y), float(z)))
        elif line.startswith("f "):
            parts = line.split()[1:]
            face = []
            for part in parts:
                vertex_id = part.split("/")[0]
                idx = int(vertex_id)
                if idx < 0:
                    idx = len(vertices) + idx + 1
                face.append(vertices[idx - 1])
            if len(face) < 3:
                continue
            for i in range(1, len(face) - 1):
                triangles.append((face[0], face[i], face[i + 1]))
    return triangles


def triangle_to_lt_box(
    triangle: tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]],
    model_min: tuple[float, float, float],
    ratio: float,
) -> list[int]:
    normalized = []
    min_max = [2**31 - 1, 2**31 - 1, 2**31 - 1, -(2**31), -(2**31), -(2**31)]
    for vertex in triangle:
        shifted = tuple((vertex[i] - model_min[i]) * ratio for i in range(3))
        rounded = tuple(int(round(value)) for value in shifted)
        normalized.append(rounded)
        for axis in range(3):
            min_max[axis] = min(min_max[axis], rounded[axis])
            min_max[axis + 3] = max(min_max[axis + 3], rounded[axis])

    corners = [
        (min_max[3], min_max[4], min_max[2]),
        (min_max[3], min_max[4], min_max[5]),
        (min_max[3], min_max[1], min_max[2]),
        (min_max[3], min_max[1], min_max[5]),
        (min_max[0], min_max[4], min_max[2]),
        (min_max[0], min_max[4], min_max[5]),
        (min_max[0], min_max[1], min_max[2]),
        (min_max[0], min_max[1], min_max[5]),
    ]

    indicator = -(1 << 31)
    packed_offsets: list[int] = []
    offset_count = 0
    corners_at_vertex = [0, 0, 0]

    for j, corner in enumerate(corners):
        closest_vertex_index = 0
        smallest_dist = float("inf")
        for k, vertex in enumerate(normalized):
            if corners_at_vertex[k] >= 3:
                continue
            dist = sum((corner[i] - vertex[i]) ** 2 for i in range(3))
            if dist < smallest_dist:
                smallest_dist = dist
                closest_vertex_index = k
        corners_at_vertex[closest_vertex_index] += 1
        vertex = normalized[closest_vertex_index]
        for axis in range(3):
            offset = int(vertex[axis] - corner[axis])
            if offset == 0:
                continue
            indicator |= 1 << (3 * j + axis)
            if offset_count % 2 == 0:
                packed_offsets.append(signed_int32((offset & 0xFFFF) << 16))
            else:
                packed_offsets[-1] = signed_int32(packed_offsets[-1] | (offset & 0xFFFF))
            offset_count += 1

    if indicator == -(1 << 31):
        return min_max
    return min_max + [signed_int32(indicator)] + [signed_int32(v) for v in packed_offsets]


def obj_to_model(obj_path: Path, grid: int, max_size: int, block: str, color: int) -> LTModel:
    triangles = read_obj(obj_path)
    if not triangles:
        raise ValueError(f"No faces found in {obj_path}")

    all_vertices = [vertex for tri in triangles for vertex in tri]
    min_x = min(v[0] for v in all_vertices)
    min_y = min(v[1] for v in all_vertices)
    min_z = min(v[2] for v in all_vertices)
    max_x = max(v[0] for v in all_vertices)
    max_y = max(v[1] for v in all_vertices)
    max_z = max(v[2] for v in all_vertices)
    size_x = max_x - min_x
    size_y = max_y - min_y
    size_z = max_z - min_z
    longest = max(size_x, size_y, size_z)
    ratio = max_size / longest if longest > 0 else 1.0

    boxes = [LTBox(triangle_to_lt_box(tri, (min_x, min_y, min_z), ratio)) for tri in triangles]
    return LTModel(grid=grid, tiles=[LTTile(block=block, color=color, boxes=boxes)])
