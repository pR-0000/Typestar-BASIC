"""Reference global paper renderer: one 64-byte tile at a time, no motors.

Coordinates are raw raster dots, not millimetres or Canon motor request units.
Global geometry is evaluated before tile clipping; no artificial seam borders.
Python wide integers are deliberate: this is not yet a large-radius HD6301 port.
"""
import argparse
import json
from pathlib import Path

from pattern_codec import SCAN_ROW_BITS


class Scene:
    def __init__(self, width, height, shapes):
        if any(type(v) is not int or not 1 <= v <= 4096 for v in (width,height)):
            raise ValueError("Canvas dimensions must be integers in 1..4096")
        self.width, self.height = width, height
        validated = []
        for original in shapes:
            shape = dict(original)
            kind = shape.get("kind")
            keys = {"rectangle": ("x0","y0","x1","y1"),
                    "ellipse": ("cx","cy","rx","ry"),
                    "line": ("x0","y0","x1","y1")}.get(kind)
            if keys is None or any(type(shape.get(k)) is not int for k in keys):
                raise ValueError("Unknown primitive or invalid coordinates")
            pen = shape.setdefault("pen",1)
            fill = shape.setdefault("fill",False)
            if type(pen) is not int or not 1 <= pen <= 16 or type(fill) is not bool:
                raise ValueError("Pen must be 1..16 and fill must be boolean")
            if kind == "ellipse":
                cx,cy,rx,ry = (shape[k] for k in keys)
                if rx < 1 or ry < 1 or not (rx <= cx < width-rx and ry <= cy < height-ry):
                    raise ValueError("Ellipse bounds exceed canvas")
            else:
                x0,y0,x1,y1 = (shape[k] for k in keys)
                if not (0 <= x0 < width and 0 <= x1 < width and 0 <= y0 < height and 0 <= y1 < height):
                    raise ValueError("Endpoint outside canvas")
                if kind == "rectangle" and (x0 > x1 or y0 > y1):
                    raise ValueError("Rectangle corners must be ordered")
                if kind == "line" and fill:
                    raise ValueError("Fill is not a line option")
            validated.append(shape)
        self.shapes = tuple(validated)

    @staticmethod
    def contains(s,x,y):
        pen = s["pen"]
        if s["kind"] == "rectangle":
            if not (s["x0"] <= x <= s["x1"] and s["y0"] <= y <= s["y1"]):
                return False
            return s["fill"] or min(x-s["x0"],s["x1"]-x,y-s["y0"],s["y1"]-y) < pen
        if s["kind"] == "ellipse":
            dx,dy,rx,ry = x-s["cx"],y-s["cy"],s["rx"],s["ry"]
            def inside(xx,yy):
                return xx*xx*ry*ry + yy*yy*rx*rx <= rx*rx*ry*ry
            if not inside(dx,dy):
                return False
            if s["fill"] or pen >= min(rx,ry):
                return True
            ix,iy = rx-pen,ry-pen
            if dx*dx*iy*iy + dy*dy*ix*ix > ix*ix*iy*iy:
                return True
            return any(not inside(a,b) for a,b in ((dx-1,dy),(dx+1,dy),(dx,dy-1),(dx,dy+1)))
        # A segment with round caps, evaluated without floating-point division.
        dx,dy = s["x1"]-s["x0"],s["y1"]-s["y0"]
        px,py = x-s["x0"],y-s["y0"]
        length2 = dx*dx+dy*dy
        dot = px*dx+py*dy
        if length2 == 0 or dot <= 0:
            return 4*(px*px+py*py) <= pen*pen
        if dot >= length2:
            return 4*((x-s["x1"])**2+(y-s["y1"])**2) <= pen*pen
        return 4*(px*dy-py*dx)**2 <= pen*pen*length2

    def pixel(self,x,y):
        # Thick line caps are explicitly clipped to the canvas, not to tiles.
        return 0 <= x < self.width and 0 <= y < self.height and any(self.contains(s,x,y) for s in self.shapes)

    def tiles(self, tile_width=31, skip_blank=True):
        if type(tile_width) is not int or not 1 <= tile_width <= 31:
            raise ValueError("Tile width must be 1..31")
        for top in range(0,self.height,16):
            for left in range(0,self.width,tile_width):
                payload = bytearray(64)
                useful_w, useful_h = min(tile_width,self.width-left),min(16,self.height-top)
                for x in range(useful_w):
                    word = sum(1 << SCAN_ROW_BITS[y] for y in range(useful_h) if self.pixel(left+x,top+y))
                    payload[2*x:2*x+2] = word.to_bytes(2,"big")
                if not skip_blank or any(payload):
                    yield {"x":left,"y":top,"width":useful_w,"height":useful_h,"data":bytes(payload)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scene",type=Path)
    parser.add_argument("--output-dir",type=Path,required=True)
    parser.add_argument("--tile-width",type=int,default=31)
    parser.add_argument("--preview-y-scale",type=int,choices=(1,2,3,4),default=1,
                        help="Illustrative preview aspect only; does not calibrate motor movement")
    args = parser.parse_args()
    spec = json.loads(args.scene.read_text(encoding="utf-8-sig"))
    scene = Scene(spec["width"],spec["height"],spec["shapes"])
    if not 1 <= args.tile_width <= 31:
        parser.error("tile width must be 1..31")
    args.output_dir.mkdir(parents=True,exist_ok=True)
    index = []
    # Only preview and output index use page-sized storage, on the PC. The
    # generator never builds an intermediate page framebuffer.
    from PIL import Image
    preview = Image.new("1",(scene.width,scene.height),1)
    from glyph_definition import unpack_columns
    for i,tile in enumerate(scene.tiles(args.tile_width)):
        name = f"tile-{i:04d}.bin"
        (args.output_dir/name).write_bytes(tile["data"])
        index.append({k:v for k,v in tile.items() if k != "data"} | {"file":name})
        for x,word in enumerate(unpack_columns(tile["data"])[:tile["width"]]):
            for y in range(tile["height"]):
                if word & (1 << (15-y)):
                    preview.putpixel((tile["x"]+x,tile["y"]+y),0)
    preview = preview.resize((scene.width,scene.height*args.preview_y_scale),Image.Resampling.NEAREST)
    preview.save(args.output_dir/"preview.png")
    report = {"width":scene.width,"height":scene.height,"tile_width":args.tile_width,
              "tiles":index,"scratch_native_buffer_bytes":64,
              "preview_y_scale":args.preview_y_scale,
              "limits":"PC reference only. Positions are raster coordinates, not motor commands or millimetres. Wide integer products need a separate bounded HD6301 implementation. Physical horizontal seams and printable A4 area not calibrated."}
    (args.output_dir/"manifest.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(f"Rendered {scene.width}x{scene.height}: {len(index)} nonblank tiles, native buffer 64 bytes")


if __name__ == "__main__":
    main()
