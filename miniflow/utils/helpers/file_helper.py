import os
import io
import uuid
import shutil
import zipfile
import mimetypes
import unicodedata
import threading
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Tuple, Set, Dict, Any, BinaryIO, TextIO, Union

from miniflow.core.exceptions import ResourceNotFoundError, InvalidInputError
from ..handlers import ConfigurationHandler


MAX_FILENAME_LENGTH = 255 
_base_storage_path: Optional[str] = None
_base_storage_path_lock = threading.Lock()
_directory_locks: Dict[str, threading.Lock] = {}
_directory_locks_lock = threading.Lock()


def ensure_directory(path: str) -> None:
    """
    Thread-safe directory creation.
    Uses per-directory locks to prevent race conditions.
    """
    # Get or create lock for this directory
    with _directory_locks_lock:
        if path not in _directory_locks:
            _directory_locks[path] = threading.Lock()
        dir_lock = _directory_locks[path]
    
    # Thread-safe directory creation
    with dir_lock:
        Path(path).mkdir(parents=True, exist_ok=True)

def _get_base_storage_path() -> str:
    """
    Thread-safe base storage path getter with lazy initialization.
    Uses double-checked locking pattern.
    """
    global _base_storage_path
    
    if _base_storage_path is None:
        with _base_storage_path_lock:
            # Double-checked locking
            if _base_storage_path is None:
                project_root = Path(__file__).resolve().parents[4]
                storage_path = project_root / 'resources'
                _base_storage_path = str(storage_path)
    
    return _base_storage_path

def sanitize_filename(name: str) -> str:
    """
    Sanitize filename with strong path traversal protection.
    Removes all path components, double-dots, and dangerous characters.
    """
    if not name:
        return "file"

    name = unicodedata.normalize('NFC', name)

    # Strong path traversal protection - remove all path separators and double-dots
    # Handle various bypass attempts: .., ...., ../, ..\\, etc.
    while ".." in name:
        name = name.replace("..", "")
    name = name.replace("/", "")
    name = name.replace("\\", "")
    name = name.replace("\x00", "")
    name = name.replace(" ", "_")

    # Remove any remaining dangerous characters
    name = "".join(c for c in name if c.isalnum() or c in "._-")

    # Final check - ensure no path traversal components remain
    if not name or name in (".", "..") or name.startswith("..") or ".." in name:
        name = "file"

    if len(name) > MAX_FILENAME_LENGTH:
        name_part, ext = os.path.splitext(name)
        max_name_length = MAX_FILENAME_LENGTH - len(ext)
        if max_name_length > 0:
            name = name_part[:max_name_length] + ext
        else:
            name = name[:MAX_FILENAME_LENGTH]

    return name

def _check_symlink(path: Path) -> None:
    """
    Check if path or any parent is a symlink (before resolve).
    Raises InvalidInputError if symlink detected.
    """
    current = path
    while current != current.parent:
        if current.is_symlink():
            raise InvalidInputError(
                field_name="path",
                message="Symlink detected in path - security risk"
            )
        current = current.parent

def get_global_script_path() -> str:
    """
    Get global script path (not workspace-specific).
    
    Returns:
        Safe global script path: resources/global_scripts
    """
    base_path = _get_base_storage_path()
    
    file_path = Path(base_path) / "global_scripts"
    
    # Check for symlinks BEFORE resolve
    _check_symlink(file_path)
    
    resolved_path = file_path.resolve()
    base_resolved = Path(base_path).resolve()
    
    try:
        resolved_path.relative_to(base_resolved)
    except ValueError:
        raise InvalidInputError(
            field_name="path",
            message="Path traversal attempt detected"
        )
    
    return str(resolved_path)


def get_workspace_global_script_path(workspace_id: str) -> str:
    """
    Workspace global script path creation with path traversal protection.
    
    Args:
        workspace_id: Workspace ID
    
    Returns:
        Safe workspace global script path
    
    Raises:
        InvalidInputError: If workspace_id is invalid or path traversal detected
    """
    base_path = _get_base_storage_path()
    safe_workspace_id = sanitize_filename(workspace_id)
    if not safe_workspace_id or safe_workspace_id in (".", ".."):
        raise InvalidInputError(
            field_name="workspace_id",
            message="Invalid workspace ID"
        )
    
    file_path = Path(base_path) / "global_scripts" / safe_workspace_id
    
    # Check for symlinks BEFORE resolve
    _check_symlink(file_path)
    
    resolved_path = file_path.resolve()
    base_resolved = Path(base_path).resolve()
    
    try:
        resolved_path.relative_to(base_resolved)
    except ValueError:
        raise InvalidInputError(
            field_name="workspace_id",
            message="Path traversal attempt detected"
        )
    
    return str(resolved_path)

def get_workspace_custom_script_path(workspace_id: str) -> str:
    base_path = _get_base_storage_path()
    safe_workspace_id = sanitize_filename(workspace_id)
    if not safe_workspace_id or safe_workspace_id in (".", ".."):
        raise InvalidInputError(
            field_name="workspace_id",
            message="Invalid workspace ID"
        )
    
    file_path = Path(base_path) / "custom_scripts" / safe_workspace_id
    
    # Check for symlinks BEFORE resolve
    _check_symlink(file_path)
    
    resolved_path = file_path.resolve()
    base_resolved = Path(base_path).resolve()
    
    try:
        resolved_path.relative_to(base_resolved)
    except ValueError:
        raise InvalidInputError(
            field_name="workspace_id",
            message="Path traversal attempt detected"
        )
    
    return str(resolved_path)

def get_workspace_file_path(workspace_id: str) -> str:
    base_path = _get_base_storage_path()
    safe_workspace_id = sanitize_filename(workspace_id)
    if not safe_workspace_id or safe_workspace_id in (".", ".."):
        raise InvalidInputError(
            field_name="workspace_id",
            message="Invalid workspace ID"
        )
    
    file_path = Path(base_path) / "files" / safe_workspace_id
    
    # Check for symlinks BEFORE resolve
    _check_symlink(file_path)
    
    resolved_path = file_path.resolve()
    base_resolved = Path(base_path).resolve()
    
    try:
        resolved_path.relative_to(base_resolved)
    except ValueError:
        raise InvalidInputError(
            field_name="workspace_id",
            message="Path traversal attempt detected"
        )
    
    return str(resolved_path)

