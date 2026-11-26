ALLOWED_EXTENSIONS = {'.pdf', '.xlsx', '.csv'}

class ValidationError(ValueError):
    """Raised when a file fails validation. Message is user-safe."""

def validate_upload(filename, content_length, mimetype, max_bytes):
    if not filename or '.' not in filename:
        raise ValidationError('File must have an extension (.pdf, .xlsx, .csv)')
    ext = '.' + filename.rsplit('.', 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(f'Unsupported file type: {ext}. Allowed: pdf, xlsx, csv')
    if content_length is None or content_length <= 0:
        raise ValidationError('File is empty')
    if content_length > max_bytes:
        raise ValidationError(f'File exceeds maximum size ({max_bytes} bytes)')
    return ext