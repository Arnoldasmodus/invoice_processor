from enum import Enum


class DocumentModelId(str, Enum):
    """Supported Azure Document Intelligence Model IDs."""
    INVOICE = "prebuilt-invoice"
    RECEIPT = "prebuilt-receipt"
    LAYOUT = "prebuilt-layout"
    READ = "prebuilt-read"
    CONTRACT = "prebuilt-contract"
    TAX_US_W2 = "prebuilt-tax.us.w2"


class DocumentAnalysisFeature(str, Enum):
    """Azure Document Intelligence analysis features."""
    OCR_HIGH_RESOLUTION = "ocrHighResolution"
    KEY_VALUE_PAIRS = "keyValuePairs"
    LANGUAGES = "languages"
    BARCODES = "barcodes"
    FORMULAS = "formulas"
    STYLE_FONT = "styleFont"


class ProcessingStatus(str, Enum):
    """Status enum for document processing workflow."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SupportedMimeTypes(str, Enum):
    """Supported input MIME types."""
    PDF = "application/pdf"
    PNG = "image/png"
    JPEG = "image/jpeg"
    TIFF = "image/tiff"
    BMP = "image/bmp"


DEFAULT_CONFIDENCE_THRESHOLD = 0.6