def get_workspace_temp_path(workspace_id: str) -> str:
    base_path = _get_base_storage_path()
    safe_workspace_id = sanitize_filename(workspace_id)
    if not safe_workspace_id or safe_workspace_id in (".", ".."):
        raise InvalidInputError(
            field_name="workspace_id",
            message="Invalid workspace ID"
        )
    
    file_path = Path(base_path) / "temp" / safe_workspace_id
    
    # Check for symlinks BEFORE resolve
    _check_symlink(file_path)
    
    resolved_path = file_path.resolve()
    base_resolved = Path(base_path).resolve()
    
    try:
        resolved_path.relative_to(base_resolved)
    except ValueError:
        raise InvalidInputError(
            field_name="workspace_id",
            message="Path traversal attempt detected"
        )
    
    return str(resolved_path)

def create_resources_folder() -> None:
    print(f"[FILE HELPER] Creating resources folder...")
    base_path = _get_base_storage_path()
    ensure_directory(base_path)
    print(f"[FILE HELPER] Resources folder created successfully")

    file_path = os.path.join(base_path, "files")
    ensure_directory(file_path)
    print(f"[FILE HELPER] File folder created: {file_path}")

    temp_path = os.path.join(base_path, "temp")
    ensure_directory(temp_path)
    print(f"[FILE HELPER] Temp folder created: {temp_path}")

    global_script_path = os.path.join(base_path, "global_scripts")
    ensure_directory(global_script_path)
    print(f"[FILE HELPER] Global script folder created: {global_script_path}")

    custom_script_path = os.path.join(base_path, "custom_scripts")
    ensure_directory(custom_script_path)
    print(f"[FILE HELPER] Custom script folder created: {custom_script_path}")
    print(f"[FILE HELPER] All resource folders created successfully")


def get_folder_size(folder_path: str) -> int:
    if not os.path.exists(folder_path):
        raise ResourceNotFoundError(resource_name="folder", resource_id=folder_path)

    total_size = 0
    # Symlink bomb protection: followlinks=False prevents following symlinks
    for dirpath, dirnames, filenames in os.walk(folder_path, followlinks=False):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.isfile(fp) and not os.path.islink(fp):  # Skip symlinks
                total_size += os.path.getsize(fp)
    
    return total_size

def delete_folder(folder_path: str) -> None:
    try:
        if not os.path.isdir(folder_path):
            raise ResourceNotFoundError(resource_name="folder", resource_id=folder_path)
        shutil.rmtree(folder_path)
        print(f"[FILE HELPER] Folder deleted: {folder_path}")
    except FileNotFoundError:
        raise ResourceNotFoundError(resource_name="folder", resource_id=folder_path)
    except Exception as e:
        print(f"[FILE HELPER] Folder deletion error: {str(e)}")
        raise InvalidInputError(field_name="folder_path", message=f"Folder deletion error: {str(e)}")


def file_exists(file_path: str) -> bool:
    return os.path.exists(file_path) and os.path.isfile(file_path)

def create_file(uploaded_file: Union[BinaryIO, TextIO], file_path: str) -> Tuple[int, float]:
    """
    Create file from uploaded file object using streaming (memory-safe).
    
    Args:
        uploaded_file: File-like object (binary or text)
        file_path: Destination file path
    
    Returns:
        Tuple[int, float]: (file_size_bytes, size_kb)
    
    Raises:
        InvalidInputError: If file cannot be written
    """
    directory = os.path.dirname(file_path)
    if directory:
        ensure_directory(directory)

    # Memory-safe streaming write
    file_size = 0
    temp_file_path = file_path + '.tmp'
    
    try:
        # Determine if binary or text mode
        is_binary = hasattr(uploaded_file, 'mode') and 'b' in getattr(uploaded_file, 'mode', '')
        
        # Stream file content to temporary file
        with open(temp_file_path, 'wb') as f:
            chunk_size = 8192  # 8KB chunks
            while True:
                if is_binary:
                    chunk = uploaded_file.read(chunk_size)
                    if not chunk:
                        break
                    if isinstance(chunk, str):
                        chunk = chunk.encode('utf-8')
                else:
                    chunk = uploaded_file.read(chunk_size)
                    if not chunk:
                        break
                    if isinstance(chunk, str):
                        chunk = chunk.encode('utf-8')
                
                file_size += len(chunk)
                f.write(chunk)
        
        # Set secure permissions
        try:
            os.chmod(temp_file_path, 0o600)
        except (OSError, PermissionError):
            pass
        
        # Atomic rename
        try:
            os.rename(temp_file_path, file_path)
        except (OSError, PermissionError):
            # Fallback for network filesystems
            shutil.copy2(temp_file_path, file_path)
            os.remove(temp_file_path)
    
    except Exception as e:
        # Cleanup on error
        try:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        except Exception:
            pass
        raise InvalidInputError(
            field_name="file_path",
            message=f"File could not be created: {str(e)}"
        )
    
    size_kb = file_size / 1024
    return file_size, size_kb

def create_file_with_content(content: str, file_path: str) -> Tuple[int, float]:
    """
    Create file with string content using atomic write.
    
    Args:
        content: File content as string
        file_path: Destination file path
    
    Returns:
        Tuple[int, float]: (file_size_bytes, size_kb)
    
    Raises:
        InvalidInputError: If content is empty or file cannot be written
    """
    if not content:
        raise InvalidInputError(
            field_name="content",
            message="Content cannot be empty"
        )
    
    directory = os.path.dirname(file_path)
    if directory:
        ensure_directory(directory)

    # Atomic file write
    temp_file_path = file_path + '.tmp'
    content_bytes = content.encode('utf-8')
    file_size = len(content_bytes)
    
    try:
        with open(temp_file_path, 'wb') as f:
            f.write(content_bytes)
        
        # Set secure permissions
        try:
            os.chmod(temp_file_path, 0o600)
        except (OSError, PermissionError):
            pass
        
        # Atomic rename
        try:
            os.rename(temp_file_path, file_path)
        except (OSError, PermissionError):
            # Fallback for network filesystems
            shutil.copy2(temp_file_path, file_path)
            os.remove(temp_file_path)
    
    except Exception as e:
        # Cleanup on error
        try:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        except Exception:
            pass
        raise InvalidInputError(
            field_name="file_path",
            message=f"File could not be created: {str(e)}"
        )
    
    size_kb = file_size / 1024
    return file_size, size_kb

