import base64
import io
from pathlib import Path
from typing import Optional


class OCRService:
    def __init__(self):
        self._vision_model = "llava:7b"
        self._fallback_model = "llama3.2"

    async def ocr_image(self, image_b64: str, prompt: str = None, language: str = "english") -> dict:
        import ollama
        
        if not prompt:
            prompt = (
                f"Extract ALL text from this image. "
                f"Output only the text, preserving the original layout and formatting as much as possible. "
                f"Language: {language}. "
                f"Do not describe the image. Do not add commentary. Just output the text you see."
            )

        try:
            response = ollama.chat(
                model=self._vision_model,
                messages=[{
                    "role": "user",
                    "content": prompt,
                    "images": [image_b64],
                }],
                options={"temperature": 0.0, "num_predict": 2000},
            )
            extracted_text = response["message"]["content"].strip()
            return {
                "status": "success",
                "text": extracted_text,
                "model": self._vision_model,
                "language": language,
            }
        except Exception as e:
            print(f"[OCR] Vision model error: {e}")
            return {"status": "error", "message": str(e)}

    async def ocr_from_url(self, image_url: str, prompt: str = None) -> dict:
        import httpx
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(image_url)
                response.raise_for_status()
                image_bytes = response.content
        except Exception as e:
            return {"status": "error", "message": f"Failed to download image: {str(e)}"}
        
        image_b64 = base64.b64encode(image_bytes).decode()
        return await self.ocr_image(image_b64, prompt=prompt)

    async def ocr_from_file(self, file_path: str, prompt: str = None) -> dict:
        path = Path(file_path)
        if not path.exists():
            return {"status": "error", "message": f"File not found: {file_path}"}
        
        try:
            image_bytes = path.read_bytes()
            image_b64 = base64.b64encode(image_bytes).decode()
            return await self.ocr_image(image_b64, prompt=prompt)
        except Exception as e:
            return {"status": "error", "message": f"Failed to read file: {str(e)}"}

    async def ocr_screenshot(self, prompt: str = None) -> dict:
        try:
            import subprocess
            import tempfile
            import os
            
            temp_path = os.path.join(tempfile.gettempdir(), "jarvis_screenshot.png")
            
            result = subprocess.run([
                "powershell", "-Command",
                "Add-Type -AssemblyName System.Windows.Forms;"
                "[System.Windows.Forms.Screen]::PrimaryScreen | ForEach-Object {"
                "  $bounds = $_.Bounds;"
                "  $bmp = New-Object System.Drawing.Bitmap($bounds.Width, $bounds.Height);"
                "  $graphics = [System.Drawing.Graphics]::FromImage($bmp);"
                "  $graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size);"
                f"  $bmp.Save('{temp_path}');"
                "  $graphics.Dispose(); $bmp.Dispose();"
                "}"
            ], capture_output=True, timeout=10)
            
            if not os.path.exists(temp_path):
                return {"status": "error", "message": "Failed to capture screenshot"}
            
            image_bytes = Path(temp_path).read_bytes()
            image_b64 = base64.b64encode(image_bytes).decode()
            
            os.remove(temp_path)
            
            if not prompt:
                prompt = (
                    "This is a screenshot. Extract ALL visible text from this screenshot. "
                    "Output only the text, preserving layout. "
                    "Include UI elements, menus, buttons, text content, titles, and any other visible text. "
                    "Do not describe the image. Just output the text."
                )
            
            return await self.ocr_image(image_b64, prompt=prompt)
        except Exception as e:
            return {"status": "error", "message": f"Screenshot capture failed: {str(e)}"}

    async def analyze_image(self, image_b64: str, question: str) -> dict:
        import ollama
        
        try:
            response = ollama.chat(
                model=self._vision_model,
                messages=[{
                    "role": "user",
                    "content": question,
                    "images": [image_b64],
                }],
                options={"temperature": 0.3, "num_predict": 1000},
            )
            return {
                "status": "success",
                "answer": response["message"]["content"].strip(),
                "model": self._vision_model,
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def translate_text(self, image_b64: str, target_language: str = "english") -> dict:
        prompt = (
            f"Extract all text from this image and translate it to {target_language}. "
            f"Output format:\n[Original text]\n{translated_text}\n\n"
            f"Show the original text first, then the translation."
        )
        return await self.ocr_image(image_b64, prompt=prompt)

    async def describe_and_read(self, image_b64: str) -> dict:
        import ollama
        
        prompt = (
            "Describe this image briefly (1-2 sentences), then extract ALL visible text. "
            "Format:\n[Description]\n...\n\n[Text]\n..."
        )
        
        try:
            response = ollama.chat(
                model=self._vision_model,
                messages=[{
                    "role": "user",
                    "content": prompt,
                    "images": [image_b64],
                }],
                options={"temperature": 0.2, "num_predict": 2000},
            )
            return {
                "status": "success",
                "result": response["message"]["content"].strip(),
                "model": self._vision_model,
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}


ocr_service = OCRService()
