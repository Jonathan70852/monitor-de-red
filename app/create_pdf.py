# Programa de Python para crear archivo PDF

from fpdf import FPDF
 
TABLE_COL_NAMES = ("FECHA", "HORA", "MÁQUINA", "NIVEL", "IP", "MENSAJE")

def render_table_header(pdf):
    pdf.set_font("Arial", size=8)
    line_height = pdf.font_size * 2
    pdf.set_font(style="B")  # enabling bold text
    for col_name in TABLE_COL_NAMES:
        if col_name == "MENSAJE":
            pdf.cell(pdf.epw / 2, line_height, col_name, border=1)
        else:
            if col_name == "IP":
                pdf.cell(pdf.epw / 7, line_height, col_name, border=1)
            else:
                if col_name == "NIVEL":
                    pdf.cell(pdf.epw / 12, line_height, col_name, border=1)
                else:
                    pdf.cell(pdf.epw / 12, line_height, col_name, border=1)

    pdf.ln(line_height)
    pdf.set_font(style="")  # disabling bold text
    return pdf
    
def create_pdf(values):
    # guarda FPDF() class dentro de
    # una variable pdf
    pdf = FPDF()
 
    # Agregar página
    pdf.add_page()
 
    # Configurar estilo y tamaño de la fuente
    # que se quiere en el PDF
    pdf.set_font("Arial", "B",size = 25)
 
    # crear una celda 
    pdf.cell(0, 10, txt = "Net-Cube", ln = 1, align = 'C')

         # agreagar otra celda
    pdf.cell(5, 5, txt = "\n", ln = 2, align = 'C')

    pdf.image("C:/Users/Jonathan/Desktop/Flask final/app/static/img/Cubo.png", 93, w = 20, h = 20)
 
     # crear otra celda
    pdf.cell(100, 15, txt = "\n", ln = 2, align = 'C')

    pdf.set_font("Arial", "B", size = 20)
        # crear otra celda
    pdf.cell(0, 10, txt = "INFORME DE ALARMAS", ln = 2, align = 'C')

    pdf = render_table_header(pdf)

    line_height = pdf.font_size * 2
    col_width = pdf.epw / 7  # distribute content evenly

    for row in values:
        if pdf.will_page_break(line_height):
            pdf = render_table_header(pdf)
        i = 0
        pdf.set_font("Arial", size = 8)
        for datum in row:
            if i == 5:
                pdf.set_font("Arial", size=8)
                pdf.cell(pdf.epw / 2 , line_height, str(datum), border=1)
            else:
                if i == 4:
                    pdf.cell(pdf.epw / 7 , line_height, str(datum), border=1)
                else:
                    if i == 3:
                        pdf.cell(pdf.epw / 12 , line_height, str(datum), border=1)
                    else:
                        pdf.cell(pdf.epw / 12 , line_height, str(datum), border=1)
            i += 1
        pdf.ln(line_height)


    # crear otra celda
    pdf.cell(100, 13, txt = "\n", ln = 2, align = 'C')

    pdf.set_font("Arial", size = 11)

    # crear otra celda
    pdf.cell(0, 10, txt = "**Tomar las acciones correspondientes respecto a las condiciones de riesgo advertidas", ln = 2, align = 'L')

    # crear otra celda
    pdf.cell(500, 20, txt = "\n", ln = 2, align = 'C')

    pdf.set_font("Arial", size = 8)

    # crear otra celda
    pdf.cell(0, 10, txt = "© Net-Cube 2022. Todos los derechos reservados.", ln = 2, align = 'C')
 
 
    return pdf