def read_file(file_path: str, max_size: Optional[int] = None) -> bytes:
    """
    Read file content with optional size limit (memory-safe).
    
    Args:
        file_path: Path to file
        max_size: Maximum bytes to read (None = no limit, but warns if > 100MB)
    
    Returns:
        bytes: File content
    
    Raises:
        ResourceNotFoundError: If file doesn't exist
        InvalidInputError: If file exceeds max_size
    """
    if not os.path.exists(file_path):
        raise ResourceNotFoundError(resource_name="file", resource_id=file_path)
    
    file_size = os.path.getsize(file_path)
    
    # Safety check: warn if reading large files without limit
    if max_size is None and file_size > 100 * 1024 * 1024:  # 100MB
        raise InvalidInputError(
            field_name="file_path",
            message=f"File too large ({file_size / 1024 / 1024:.2f} MB). Use max_size parameter or streaming."
        )
    
    if max_size is not None and file_size > max_size:
        raise InvalidInputError(
            field_name="file_path",
            message=f"File size ({file_size} bytes) exceeds max_size ({max_size} bytes)"
        )
    
    # For small files, read directly (efficient)
    # For larger files, could stream but bytes return type requires full read
    with open(file_path, 'rb') as f:
        return f.read()

def delete_file(file_path: str) -> None:
    try:
        if not os.path.isfile(file_path):
            raise ResourceNotFoundError(resource_name="file", resource_id=file_path)
        os.remove(file_path)
    except FileNotFoundError:
        raise ResourceNotFoundError(resource_name="file", resource_id=file_path)
    except Exception as e:
        raise ResourceNotFoundError(resource_name="file", resource_id=file_path)

def get_file_size(file_path: str) -> int:
    if not file_exists(file_path):
        raise ResourceNotFoundError(resource_name="file", resource_id=file_path)
    
    return os.path.getsize(file_path)

# Removed unused functions: validate_file_extension, get_mime_type_from_extension, validate_mime_type
# These functions are not used anywhere in the codebase and were causing dead code warnings.


def generate_unique_filename(original_filename: str, workspace_id: str) -> str:
    """
    Generate unique filename with sanitized workspace_id and 16-character UUID.
    
    Args:
        original_filename: Original filename
        workspace_id: Workspace ID (will be sanitized)
    
    Returns:
        Unique filename with timestamp, sanitized workspace_id, 16-char UUID, and sanitized name
    """
    name, ext = os.path.splitext(original_filename)
    # Use 16 characters from UUID (reduces collision risk significantly)
    unique_id = str(uuid.uuid4().hex[:16])
    # Use UTC timezone for timestamp
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    name = sanitize_filename(name)
    
    # Sanitize workspace_id before including in filename
    safe_workspace_id = sanitize_filename(workspace_id)
    if not safe_workspace_id or safe_workspace_id in (".", ".."):
        safe_workspace_id = "workspace"

    fixed_length = len(timestamp) + 1 + len(safe_workspace_id) + 1 + len(unique_id) + 1
    available_length = MAX_FILENAME_LENGTH - fixed_length - len(ext)

    if available_length > 0 and len(name) > available_length:
        name = name[:available_length]

    new_name = f"{timestamp}_{safe_workspace_id}_{unique_id}_{name}{ext}"
    new_name = sanitize_filename(new_name)

    if ext and not new_name.endswith(ext):
        if len(new_name) + len(ext) <= MAX_FILENAME_LENGTH:
            new_name = new_name + ext
        else:
            truncate_length = MAX_FILENAME_LENGTH - len(ext)
            new_name = new_name[:truncate_length] + ext
    
    return new_name

def _detect_zip_mime_type(content: bytes) -> str:
    try:
        zip_buffer = io.BytesIO(content)
        
        with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
            namelist = zip_file.namelist()
            
            if any('word/' in name.lower() for name in namelist) or \
               any('[Content_Types].xml' in name for name in namelist):
                if any(name.endswith('.xml') and 'word' in name.lower() for name in namelist):
                    return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            
            if any('xl/' in name.lower() for name in namelist) or \
               any('worksheets/' in name.lower() for name in namelist):
                return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            
            if any('ppt/' in name.lower() for name in namelist):
                return 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
            
            return 'application/zip'
            
    except (zipfile.BadZipFile, Exception):
        return 'application/zip'

