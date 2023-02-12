import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import mysql.connector


#The mail addresses and password
def send_email(values):
    #sender_address = 'daniel.alejandro0113@gmail.com'
    #sender_pass = 'hrffzzbtezjrsvxl'
    mail_content = "Notificación del Servidor\n\nEstimado Administrador,\n\nEl sistema ha detectado una posible situación de emergencia, e implica su monitoreo riguroso de las condiciones de riesgo advertidas.\n\nA continuación se enlista el detalle de la alerta:\n\n"
    conn=mysql.connector.connect(host="localhost", user="root", password="", db="net_cube")           
    cur = conn.cursor()
    cur.execute("SELECT EMAIL_RECEIVER, EMAIL_SENDER, PASSWORD_SENDER FROM configuracion")
    data=cur.fetchall()
    conn.close()
    receiver_address = data[0][0]
    sender_address = data[0][1]
    sender_pass = data[0][2]
    #Setup the MIME
    message = MIMEMultipart()
    message['From'] = sender_address
    message['To'] = receiver_address
    message['Subject'] = 'Alerta automatica Net-Cube'   #The subject line
    #The body and the attachments for the mail
    string_format = "FECHA: {0}\nHORA: {1}\nMAQUINA: {2}\nNIVEL: {3}\nIP: {4}\nTIPO DE ALERTA: {5}\nMENSAJE: {6}\n"
    mail_content += string_format.format(*values)
    message.attach(MIMEText(mail_content, 'plain'))
    #Create SMTP session for sending the mail
    session = smtplib.SMTP('smtp.gmail.com', 587) #use gmail with port
    session.starttls() #enable security
    session.login(sender_address, sender_pass) #login with mail_id and password
    text = message.as_string()
    session.sendmail(sender_address, receiver_address, text)
    session.quit()
    print('Mail Sent')
