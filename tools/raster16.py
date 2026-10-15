"""Rasterize coordinates into Canon format-0 words for a sixteen-row band.

x counts pattern units and y counts paper rows, top to bottom. Their physical
pitches need not be equal. This host-side generator does not move a motor.
"""
from math import sqrt,isfinite,floor
from pattern_codec import SCAN_ROW_BITS

def line(width,x0,y0,x1,y1):
    """Integer Bresenham line, endpoints included, no silent clipping."""
    if not isinstance(width,int) or width<1:
        raise ValueError('Width must be positive')
    if any(not isinstance(v,int) for v in (x0,y0,x1,y1)):
        raise ValueError('Coordinates must be integers')
    if not (0<=x0<width and 0<=x1<width and 0<=y0<16 and 0<=y1<16):
        raise ValueError('Coordinates outside sixteen-row band')
    columns=[0]*width
    dx,dy=abs(x1-x0),-abs(y1-y0)
    sx,sy=1 if x0<x1 else -1,1 if y0<y1 else -1
    error=dx+dy
    while True:
        columns[x0] |= 1<<SCAN_ROW_BITS[y0]
        if (x0,y0)==(x1,y1): return columns
        twice=2*error
        if twice>=dy: error+=dy; x0+=sx
        if twice<=dx: error+=dx; y0+=sy

def diamond(width,height=16,y0=0):
    if not isinstance(height,int) or not isinstance(y0,int) or height<2 or y0<0 or y0+height>16:
        raise ValueError('Diamond must fit within the sixteen-row band')
    middle=y0+(height-1)//2
    vertices=((0,middle),(width//2,y0),(width-1,middle),(width//2,y0+height-1),(0,middle))
    result=[0]*width
    for a,b in zip(vertices,vertices[1:]):
        result=[p|q for p,q in zip(result,line(width,*a,*b))]
    return result

def ellipse(width,height=16,y0=0):
    """Two samples per column; apparent aspect ratio awaits pitch calibration.

    This deliberately sparse contour tests combining channels. Endpoint
    continuity on paper is an observation, not an antialiasing guarantee.
    """
    if not isinstance(width,int) or width<3 or width%2==0:
        raise ValueError('Ellipse requires an odd width of at least three')
    if not isinstance(height,int) or not isinstance(y0,int) or height<2 or y0<0 or y0+height>16:
        raise ValueError('Ellipse must fit within the sixteen-row band')
    radius=(width-1)/2
    vertical_radius=(height-1)/2
    columns=[]
    for x in range(width):
        offset=vertical_radius*sqrt(max(0,1-((x-radius)/radius)**2))
        local_top=int(vertical_radius-offset+0.5)
        top=y0+local_top
        bottom=y0+height-1-local_top
        columns.append((1<<SCAN_ROW_BITS[top])|(1<<SCAN_ROW_BITS[bottom]))
    return columns

def demo_shapes():
    return {'A':line(23,0,0,22,15),'B':line(23,0,15,22,0),
            'C':diamond(23),'D':ellipse(23)}

def aspect_shapes():
    """Same sixteen-row height, three increasing widths, then four fiducials.

    Fiducial centres are separated by 22 pattern units and 15 row intervals.
    A scan must preserve equal scale on both axes for a physical aspect ratio.
    """
    corners=[0]*23
    corners[0]=corners[-1]=(1<<SCAN_ROW_BITS[0])|(1<<SCAN_ROW_BITS[15])
    return {'A':ellipse(23),'B':ellipse(25),'C':ellipse(27),'D':corners}

def circle(width,row_pitch_ratio):
    """Fit a measured-aspect circle by quantizing its height to physical rows.

    Ratio = row pitch / pattern-unit pitch. Refuse to clip a circle taller
    than the band. This remains a sparse contour, not subpixel rendering.
    """
    if not isinstance(width,int) or width<3 or width%2==0:
        raise ValueError('Circle requires an odd width of at least three')
    if not isfinite(row_pitch_ratio) or row_pitch_ratio<=0:
        raise ValueError('Row pitch ratio must be finite and positive')
    height=floor((width-1)/row_pitch_ratio+0.5)+1
    if not 2<=height<=16:
        raise ValueError('Circle height does not fit the band')
    y0=(16-height)//2
    return ellipse(width,height,y0),{'width_columns':width,'height_rows':height,'top_row':y0,
        'predicted_height_over_width':(height-1)*row_pitch_ratio/(width-1)}

def corrected_circles(row_pitch_ratio):
    wide,wide_geometry=circle(27,row_pitch_ratio)
    small,small_geometry=circle(25,row_pitch_ratio)
    return ({'A':ellipse(27),'B':wide,'C':small,'D':aspect_shapes()['D']},
            {'B':wide_geometry,'C':small_geometry})

def ellipse_closed(width,height,y0=0):
    """Sample both columns AND rows to avoid missing steep ellipse sides.

    Column-only sampling can jump several rows near either horizontal end.
    Complementary row samples retain the same bounding box and symmetry,
    without filling the ellipse interior. Connectivity refers to the logical
    grid; actual ink continuity still depends on head pitch and drive phases.
    """
    columns=ellipse(width,height,y0) # Validate geometry and retain old samples.
    rx,ry=(width-1)/2,(height-1)/2
    for y in range(height):
        offset=rx*sqrt(max(0,1-((y-ry)/ry)**2))
        left=int(rx-offset+0.5)
        right=width-1-left
        mask=1<<SCAN_ROW_BITS[y0+y]
        columns[left] |= mask
        columns[right] |= mask
    return columns

def continuous_contours(row_pitch_ratio):
    sparse,big=circle(27,row_pitch_ratio)
    _,small=circle(25,row_pitch_ratio)
    closed_big=ellipse_closed(27,big['height_rows'],big['top_row'])
    closed_small=ellipse_closed(25,small['height_rows'],small['top_row'])
    return ({'A':sparse,'B':closed_big,'C':closed_small,'D':diamond(25)},
            {'A':big,'B':big,'C':small})

def ellipse_inset_sides(width,height,y0=0):
    """Move only added extreme-side samples one column inward, symmetrically.

    This is an experimental raster correction for the repeated right-side
    protrusion seen on the 27x14 paper contour. It does not establish its
    mechanical cause or change the drive timing. Original cap samples stay.
    """
    sparse=ellipse(width,height,y0)
    result=ellipse_closed(width,height,y0)
    for outer,inner in ((0,1),(width-1,width-2)):
        added=result[outer]&~sparse[outer]
        result[outer]&=~added
        result[inner]|=added
    return result

def refined_contours(row_pitch_ratio):
    old,geometry=continuous_contours(row_pitch_ratio)
    big,small=geometry['B'],geometry['C']
    return ({'A':old['B'],
             'B':ellipse_inset_sides(27,big['height_rows'],big['top_row']),
             'C':old['C'],
             'D':diamond(25,small['height_rows'],small['top_row'])},
            {'A':big,'B':big,'C':small,'D':small})