def _detect_mime_type_from_content(content: bytes) -> Optional[str]:
    if not content or len(content) < 4:
        return None
    
    # Magic bytes signatures
    signatures = {
        # Images
        b'\xFF\xD8\xFF': 'image/jpeg',
        b'\x89PNG\r\n\x1a\n': 'image/png',
        b'GIF87a': 'image/gif',
        b'GIF89a': 'image/gif',
        b'BM': 'image/bmp',
        b'RIFF': 'image/webp',
        b'<svg': 'image/svg+xml',
        
        # Documents
        b'%PDF': 'application/pdf',
        b'PK\x03\x04': 'application/zip',  # ZIP, DOCX, XLSX, PPTX
        b'\xd0\xcf\x11\xe0': 'application/msword',  # Old MS Office
        
        # Text
        b'\xEF\xBB\xBF': 'text/plain',  # UTF-8 BOM
        b'\xFF\xFE': 'text/plain',  # UTF-16 LE BOM
        b'\xFE\xFF': 'text/plain',  # UTF-16 BE BOM
        
        # Archives
        b'\x1f\x8b': 'application/gzip',
        b'Rar!\x1a\x07': 'application/x-rar-compressed',
        b'7z\xbc\xaf\x27\x1c': 'application/x-7z-compressed',
        b'ustar': 'application/x-tar',  # TAR
        b'MSCF': 'application/vnd.ms-cab-compressed',  # CAB
        
        # Audio
        b'ID3': 'audio/mpeg',  # MP3 with ID3 tag
        b'\xFF\xFB': 'audio/mpeg',  # MP3 without ID3
        b'\xFF\xF3': 'audio/mpeg',  # MP3
        b'\xFF\xF2': 'audio/mpeg',  # MP3
        b'RIFF': 'audio/wav',  # WAV (check after RIFF)
        b'fLaC': 'audio/flac',  # FLAC
        b'OggS': 'audio/ogg',  # OGG
        b'ftyp': 'audio/mp4',  # M4A
        
        # Video
        b'\x00\x00\x00\x18ftyp': 'video/mp4',  # MP4
        b'\x00\x00\x00\x20ftyp': 'video/mp4',  # MP4
        b'RIFF': 'video/avi',  # AVI (check after RIFF)
        b'\x00\x00\x00\x14ftypqt': 'video/quicktime',  # MOV
        b'\x1a\x45\xdf\xa3': 'video/x-matroska',  # MKV
    }
    
    # Check first 512 bytes
    header = content[:512]
    
    for signature, mime_type in signatures.items():
        if header.startswith(signature):
            # ZIP-based formats - use zipfile for proper detection
            if signature == b'PK\x03\x04':
                return _detect_zip_mime_type(content)
            
            # RIFF-based formats need additional check
            if signature == b'RIFF' and len(header) >= 12:
                if header[8:12] == b'WEBP':
                    return 'image/webp'
                elif header[8:12] == b'WAVE':
                    return 'audio/wav'
                elif header[8:12] == b'AVI ':
                    return 'video/x-msvideo'
            
            return mime_type
    
    return None    


