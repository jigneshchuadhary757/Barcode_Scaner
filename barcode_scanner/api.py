from barcode.writer import ImageWriter
from io import BytesIO
from barcode import get_barcode_class
import base64
import frappe
from frappe import _
import random
import string
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from PIL import Image

@frappe.whitelist()
def generate_and_print_barcodes(item_code, quantity):
    try:
        quantity = int(quantity)
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        # Starting positions for the barcodes
        x, y = 45, 780
    
        for i in range(quantity):
            custom_barcode = generate_custom_barcode_code(item_code)
            barcode_img = generate_item_barcode(custom_barcode)
            pil_image = Image.open(barcode_img)
            image_path = "/tmp/barcode_{}.png".format(i)
            pil_image.save(image_path)

            c.drawImage(image_path, x, y, width=200, height=50)
            y -= 105  # Move down for the next barcode

        c.save()
        buffer.seek(0)
        pdf_base64 = base64.b64encode(buffer.read()).decode('utf-8')

        return {
            'pdf_base64': pdf_base64,
            'print_instruction': 'Print the generated PDF to obtain the barcodes.'
        }

    except Exception as e:
        frappe.log_error(f'Unexpected error: {str(e)}', 'Barcode Generation Error')
        frappe.throw(_('Error generating and printing barcodes: {0}').format(e))

def generate_item_barcode(custom_barcode):
    barcode_class = get_barcode_class('ean13')
    barcode_instance = barcode_class(custom_barcode, writer=ImageWriter())

    barcode_io = BytesIO()
    barcode_instance.write(barcode_io)
    barcode_io.seek(0)

    return barcode_io

def generate_custom_barcode_code(item_code):
    random_number = ''.join(random.choices(string.digits, k=12))
    custom_barcode_code = (item_code[:1] + random_number)[:13]
    return custom_barcode_code
