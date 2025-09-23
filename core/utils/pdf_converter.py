import os
import platform
import subprocess
from typing import Optional

def convert_docx_to_pdf(docx_path: str, pdf_path: str) -> bool:
    """
    Convert DOCX to PDF with cross-platform compatibility.
    
    Args:
        docx_path: Path to input DOCX file
        pdf_path: Path to output PDF file
        
    Returns:
        bool: True if conversion successful, False otherwise
    """
    try:
        system = platform.system().lower()
        
        if system == "darwin":  # macOS
            return _convert_macos(docx_path, pdf_path)
        elif system == "linux":
            return _convert_linux(docx_path, pdf_path)
        elif system == "windows":
            return _convert_windows(docx_path, pdf_path)
        else:
            print(f"Unsupported platform: {system}")
            return False
            
    except Exception as e:
        print(f"PDF conversion failed: {e}")
        return False

def _convert_macos(docx_path: str, pdf_path: str) -> bool:
    """Convert on macOS using multiple fallback methods"""
    
    # Method 1: Try LibreOffice if available
    if _check_command("libreoffice"):
        try:
            cmd = [
                "libreoffice", "--headless", "--convert-to", "pdf",
                "--outdir", os.path.dirname(pdf_path), docx_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            # LibreOffice creates PDF with same name as DOCX
            generated_pdf = os.path.join(
                os.path.dirname(pdf_path),
                os.path.splitext(os.path.basename(docx_path))[0] + ".pdf"
            )
            
            if os.path.exists(generated_pdf):
                if generated_pdf != pdf_path:
                    os.rename(generated_pdf, pdf_path)
                return True
        except Exception as e:
            print(f"LibreOffice conversion failed: {e}")
    
    # Method 2: Try pandoc if available
    if _check_command("pandoc"):
        try:
            cmd = ["pandoc", docx_path, "-o", pdf_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0 and os.path.exists(pdf_path):
                return True
        except Exception as e:
            print(f"Pandoc conversion failed: {e}")
    
    # Method 3: Try textutil (macOS built-in) - converts to RTF first, then PDF
    try:
        rtf_path = pdf_path.replace('.pdf', '.rtf')
        
        # Convert DOCX to RTF
        cmd1 = ["textutil", "-convert", "rtf", docx_path, "-output", rtf_path]
        result1 = subprocess.run(cmd1, capture_output=True, text=True, timeout=30)
        
        if result1.returncode == 0 and os.path.exists(rtf_path):
            # Convert RTF to PDF
            cmd2 = ["textutil", "-convert", "pdf", rtf_path, "-output", pdf_path]
            result2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=30)
            
            # Clean up RTF file
            if os.path.exists(rtf_path):
                os.remove(rtf_path)
            
            if result2.returncode == 0 and os.path.exists(pdf_path):
                return True
    except Exception as e:
        print(f"textutil conversion failed: {e}")
    
    print("All macOS conversion methods failed. Consider installing LibreOffice.")
    return False

def _convert_linux(docx_path: str, pdf_path: str) -> bool:
    """Convert on Linux using LibreOffice"""
    
    if not _check_command("libreoffice"):
        print("LibreOffice not found. Install with: sudo apt-get install libreoffice")
        return False
    
    try:
        cmd = [
            "libreoffice", "--headless", "--convert-to", "pdf",
            "--outdir", os.path.dirname(pdf_path), docx_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        # LibreOffice creates PDF with same name as DOCX
        generated_pdf = os.path.join(
            os.path.dirname(pdf_path),
            os.path.splitext(os.path.basename(docx_path))[0] + ".pdf"
        )
        
        if os.path.exists(generated_pdf):
            if generated_pdf != pdf_path:
                os.rename(generated_pdf, pdf_path)
            return True
            
    except Exception as e:
        print(f"LibreOffice conversion failed: {e}")
    
    return False

def _convert_windows(docx_path: str, pdf_path: str) -> bool:
    """Convert on Windows using multiple methods"""
    
    # Method 1: Try LibreOffice
    if _check_command("libreoffice"):
        try:
            cmd = [
                "libreoffice", "--headless", "--convert-to", "pdf",
                "--outdir", os.path.dirname(pdf_path), docx_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            generated_pdf = os.path.join(
                os.path.dirname(pdf_path),
                os.path.splitext(os.path.basename(docx_path))[0] + ".pdf"
            )
            
            if os.path.exists(generated_pdf):
                if generated_pdf != pdf_path:
                    os.rename(generated_pdf, pdf_path)
                return True
        except Exception as e:
            print(f"LibreOffice conversion failed: {e}")
    
    # Method 2: Try using COM automation (Windows only)
    try:
        import win32com.client
        
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        
        doc = word.Documents.Open(os.path.abspath(docx_path))
        doc.SaveAs(os.path.abspath(pdf_path), FileFormat=17)  # 17 = PDF format
        doc.Close()
        word.Quit()
        
        return os.path.exists(pdf_path)
        
    except ImportError:
        print("pywin32 not available for COM automation")
    except Exception as e:
        print(f"COM automation failed: {e}")
    
    return False

def _check_command(command: str) -> bool:
    """Check if a command is available in PATH"""
    try:
        subprocess.run([command, "--version"], capture_output=True, timeout=5)
        return True
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        return False

def get_conversion_info() -> dict:
    """Get information about available conversion methods"""
    system = platform.system().lower()
    info = {
        "platform": system,
        "available_converters": []
    }
    
    if _check_command("libreoffice"):
        info["available_converters"].append("LibreOffice")
    
    if _check_command("pandoc"):
        info["available_converters"].append("Pandoc")
    
    if system == "darwin" and _check_command("textutil"):
        info["available_converters"].append("textutil (macOS)")
    
    if system == "windows":
        try:
            import win32com.client
            info["available_converters"].append("Microsoft Word COM")
        except ImportError:
            pass
    
    return info