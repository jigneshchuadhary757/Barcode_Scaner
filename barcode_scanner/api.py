import barcode
from barcode.writer import ImageWriter
from io import BytesIO
import base64
from reportlab.lib.pagesizes import mm
from reportlab.pdfgen import canvas
from PIL import Image
from frappe import _
import frappe
import os

@frappe.whitelist()
def generate_barcodes_for_purchase_receipt(purchase_receipt, barcode_setting):
    try:
        # Fetch the settings
        settings = frappe.get_doc('Barcode Settings', barcode_setting)
        page_width = settings.page_width * mm
        page_height = settings.page_height * mm
        barcode_width = settings.barcode_width * mm
        barcode_height = settings.barcode_height * mm

        # Fetch the purchase receipt
        pr = frappe.get_doc('Purchase Receipt', purchase_receipt)
        
        # Buffer for the PDF
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=(page_width, page_height))

        # Function to generate a barcode and draw it on the canvas
        def generate_and_draw_barcode(code, index):
            barcode_io = generate_item_barcode(code)
            barcode_io.seek(0)
            pil_image = Image.open(barcode_io)

            # Calculate starting x and y positions for centering
            x_center = (page_width - barcode_width) / 2
            y_center = (page_height - barcode_height) / 2

            # Save the image temporarily to a file
            image_path = f"/tmp/barcode_{index}.png"
            pil_image.save(image_path, format='PNG')

            c.drawImage(image_path, x_center, y_center, width=barcode_width, height=barcode_height)

            if (index + 1) % (page_width // barcode_width) == 0:
                c.showPage()

        # Iterate through items in the purchase receipt
        barcode_index = 0
        for item in pr.items:
            if item.serial_and_batch_bundle:
                bundle_doc = frappe.get_doc("Serial and Batch Bundle", item.serial_and_batch_bundle)
                for row in bundle_doc.entries:
                    if row.batch_no:
                        generate_and_draw_barcode(row.batch_no, barcode_index)
                        barcode_index += 1
                    if row.serial_no:
                        generate_and_draw_barcode(row.serial_no, barcode_index)
                        barcode_index += 1
            if item.batch_no:
                generate_and_draw_barcode(item.batch_no, barcode_index)
                barcode_index += 1
            if item.serial_no:
                serial_numbers = item.serial_no.split('\n')
                for serial in serial_numbers:
                    generate_and_draw_barcode(serial, barcode_index)
                    barcode_index += 1

        # Finalize the PDF
        c.save()
        buffer.seek(0)
        pdf_base64 = base64.b64encode(buffer.read()).decode('utf-8')

        # Clean up the temporary files
        for i in range(barcode_index):
            image_path = f"/tmp/barcode_{i}.png"
            if os.path.exists(image_path):
                os.remove(image_path)

        return {
            'pdf_base64': pdf_base64,
            'print_instruction': 'Print the generated PDF to obtain the barcodes.'
        }

    except Exception as e:
        frappe.log_error(f'Unexpected error: {str(e)}', 'Barcode Generation Error')
        frappe.throw(_('Error generating and printing barcodes: {0}').format(e))

def generate_item_barcode(code):
    barcode_class = barcode.get_barcode_class('code128')
    barcode_instance = barcode_class(code, writer=ImageWriter())

    barcode_io = BytesIO()
    barcode_instance.write(barcode_io)
    barcode_io.seek(0)

    return barcode_io