def upload_file(
    uploaded_file: Union[BinaryIO, TextIO],
    workspace_id: str,
    max_file_size_mb: Optional[int] = None,
    allowed_extensions: Optional[Set[str]] = None,
    blocked_extensions: Optional[Set[str]] = None,
    allowed_mime_types: Optional[Set[str]] = None
) -> Dict[str, Any]:
    """
    Process, validate and save file from API with security features.
    
    Security features:
    - Path traversal protection
    - Memory-efficient streaming (for large files)
    - Magic bytes check (real file type detection)
    - Atomic file operations (TOCTOU protection)
    - Secure file permissions (owner read/write only)
    
    Args:
        uploaded_file: File object from API (form data)
        workspace_id: Workspace ID
        max_file_size_mb: Maximum file size (MB). 
            - If provided: Uses this value (allows dynamic plan-based limits)
            - If None: Reads from configuration file ("FILE OPERATIONS" section)
            Example: For plan-based limits, pass the plan's max_file_size_mb value here
        allowed_extensions: Allowed file extensions. 
            - If provided: Uses this set
            - If None: Reads from configuration file ("FILE OPERATIONS" section)
        blocked_extensions: Blocked file extensions.
            - If provided: Uses this set
            - If None: Reads from configuration file ("FILE OPERATIONS" section)
        allowed_mime_types: Allowed MIME types.
            - If provided: Uses this set
            - If None: Reads from configuration file ("FILE OPERATIONS" section)
    
    Returns:
        Dict[str, Any]: File information
            - file_path: File path
            - file_size: File size (bytes)
            - mime_type: MIME type
            - extension: File extension
            - file_name: File name
    
    Raises:
        InvalidInputError: When file size limit exceeded or invalid file type
    
    Example:
        # Using config default (100 MB from dev.ini)
        result = upload_file(uploaded_file, workspace_id="workspace123")
        
        # Using dynamic plan-based limit (e.g., 50 MB from user plan)
        result = upload_file(uploaded_file, workspace_id="workspace123", max_file_size_mb=50)
        
        # Using custom extensions
        result = upload_file(
            uploaded_file, 
            workspace_id="workspace123",
            allowed_extensions={".pdf", ".doc", ".docx"}
        )
    """
    # Load configuration
    try:
        ConfigurationHandler.load_config()
    except Exception:
        pass  # Already loaded
    
    original_filename = uploaded_file.filename if hasattr(uploaded_file, 'filename') else "unknown"
    if original_filename == "unknown":
        raise InvalidInputError(
            field_name="file",
            message="File name not found"
        )

    if max_file_size_mb is None:
        max_file_size_mb = ConfigurationHandler.get_int("FILE OPERATIONS", "max_file_size_mb", fallback=None)
    max_file_size_bytes = (max_file_size_mb * 1024 * 1024) if max_file_size_mb and max_file_size_mb > 0 else None

    # Memory-safe streaming: read first chunk for magic bytes, then stream to file
    file_size = 0
    magic_bytes = None
    temp_file_path = None

    try:
        if hasattr(uploaded_file, 'seek'):
            try:
                uploaded_file.seek(0)
            except (AttributeError, OSError):
                pass

        # Read first 512 bytes for magic bytes detection (memory-safe)
        first_chunk = uploaded_file.read(512)
        if not first_chunk:
            raise InvalidInputError(
                field_name="file",
                message="File is empty"
            )

        if isinstance(first_chunk, bytes):
            magic_bytes = first_chunk
            file_size = len(first_chunk)
        else:
            magic_bytes = first_chunk.encode('utf-8')
            file_size = len(magic_bytes)
        
        # Stream remaining content directly to temporary file (memory-safe)
        # Don't accumulate in memory - write directly to disk
        chunk_size = 8192  # 8KB chunks
        
        # Create temporary file for streaming write
        workspace_file_path = get_workspace_file_path(workspace_id)
        ensure_directory(workspace_file_path)
        temp_file_path = os.path.join(workspace_file_path, f".tmp_{uuid.uuid4().hex}")
        
        with open(temp_file_path, 'wb') as temp_file:
            # Write first chunk
            if isinstance(first_chunk, bytes):
                temp_file.write(first_chunk)
            else:
                temp_file.write(first_chunk.encode('utf-8'))
            
            # Stream remaining chunks
            while True:
                chunk = uploaded_file.read(chunk_size)
                if not chunk:
                    break
                
                if isinstance(chunk, bytes):
                    chunk_size_bytes = len(chunk)
                else:
                    chunk = chunk.encode('utf-8')
                    chunk_size_bytes = len(chunk)
                
                file_size += chunk_size_bytes
                
                # Check size limit during streaming (before writing)
                if max_file_size_bytes and file_size > max_file_size_bytes:
                    # Cleanup temp file
                    try:
                        if os.path.exists(temp_file_path):
                            os.remove(temp_file_path)
                    except Exception:
                        pass
                    raise InvalidInputError(
                        field_name="file",
                        message=f"File size limit exceeded. Maximum: {max_file_size_mb} MB"
                    )
                
                temp_file.write(chunk)
        
    except InvalidInputError:
        # Cleanup on validation error
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception:
                pass
        raise
    except Exception as e:
        # Cleanup on read error
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception:
                pass
        raise InvalidInputError(
            field_name="file",
            message=f"File could not be read: {str(e)}"
        )

    if file_size == 0:
        raise InvalidInputError(
            field_name="file",
            message="Empty files cannot be uploaded"
        )
    
    # Sanitize filename (preserving extension)
    sanitized_name = sanitize_filename(original_filename)
    original_ext = os.path.splitext(original_filename)[1]
    if original_ext and not sanitized_name.endswith(original_ext.lower()):
        sanitized_name = sanitized_name + original_ext.lower()
    
    # Calculate file extension (preserve case for case-sensitive filesystems)
    # But normalize to lowercase for validation
    extension_with_case = os.path.splitext(sanitized_name)[1]
    extension = extension_with_case.lower()  # Use lowercase for validation
    if not extension:
        raise InvalidInputError(
            field_name="filename",
            message="File extension not found"
        )
    
    # MIME type detection - first magic bytes, then extension
    mime_type_from_content = None
    if magic_bytes and isinstance(magic_bytes, bytes) and len(magic_bytes) >= 4:
        mime_type_from_content = _detect_mime_type_from_content(magic_bytes)
    
    mime_type_from_extension, _ = mimetypes.guess_type(sanitized_name)
    if not mime_type_from_extension:
        mime_type_from_extension = mimetypes.types_map.get(extension, "application/octet-stream")
    
    # MIME type mismatch detection - REJECT if mismatch detected
    if mime_type_from_content and mime_type_from_extension:
        # Normalize for comparison (remove parameters, lowercase)
        content_mime = mime_type_from_content.lower().split(';')[0].strip()
        extension_mime = mime_type_from_extension.lower().split(';')[0].strip()
        
        # If magic bytes and extension don't match, REJECT (security risk)
        if content_mime != extension_mime:
            raise InvalidInputError(
                field_name="file",
                message=f"MIME type mismatch detected. Content type: {mime_type_from_content}, Extension type: {mime_type_from_extension}. File rejected for security."
            )
        mime_type = mime_type_from_content
    else:
        mime_type = mime_type_from_content or mime_type_from_extension
    
    # Get default values from configuration
    if allowed_extensions is None:
        allowed_extensions_list = ConfigurationHandler.get_list("FILE OPERATIONS", "allowed_extensions", fallback=[])
        allowed_extensions = {ext.strip().lower() for ext in allowed_extensions_list}
    
    if blocked_extensions is None:
        blocked_extensions_list = ConfigurationHandler.get_list("FILE OPERATIONS", "blocked_extensions", fallback=[])
        blocked_extensions = {ext.strip().lower() for ext in blocked_extensions_list}
    
    if allowed_mime_types is None:
        allowed_mime_types_list = ConfigurationHandler.get_list("FILE OPERATIONS", "allowed_mime_types", fallback=[])
        allowed_mime_types = {mime.strip().lower() for mime in allowed_mime_types_list}
    
    # File extension validation
    if allowed_extensions and extension not in allowed_extensions:
        raise InvalidInputError(
            field_name="file",
            message=f"File extension not allowed: {extension}"
        )
    
    if blocked_extensions and extension in blocked_extensions:
        raise InvalidInputError(
            field_name="file",
            message=f"File type blocked: {extension}"
        )
    
    # Multi-level double extension check (all levels)
    # Check for blocked extensions at ALL levels (e.g., file.exe.txt, file.exe.txt.zip)
    if blocked_extensions:
        parts = sanitized_name.split('.')
        if len(parts) > 1:  # Has at least one extension
            # Check all parts except the last (which is the main extension)
            for part in parts[:-1]:
                if part.lower() in blocked_extensions:
                    raise InvalidInputError(
                        field_name="file",
                        message=f"Suspicious file extension detected at multiple levels: {part}"
                    )
            # Also check if any part contains blocked extension pattern
            for i in range(len(parts) - 1):
                potential_ext = '.' + parts[i].lower()
                if potential_ext in blocked_extensions:
                    raise InvalidInputError(
                        field_name="file",
                        message=f"Suspicious file extension pattern detected: {potential_ext}"
                    )
    
    # MIME type validation
    if allowed_mime_types and mime_type.lower() not in allowed_mime_types:
        raise InvalidInputError(
            field_name="file",
            message=f"File type not allowed: {mime_type}"
        )
    
    # Generate unique filename (with sanitized name)
    unique_filename = generate_unique_filename(sanitized_name, workspace_id)
    
    # Create file path (safe path)
    workspace_file_path = get_workspace_file_path(workspace_id)
    ensure_directory(workspace_file_path)
    
    # Path.resolve() for absolute path and path traversal check
    file_path_obj = Path(workspace_file_path) / unique_filename
    
    # Check for symlinks BEFORE resolve
    _check_symlink(file_path_obj)
    
    resolved_path = file_path_obj.resolve()
    base_resolved = Path(workspace_file_path).resolve()
    
    # Path traversal check
    try:
        resolved_path.relative_to(base_resolved)
    except ValueError:
        raise InvalidInputError(
            field_name="file",
            message="Path traversal attempt detected"
        )
    
    file_path = str(resolved_path)
    
    # Atomic file write (TOCTOU protection)
    # Content already in temp_file_path from streaming, just rename it
    # temp_file_path was created during streaming above
    
    try:
        # Create directory
        directory = os.path.dirname(file_path)
        if directory:
            ensure_directory(directory)

        # Set secure file permissions (owner read/write only)
        try:
            os.chmod(temp_file_path, 0o600)
        except (OSError, PermissionError):
            # Continue - some filesystems don't support chmod
            pass
        
        # Atomic rename (TOCTOU protection)
        # Try atomic rename first, fallback to copy+delete for network filesystems
        try:
            os.rename(temp_file_path, file_path)
        except (OSError, PermissionError):
            # Fallback for network filesystems that don't support atomic rename
            try:
                # Copy then delete (not atomic but works on network filesystems)
                shutil.copy2(temp_file_path, file_path)
                os.remove(temp_file_path)
            except Exception as fallback_error:
                # Cleanup on fallback failure
                try:
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                except Exception:
                    pass
                raise fallback_error
        
    except OSError as e:
        # Handle quota limits and disk space errors explicitly
        error_code = getattr(e, 'errno', None)
        if error_code == 28:  # ENOSPC - No space left on device
            raise InvalidInputError(
                field_name="file",
                message="Disk quota exceeded or no space left on device"
            )
        elif error_code == 122:  # EDQUOT - Disk quota exceeded
            raise InvalidInputError(
                field_name="file",
                message="Disk quota exceeded"
            )
        else:
            raise InvalidInputError(
                field_name="file",
                message=f"File system error: {str(e)}"
            )
    except Exception as e:
        # Cleanup temporary file
        try:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        except Exception:
            pass
        
        raise InvalidInputError(
            field_name="file",
            message=f"File could not be saved: {str(e)}"
        )
    
    size_kb = file_size / 1024
    
    return {
        "file_path": file_path,
        "file_size": file_size,
        "mime_type": mime_type,
        "extension": extension,
        "file_name": unique_filename
    }


