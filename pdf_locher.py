import sys
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
import io
import os
from pdf2image import convert_from_path
import numpy as np

# Konstante für Umrechnungen
MM_TO_POINTS = 2.83465  # Umrechnungsfaktor von mm nach Punkten

# Funktion zum Erstellen von Löchern
def create_holes(input_pdf, output_pdf):
    hole_diameter = 6  # Durchmesser der Löcher in mm
    hole_radius = hole_diameter / 2  # Radius in mm
    hole_distance = 80  # Abstand zwischen den Mittelpunkten in mm
    offset_from_edge = 12  # Abstand von Blattrand in mm

    min_page_height = hole_distance + 2 * offset_from_edge

    # Umwandeln in Punkte
    hole_radius_points = hole_radius * MM_TO_POINTS
    hole_distance_points = hole_distance * MM_TO_POINTS
    offset_from_edge_points = offset_from_edge * MM_TO_POINTS
    min_page_height_points = min_page_height * MM_TO_POINTS

    # Lese die ursprüngliche PDF-Datei
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    # Gehe durch jede Seite
    for page_num in range(len(reader.pages)):
        print(f" {int((page_num+1)/len(reader.pages)*100)}%", end="\r")
        page = reader.pages[page_num]

        # Hole die Größe der Seite
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        
        # Erzeuge ein neues temporäres PDF zum Hinzufügen von Löchern
        packet = io.BytesIO()
        can = canvas.Canvas(packet)
        can.setPageSize((width, height))
        can.drawString(0, 0, "")

        if height < min_page_height_points:
            print(f"Fehler: Seite zu klein für den Locher. Drehen Sie die Seite und versuchen Sie es erneut")
        else:
            # Berechne die Y-Positionen für die Löcher
            y_top = height / 2 + hole_distance_points / 2
            y_bottom = height / 2 - hole_distance_points / 2
        
            # Konvertiere die Seite zu einem Bild
            dpi = 200
            images = convert_from_path(input_pdf, first_page=page_num + 1, last_page=page_num + 1, dpi=dpi)
            img = images[0]
            img_array = np.array(img)

            adj_dpi = dpi/72

            # Definiere die Region und stelle sicher, dass die Indizes innerhalb der Grenzen liegen
            y_start = int(adj_dpi * max(0, int(y_top - hole_radius_points - 1 * MM_TO_POINTS)))
            y_end = int(adj_dpi * min(height, int(y_top + hole_radius_points + 1 * MM_TO_POINTS)))
            x_start = int(adj_dpi * max(0, int(offset_from_edge_points - hole_radius_points - 1 * MM_TO_POINTS)))
            x_end = int(adj_dpi * min(width, int(offset_from_edge_points + hole_radius_points + 1 * MM_TO_POINTS)))

            bg_top = img_array[y_start:y_end, x_start:x_end]

            # Extrahiere die Region und berechne die durchschnittliche Farbe
            # switcheruuu
            avg_color_bottom = np.mean(bg_top, axis=(0, 1))

            # Definiere die Region für den unteren Teil und stelle sicher, dass die Indizes innerhalb der Grenzen liegen
            y_start_bottom = int(adj_dpi * max(0, int(y_bottom - hole_radius_points - 1 * MM_TO_POINTS)))
            y_end_bottom = int(adj_dpi * min(height, int(y_bottom + hole_radius_points + 1 * MM_TO_POINTS)))
            x_start_bottom = int(adj_dpi * max(0, int(offset_from_edge_points - hole_radius_points - 1 * MM_TO_POINTS)))
            x_end_bottom = int(adj_dpi * min(width, int(offset_from_edge_points + hole_radius_points + 1 * MM_TO_POINTS)))

            bg_bottom = img_array[y_start_bottom:y_end_bottom, x_start_bottom:x_end_bottom]

            # Extrahiere die Region für den unteren Teil und berechne die durchschnittliche Farbe
            # switcheruuu
            avg_color_top = np.mean(bg_bottom, axis=(0, 1))

            # Bestimme, ob der Hintergrund vorwiegend schwarz oder weiß ist
            if avg_color_top.mean() < 128:
                fill_color_top = 'white'
                outline_color_top = 'black'
            else:
                fill_color_top = 'black'
                outline_color_top = 'white'

            # Bestimme, ob der Hintergrund vorwiegend schwarz oder weiß ist
            if avg_color_bottom.mean() < 128:
                fill_color_bottom = 'white'
                outline_color_bottom = 'black'
            else:
                fill_color_bottom = 'black'
                outline_color_bottom = 'white'


            # Zeichne die Kreise (Löcher) mit der entsprechenden Farbe
            can.setStrokeColor(outline_color_top)
            can.setFillColor(fill_color_top)

            can.circle(offset_from_edge_points, y_top, hole_radius_points + 1, stroke=1, fill=0)  # Umrandung
            can.circle(offset_from_edge_points, y_top, hole_radius_points, stroke=0, fill=1)  # Loch

            can.setStrokeColor(outline_color_bottom)
            can.setFillColor(fill_color_bottom)

            can.circle(offset_from_edge_points, y_bottom, hole_radius_points + 1, stroke=1, fill=0)  # Umrandung
            can.circle(offset_from_edge_points, y_bottom, hole_radius_points, stroke=0, fill=1)  # Loch

        can.save()

        # Kombiniere das ursprüngliche PDF mit dem temporären
        packet.seek(0)
        overlay_pdf = PdfReader(packet)
        overlay_page = overlay_pdf.pages[0]

        # Kombiniere die Seiten
        page.merge_page(overlay_page)

        # Füge die bearbeitete Seite zum Writer hinzu
        writer.add_page(page)

    # Schreibe die neue PDF-Datei
    with open(output_pdf, "wb") as output_file:
        writer.write(output_file)

def main():
    if len(sys.argv) < 2:
        print("Usage: python pdf_locher.py <input.pdf> [-o <output.pdf>]")
        print("Usage: pdf-locher <input.pdf> [-o <output.pdf>]")
        sys.exit(1)

    input_pdf = sys.argv[1]
    output_pdf = f"{os.path.splitext(input_pdf)[0]}_gelocht.pdf"  # Standard-Ausgabenamen

    # Überprüfe auf zusätzliches Argument -o für den Ausgabedateinamen
    if '-o' in sys.argv:
        try:
            output_index = sys.argv.index('-o') + 1
            output_pdf = sys.argv[output_index]
        except IndexError:
            print("Fehler: Kein Ausgabedateiname nach -o angegeben.")
            sys.exit(1)

    # Stelle sicher, dass die Eingabedatei existiert
    if not os.path.isfile(input_pdf):
        print(f"Fehler: Die Datei '{input_pdf}' existiert nicht.")
        sys.exit(1)

    # Rufe die Funktion auf
    create_holes(input_pdf, output_pdf)
    print(f"'{input_pdf}' wurde gelocht und in '{output_pdf}' gespeichert.")
    if '-k' not in sys.argv:
        os.remove(input_pdf)

if __name__ == "__main__":
    main()