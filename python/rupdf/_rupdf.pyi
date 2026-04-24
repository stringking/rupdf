"""Type stubs for rupdf._rupdf native module."""

from typing import Dict, List, Literal, Tuple, TypedDict, Union

# Type aliases for colors and coordinates
Color = Tuple[int, int, int, int]  # RGBA (0-255 each)
Size = Tuple[float, float]  # (width, height) in points

# Alignment types
HAlign = Literal["left", "center", "right"]
VAlign = Literal["top", "center", "bottom"]
VerticalAnchor = Literal["baseline", "capline", "center"]
TextAlignY = Literal["top", "capline", "center", "baseline", "bottom"]


class TextElement(TypedDict, total=False):
    type: Literal["text"]
    x: float
    y: float
    text: str
    font: str
    size: float
    color: Color
    align: HAlign
    vertical_anchor: VerticalAnchor


class TextBoxElement(TypedDict, total=False):
    """Multi-line text with word wrapping within a fixed box."""

    type: Literal["textbox"]
    x: float
    y: float
    w: float
    h: float
    text: str
    font: str
    size: float
    line_height: float  # defaults to size * 1.2
    color: Color
    box_align_x: HAlign  # positions box relative to (x, y)
    box_align_y: VAlign  # positions box relative to (x, y)
    text_align_x: HAlign  # positions text within box
    text_align_y: TextAlignY  # positions text within box


class RectElement(TypedDict, total=False):
    type: Literal["rect"]
    x: float
    y: float
    w: float
    h: float
    stroke: float
    stroke_color: Color
    fill_color: Color
    corner_radius: float


class LineElement(TypedDict, total=False):
    type: Literal["line"]
    x1: float
    y1: float
    x2: float
    y2: float
    stroke: float
    color: Color


class ImageElement(TypedDict, total=False):
    type: Literal["image"]
    x: float
    y: float
    w: float
    h: float
    image_ref: str
    align: HAlign


class BarcodeElement(TypedDict, total=False):
    type: Literal["barcode", "barcode128"]
    x: float
    y: float
    w: float
    h: float
    value: str
    human_readable: bool
    font: str
    font_size: float


class GS1_128Element(TypedDict, total=False):
    """GS1-128 barcode (Code 128 with FNC1 designator and Application Identifiers).

    `value` is a parenthesized AI string, e.g. "(01)12345678901234(17)260101(10)BATCH123".
    Fixed-length AIs (00, 01-04, 11-19, 20, 31xx-36xx, 41) are validated; FNC1
    separators are inserted automatically after variable-length fields.
    """

    type: Literal["gs1_128", "gs1-128", "gs1"]
    x: float
    y: float
    w: float
    h: float
    value: str
    human_readable: bool
    font: str
    font_size: float


class QRCodeElement(TypedDict, total=False):
    type: Literal["qrcode", "qr"]
    x: float
    y: float
    size: float  # QR codes are square
    value: str
    color: Color  # foreground (dark modules)
    background: Color  # background (light modules)


class DataMatrixElement(TypedDict, total=False):
    """Data Matrix (ECC 200) barcode.

    Use type "gs1_datamatrix" (aliased "gs1-datamatrix") to encode a GS1
    Data Matrix from the parenthesized AI form, e.g.
    "(01)12345678901234(17)260101(10)BATCH123". Fixed-length AIs are
    validated; the FNC1 designator is added automatically.

    `size` is the bounding-box dimension. For square symbols the result is
    a `size × size` block; rectangular symbols (rare with default settings)
    fill the longer axis to `size` and keep modules square.
    """

    type: Literal["datamatrix", "gs1_datamatrix", "gs1-datamatrix"]
    x: float
    y: float
    size: float
    value: str
    color: Color  # foreground (dark modules)
    background: Color  # background (light modules)


Element = Union[
    TextElement,
    TextBoxElement,
    RectElement,
    LineElement,
    ImageElement,
    BarcodeElement,
    GS1_128Element,
    QRCodeElement,
    DataMatrixElement,
]


class FontResource(TypedDict, total=False):
    path: str
    bytes: bytes


class ImageResource(TypedDict, total=False):
    path: str
    bytes: bytes


class Resources(TypedDict, total=False):
    fonts: Dict[str, FontResource]
    images: Dict[str, ImageResource]


class Metadata(TypedDict, total=False):
    title: str
    author: str
    subject: str
    creator: str
    creation_date: str


class Page(TypedDict, total=False):
    size: Size
    background: Color
    elements: List[Element]


class Document(TypedDict, total=False):
    metadata: Metadata
    pages: List[Page]
    resources: Resources


class RupdfError(Exception):
    """Error raised by rupdf operations."""

    ...


def render_pdf(document: Document, *, compress: bool = True) -> bytes:
    """
    Render a document to PDF bytes.

    Args:
        document: Document specification with pages, elements, and resources.
        compress: Whether to compress the PDF content streams (default: True).

    Returns:
        PDF file contents as bytes.

    Raises:
        RupdfError: If rendering fails (missing fonts, invalid elements, etc.)

    Example:
        >>> doc = {
        ...     "pages": [{"size": (612, 792), "elements": []}],
        ...     "resources": {"fonts": {}, "images": {}}
        ... }
        >>> pdf = render_pdf(doc)
        >>> pdf[:5]
        b'%PDF-'
    """
    ...
