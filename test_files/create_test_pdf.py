from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
import arabic_reshaper
from bidi.algorithm import get_display
import os

# Register a font that supports Arabic
FONT_PATH = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"  # Common path on macOS
pdfmetrics.registerFont(TTFont('ArialUnicode', FONT_PATH))

def create_pdf_with_arabic(input_txt, output_pdf):
    # Create PDF
    c = canvas.Canvas(output_pdf, pagesize=A4)
    c.setFont('ArialUnicode', 14)
    
    # Read the text file
    with open(input_txt, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Split into lines
    lines = text.split('\n')
    
    # Start position
    y = 800  # Start from top of page
    
    for line in lines:
        if line.strip():
            # Reshape Arabic text and apply BIDI
            reshaped_text = arabic_reshaper.reshape(line)
            bidi_text = get_display(reshaped_text)
            
            # Write the line
            c.drawString(50, y, bidi_text)
            y -= 20  # Move down for next line
    
    c.save()

if __name__ == "__main__":
    # Create test_files directory if it doesn't exist
    os.makedirs("test_files", exist_ok=True)
    
    input_file = "test_files/arabic_test.txt"
    output_file = "test_files/arabic_test.pdf"
    
    create_pdf_with_arabic(input_file, output_file)
    print(f"PDF created: {output_file}") 