def upload_custom_script(
    content: str,
    script_name: str,
    extension: str,
    workspace_id: str,
    category: Optional[str] = None,
    subcategory: Optional[str] = None
) -> Dict[str, Any]:
    """
    Upload custom script file with content.
    Creates file at: resources/custom_scripts/{workspace_id}/{category?}/{subcategory?}/{script_name}.{extension}
    
    Validates against CUSTOM SCRIPTS configuration:
    - allowed_script_extensions: Allowed script extensions
    - allowed_script_mime_types: Allowed MIME types (optional)
    - max_script_size_mb: Maximum script size in MB
    - script_validation_enabled: Whether to validate script content
    
    Args:
        content: Script content (string)
        script_name: Script name (without extension)
        extension: File extension (with or without dot, e.g., 'py' or '.py')
        workspace_id: Workspace ID
        category: Optional category for organizing scripts (will be sanitized and added to path)
        subcategory: Optional subcategory for organizing scripts (will be sanitized and added to path)
    
    Returns:
        Dict[str, Any]: Script file information
            - file_path: Final file path where script was saved (absolute path)
            - file_size: File size in bytes
            - mime_type: Detected MIME type
            - extension: File extension (normalized)
            - file_name: Final filename
    
    Raises:
        InvalidInputError: If content is empty, invalid path, extension not allowed, MIME type not allowed, size exceeded, or file system error
    """
    # Load configuration
    try:
        ConfigurationHandler.load_config()
    except Exception:
        pass  # Already loaded
    
    if not content:
        raise InvalidInputError(
            field_name="content",
            message="Content cannot be empty"
        )
    
    if not script_name:
        raise InvalidInputError(
            field_name="script_name",
            message="Script name cannot be empty"
        )
    
    if not extension:
        raise InvalidInputError(
            field_name="extension",
            message="Extension cannot be empty"
        )
    
    # Normalize extension (ensure it starts with dot)
    if not extension.startswith('.'):
        extension = '.' + extension
    
    extension_lower = extension.lower()
    
    # Validate script extension against configuration
    allowed_script_extensions_list = ConfigurationHandler.get_list("CUSTOM SCRIPTS", "allowed_script_extensions", fallback=[".py"])
    allowed_script_extensions = {ext.strip().lower() for ext in allowed_script_extensions_list}
    
    if extension_lower not in allowed_script_extensions:
        raise InvalidInputError(
            field_name="extension",
            message=f"Script extension not allowed: {extension}. Allowed extensions: {', '.join(allowed_script_extensions)}"
        )
    
    # Validate script size against configuration
    max_script_size_mb = ConfigurationHandler.get_int("CUSTOM SCRIPTS", "max_script_size_mb", fallback=1)
    max_script_size_bytes = max_script_size_mb * 1024 * 1024
    
    content_bytes = content.encode('utf-8')
    content_size = len(content_bytes)
    if content_size > max_script_size_bytes:
        raise InvalidInputError(
            field_name="content",
            message=f"Script size ({content_size / 1024 / 1024:.2f} MB) exceeds maximum allowed size ({max_script_size_mb} MB)"
        )
    
    # Detect MIME type from extension
    mime_type_from_extension, _ = mimetypes.guess_type(f"file{extension}")
    if not mime_type_from_extension:
        # Default MIME types for common script extensions
        mime_type_map = {
            '.py': 'text/x-python',
            '.js': 'application/javascript',
            '.ts': 'application/typescript',
            '.sh': 'application/x-sh',
            '.bash': 'application/x-sh',
            '.zsh': 'application/x-sh',
            '.ps1': 'application/x-powershell',
            '.rb': 'text/x-ruby',
            '.php': 'text/x-php',
            '.go': 'text/x-go',
            '.java': 'text/x-java-source',
            '.cpp': 'text/x-c++src',
            '.c': 'text/x-csrc',
        }
        mime_type_from_extension = mime_type_map.get(extension_lower, 'text/plain')
    
    mime_type = mime_type_from_extension
    
    # Validate MIME type against configuration (if configured)
    allowed_script_mime_types_list = ConfigurationHandler.get_list("CUSTOM SCRIPTS", "allowed_script_mime_types", fallback=[])
    if allowed_script_mime_types_list:
        allowed_script_mime_types = {mime.strip().lower() for mime in allowed_script_mime_types_list}
        if mime_type.lower() not in allowed_script_mime_types:
            raise InvalidInputError(
                field_name="extension",
                message=f"Script MIME type not allowed: {mime_type}. Allowed MIME types: {', '.join(allowed_script_mime_types)}"
            )
    
    # Script validation (if enabled)
    script_validation_enabled = ConfigurationHandler.get_bool("CUSTOM SCRIPTS", "script_validation_enabled", fallback=True)
    if script_validation_enabled:
        # Basic validation: check for dangerous patterns (can be extended)
        dangerous_patterns = [
            "import os.system",
            "import subprocess",
            "__import__",
            "eval(",
            "exec(",
            "compile(",
        ]
        content_lower = content.lower()
        for pattern in dangerous_patterns:
            if pattern.lower() in content_lower:
                raise InvalidInputError(
                    field_name="content",
                    message=f"Script contains potentially dangerous pattern: {pattern}"
                )
    
    # Sanitize script name
    sanitized_script_name = sanitize_filename(script_name)
    
    # Build filename with extension
    filename = f"{sanitized_script_name}{extension}"
    
    # Ensure filename length is within limit
    if len(filename) > MAX_FILENAME_LENGTH:
        # Truncate filename while preserving extension
        name_part = sanitized_script_name
        max_name_length = MAX_FILENAME_LENGTH - len(extension)
        if max_name_length > 0:
            truncated_name = name_part[:max_name_length] + extension
            filename = truncated_name
        else:
            raise InvalidInputError(
                field_name="script_name",
                message=f"Filename too long (max {MAX_FILENAME_LENGTH} characters)"
            )
    
    # Get workspace custom script path (with path traversal protection)
    workspace_script_path = get_workspace_custom_script_path(workspace_id)
    ensure_directory(workspace_script_path)
    
    # Add category and subcategory to path if provided
    if category:
        safe_category = sanitize_filename(category)
        workspace_script_path = os.path.join(workspace_script_path, safe_category)
        ensure_directory(workspace_script_path)
        if subcategory:
            safe_subcategory = sanitize_filename(subcategory)
            workspace_script_path = os.path.join(workspace_script_path, safe_subcategory)
            ensure_directory(workspace_script_path)
    
    # Build full file path
    file_path_obj = Path(workspace_script_path) / filename
    
    # Check for symlinks BEFORE resolve
    _check_symlink(file_path_obj)
    
    resolved_path = file_path_obj.resolve()
    base_resolved = Path(workspace_script_path).resolve()
    
    # Path traversal check
    try:
        resolved_path.relative_to(base_resolved)
    except ValueError:
        raise InvalidInputError(
            field_name="script_name",
            message="Path traversal attempt detected"
        )
    
    final_path_str = str(resolved_path)
    
    # Atomic file write (TOCTOU protection)
    temp_file_path = final_path_str + '.tmp'
    
    try:
        # Write to temporary file
        with open(temp_file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Set secure file permissions (owner read/write only)
        try:
            os.chmod(temp_file_path, 0o600)
        except (OSError, PermissionError):
            # Continue - some filesystems don't support chmod
            pass
        
        # Atomic rename (TOCTOU protection)
        try:
            os.rename(temp_file_path, final_path_str)
        except (OSError, PermissionError):
            # Fallback for network filesystems
            try:
                shutil.copy2(temp_file_path, final_path_str)
                os.remove(temp_file_path)
            except Exception as fallback_error:
                # Cleanup on fallback failure
                try:
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                except Exception:
                    pass
                raise fallback_error
        
    except OSError as e:
        # Handle quota limits
        error_code = getattr(e, 'errno', None)
        if error_code == 28:  # ENOSPC - No space left on device
            raise InvalidInputError(
                field_name="file_path",
                message="Disk quota exceeded or no space left on device"
            )
        elif error_code == 122:  # EDQUOT - Disk quota exceeded
            raise InvalidInputError(
                field_name="file_path",
                message="Disk quota exceeded"
            )
        else:
            raise InvalidInputError(
                field_name="file_path",
                message=f"File system error: {str(e)}"
            )
    except Exception as e:
        # Cleanup temporary file
        try:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        except Exception:
            pass
        
        raise InvalidInputError(
            field_name="file_path",
            message=f"File could not be saved: {str(e)}"
        )
    
    return {
        "file_path": final_path_str,
        "file_size": content_size,
        "mime_type": mime_type,
        "extension": extension_lower,
        "file_name": filename
    }


def upload_global_script(
    content: str,
    script_name: str,
    extension: str,
    category: Optional[str] = None,
    subcategory: Optional[str] = None
) -> Dict[str, Any]:
    """
    Upload global script file with content.
    Creates file at: resources/global_scripts/{category?}/{subcategory?}/{script_name}.{extension}
    
    Global scripts are not workspace-specific and available to all workspaces.
    
    Validates against GLOBAL SCRIPTS configuration (if exists):
    - allowed_script_extensions: Allowed script extensions (optional)
    - allowed_script_mime_types: Allowed MIME types (optional)
    - max_script_size_mb: Maximum script size in MB (optional)
    
    Args:
        content: Script content (string)
        script_name: Script name (without extension)
        extension: File extension (with or without dot, e.g., 'py' or '.py')
        category: Optional category for organizing scripts (will be sanitized and added to path)
        subcategory: Optional subcategory for organizing scripts (will be sanitized and added to path)
    
    Returns:
        Dict[str, Any]: Script file information
            - file_path: Final file path where script was saved (absolute path)
            - file_size: File size in bytes
            - mime_type: Detected MIME type
            - extension: File extension (normalized)
            - file_name: Final filename
    
    Raises:
        InvalidInputError: If content is empty, invalid path, extension not allowed, MIME type not allowed, size exceeded, or file system error
    """
    if not content:
        raise InvalidInputError(
            field_name="content",
            message="Content cannot be empty"
        )
    
    if not script_name:
        raise InvalidInputError(
            field_name="script_name",
            message="Script name cannot be empty"
        )
    
    if not extension:
        raise InvalidInputError(
            field_name="extension",
            message="Extension cannot be empty"
        )
    
    # Load configuration
    try:
        ConfigurationHandler.load_config()
    except Exception:
        pass  # Already loaded
    
    # Normalize extension (ensure it starts with dot)
    if not extension.startswith('.'):
        extension = '.' + extension
    
    extension_lower = extension.lower()
    
    # Validate script extension against configuration (if configured)
    allowed_script_extensions_list = ConfigurationHandler.get_list("GLOBAL SCRIPTS", "allowed_script_extensions", fallback=[])
    if allowed_script_extensions_list:
        allowed_script_extensions = {ext.strip().lower() for ext in allowed_script_extensions_list}
        if extension_lower not in allowed_script_extensions:
            raise InvalidInputError(
                field_name="extension",
                message=f"Script extension not allowed: {extension}. Allowed extensions: {', '.join(allowed_script_extensions)}"
            )
    
    # Validate script size against configuration (if configured)
    max_script_size_mb = ConfigurationHandler.get_int("GLOBAL SCRIPTS", "max_script_size_mb", fallback=None)
    if max_script_size_mb:
        max_script_size_bytes = max_script_size_mb * 1024 * 1024
        content_bytes = content.encode('utf-8')
        content_size = len(content_bytes)
        if content_size > max_script_size_bytes:
            raise InvalidInputError(
                field_name="content",
                message=f"Script size ({content_size / 1024 / 1024:.2f} MB) exceeds maximum allowed size ({max_script_size_mb} MB)"
            )
    else:
        content_bytes = content.encode('utf-8')
        content_size = len(content_bytes)
    
    # Detect MIME type from extension
    mime_type_from_extension, _ = mimetypes.guess_type(f"file{extension}")
    if not mime_type_from_extension:
        # Default MIME types for common script extensions
        mime_type_map = {
            '.py': 'text/x-python',
            '.js': 'application/javascript',
            '.ts': 'application/typescript',
            '.sh': 'application/x-sh',
            '.bash': 'application/x-sh',
            '.zsh': 'application/x-sh',
            '.ps1': 'application/x-powershell',
            '.rb': 'text/x-ruby',
            '.php': 'text/x-php',
            '.go': 'text/x-go',
            '.java': 'text/x-java-source',
            '.cpp': 'text/x-c++src',
            '.c': 'text/x-csrc',
        }
        mime_type_from_extension = mime_type_map.get(extension_lower, 'text/plain')
    
    mime_type = mime_type_from_extension
    
    # Validate MIME type against configuration (if configured)
    allowed_script_mime_types_list = ConfigurationHandler.get_list("GLOBAL SCRIPTS", "allowed_script_mime_types", fallback=[])
    if allowed_script_mime_types_list:
        allowed_script_mime_types = {mime.strip().lower() for mime in allowed_script_mime_types_list}
        if mime_type.lower() not in allowed_script_mime_types:
            raise InvalidInputError(
                field_name="extension",
                message=f"Script MIME type not allowed: {mime_type}. Allowed MIME types: {', '.join(allowed_script_mime_types)}"
            )
    
    # Sanitize script name
    sanitized_script_name = sanitize_filename(script_name)
    
    # Build filename with extension
    filename = f"{sanitized_script_name}{extension}"
    
    # Ensure filename length is within limit
    if len(filename) > MAX_FILENAME_LENGTH:
        # Truncate filename while preserving extension
        name_part = sanitized_script_name
        max_name_length = MAX_FILENAME_LENGTH - len(extension)
        if max_name_length > 0:
            truncated_name = name_part[:max_name_length] + extension
            filename = truncated_name
        else:
            raise InvalidInputError(
                field_name="script_name",
                message=f"Filename too long (max {MAX_FILENAME_LENGTH} characters)"
            )
    
    # Get global script path (not workspace-specific)
    global_script_path = get_global_script_path()
    ensure_directory(global_script_path)
    
    # Add category and subcategory to path if provided
    if category:
        safe_category = sanitize_filename(category)
        global_script_path = os.path.join(global_script_path, safe_category)
        ensure_directory(global_script_path)
        if subcategory:
            safe_subcategory = sanitize_filename(subcategory)
            global_script_path = os.path.join(global_script_path, safe_subcategory)
            ensure_directory(global_script_path)
    
    # Build full file path
    file_path_obj = Path(global_script_path) / filename
    
    # Check for symlinks BEFORE resolve
    _check_symlink(file_path_obj)
    
    resolved_path = file_path_obj.resolve()
    base_resolved = Path(global_script_path).resolve()
    
    # Path traversal check
    try:
        resolved_path.relative_to(base_resolved)
    except ValueError:
        raise InvalidInputError(
            field_name="script_name",
            message="Path traversal attempt detected"
        )
    
    final_path_str = str(resolved_path)
    
    # Atomic file write (TOCTOU protection)
    temp_file_path = final_path_str + '.tmp'
    
    try:
        # Write to temporary file
        with open(temp_file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Set secure file permissions (owner read/write only)
        try:
            os.chmod(temp_file_path, 0o600)
        except (OSError, PermissionError):
            # Continue - some filesystems don't support chmod
            pass
        
        # Atomic rename (TOCTOU protection)
        try:
            os.rename(temp_file_path, final_path_str)
        except (OSError, PermissionError):
            # Fallback for network filesystems
            try:
                shutil.copy2(temp_file_path, final_path_str)
                os.remove(temp_file_path)
            except Exception as fallback_error:
                # Cleanup on fallback failure
                try:
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                except Exception:
                    pass
                raise fallback_error
        
    except OSError as e:
        # Handle quota limits
        error_code = getattr(e, 'errno', None)
        if error_code == 28:  # ENOSPC - No space left on device
            raise InvalidInputError(
                field_name="file_path",
                message="Disk quota exceeded or no space left on device"
            )
        elif error_code == 122:  # EDQUOT - Disk quota exceeded
            raise InvalidInputError(
                field_name="file_path",
                message="Disk quota exceeded"
            )
        else:
            raise InvalidInputError(
                field_name="file_path",
                message=f"File system error: {str(e)}"
            )
    except Exception as e:
        # Cleanup temporary file
        try:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        except Exception:
            pass
        
        raise InvalidInputError(
            field_name="file_path",
            message=f"File could not be saved: {str(e)}"
        )
    
    return {
        "file_path": final_path_str,
        "file_size": content_size,
        "mime_type": mime_type,
        "extension": extension_lower,
        "file_name": filename
    }