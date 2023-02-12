
from flask import Flask, request, render_template, make_response, redirect, flash, session 
from flask_mysqldb import MySQL
from lib.livehost import arp_scan
from lib.snmp import create_list, snmp_device_scan
from send_emails import send_email
from create_pdf import create_pdf
from datetime import datetime
from alerts_thread import RepeatTimer
from flask_wtf import FlaskForm
from wtforms.fields import DateField
from wtforms.validators import DataRequired
from wtforms import validators, SubmitField

app = Flask(__name__)

#Conexión a MySQL
app.config['MYSQL_HOST'] = 'localhost'
#app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'net_cube'

conexion = MySQL(app)

hardDisk_alert = ""
wifi_alert = ""
ethernet_alert = ""
disconnect_alert = ""
alarmas = []


"""
Clave secreta. Esta debe ser aleatoria.
Entrarás a la CLI de Python, ahí ejecuta:
import os; print(os.urandom(16));
Eso te dará algo como:
b'\x11\xad\xec\t\x99\x8f\xfa\x86\xe8A\xd9\x1a\xf6\x12Z\xf4'
Simplemente remplaza la clave que se ve a continuación con los bytes aleatorios que generaste
"""

app.secret_key = b'\xa3w5y\x1dL|\xd3oy\x8ew\xd3D\xe9\xc8'

class InfoForm(FlaskForm):
    startdate = DateField('Fecha de inicio', format='%Y-%m-%d')
    enddate = DateField('Fecha de fin', format='%Y-%m-%d')
    submit = SubmitField('Filtrar')

@app.route('/')
def login():
    return render_template('Login.html')


@app.route("/hacer_login", methods=["POST"])
def hacer_login():
    correo = request.form["correo"]
    palabra_secreta = request.form["palabra_secreta"]

    cur = conexion.connection.cursor()
    query = "SELECT PASSWORD FROM usuarios WHERE EMAIL ='" + correo + "'"
    cur.execute(query)
    user = cur.fetchall()

    if user:
        password = user[0][0]
        if palabra_secreta == password:
            # Si coincide, iniciamos sesión y además redireccionamos
            session["usuario"] = correo
            return redirect("/home")
        else:
             # Si NO coincide, lo regresamos
            flash("Correo o contraseña incorrectos")
            return redirect("/")

    else:
        # Si NO coincide, lo regresamos
        flash("Correo o contraseña incorrectos")
        return redirect("/")

# Cerrar sesión
@app.route("/logout")
def logout():
    session.pop("usuario", None)
    return redirect("/")

# Un "middleware" que se ejecuta antes de responder a cualquier ruta. Aquí verificamos si el usuario ha iniciado sesión
@app.before_request
def antes_de_cada_peticion():
    ruta = request.path
    # Si no ha iniciado sesión y no quiere ir a algo relacionado al login, lo redireccionamos al login
    if not 'usuario' in session and ruta != "/" and ruta != "/hacer_login" and ruta != "/logout" and not ruta.startswith("/static"):
        flash("Inicia sesión para continuar")
        return redirect("/")
    # Si ya ha iniciado, no hacemos nada, es decir lo dejamos pasar

@app.route('/home')
def Home():
    if session["usuario"]:
        return render_template('home.html')
    else:
        return redirect("/")

@app.route('/empezar')
def Empezar():
    if session["usuario"]:
        return render_template('empezar.html')
    else:
        return redirect("/")


@app.route('/inicio',methods = ['POST', 'GET'])
def Inicio():
    if session["usuario"]:
        if request.method == 'POST':
            form_data = request.form
            fecha_inicio = form_data.getlist('startdate')[0]
            fecha_fin = form_data.getlist('enddate')[0]
        else:
            print("get")
            if request.method == 'GET':
                fecha_inicio = ""
                fecha_fin = ""
        
        if request.method == 'POST' or request.method == 'GET':
            form = InfoForm()
            # Definir datos del primer grafico - Total de alarmas por tipo
            labels_g1= [
            'Desconexión',
            'Wifi',
            'Ethernet',
            'HDD',
            ]
            cur = conexion.connection.cursor()
            disconnection_count_query = "SELECT COUNT(*) AS DISCONNECTION FROM alertas WHERE TIPO_ALERTA = 'Desconexión de equipo'" + ((" AND FECHA <= '" + fecha_fin + "' AND FECHA >= '" + fecha_inicio + "'") if (fecha_inicio != "" and fecha_fin != "") else "")
            cur.execute(disconnection_count_query)
            disconnection_count=cur.fetchall()
            wifi_count_query = "SELECT COUNT(*) AS WIFI FROM alertas WHERE TIPO_ALERTA = 'Velocidad Wifi'"  + ((" AND FECHA <= '" + fecha_fin + "' AND FECHA >= '" + fecha_inicio + "'") if (fecha_inicio != "" and fecha_fin != "") else "")
            cur.execute(wifi_count_query)
            wifi_count=cur.fetchall()
            ethernet_count_query = "SELECT COUNT(*) AS ETHERNET FROM alertas WHERE TIPO_ALERTA = 'Velocidad Ethernet'"  + ((" AND FECHA <= '" + fecha_fin + "' AND FECHA >= '" + fecha_inicio + "'") if (fecha_inicio != "" and fecha_fin != "") else "")
            cur.execute(ethernet_count_query)
            ethernet_count=cur.fetchall()
            hdd_count_query = "SELECT COUNT(*) AS HDD FROM alertas WHERE TIPO_ALERTA = 'Espacio en disco HDD'"  + ((" AND FECHA <= '" + fecha_fin + "' AND FECHA >= '" + fecha_inicio + "'") if (fecha_inicio != "" and fecha_fin != "") else "")
            cur.execute(hdd_count_query)
            hdd_count=cur.fetchall()
            data_g1 = [disconnection_count[0][0], wifi_count[0][0], ethernet_count[0][0], hdd_count[0][0]]
            # Definir datos del segundo grafico - Total de alarmas por nivel
            labels_g2= [
            'Crítico',
            'Aviso',
            ]
            critico_count_query = "SELECT COUNT(*) AS CRITICO FROM alertas WHERE NIVEL = 'Crítico'"  + ((" AND FECHA <= '" + fecha_fin + "' AND FECHA >= '" + fecha_inicio + "'") if (fecha_inicio != "" and fecha_fin != "") else "")
            cur.execute(critico_count_query)
            critico_count=cur.fetchall()
            aviso_count_query = "SELECT COUNT(*) AS AVISO FROM alertas WHERE NIVEL = 'Aviso'"  + ((" AND FECHA <= '" + fecha_fin + "' AND FECHA >= '" + fecha_inicio + "'") if (fecha_inicio != "" and fecha_fin != "") else "")
            cur.execute(aviso_count_query)
            aviso_count=cur.fetchall()
            data_g2 = [critico_count[0][0], aviso_count[0][0]]

            # Definir datos del tercer grafico - Cantidad de alarmas por fecha
            critico_count_query = "SELECT FECHA, COUNT(FECHA) AS NUMERO FROM alertas "+ ((" WHERE FECHA <= '" + fecha_fin + "' AND FECHA >= '" + fecha_inicio + "'") if (fecha_inicio != "" and fecha_fin != "") else "") + " GROUP BY FECHA" 
            cur.execute(critico_count_query)

            data=cur.fetchall()
            labels_g3=[]
            data_g3=[]
            for row in data:
                labels_g3.append(str(row[0]))
                data_g3.append(row[1])
        
            return render_template('inicio.html',form = form, data_g1= data_g1,
            labels_g1=labels_g1, labels_g2=labels_g2,data_g2=data_g2,labels_g3=labels_g3,data_g3=data_g3)
    else:
        return redirect("/")


@app.route('/dispositivos')
def Dispositivos():
    if session["usuario"]:
        return render_template('dispositivos.html')
    else:
        return redirect("/")

@app.route('/alarmas')
def Alarmas():
    if session["usuario"]:
        form = InfoForm()
        cur = conexion.connection.cursor()
        query = "SELECT * FROM alertas"
        cur.execute(query)
        alertas=cur.fetchall()
        #print(alertas)
        alertas = alertas[::-1]
        #print(alertas)
        global alarmas
        alarmas = alertas
        return render_template('alarmas.html', alarmas = alertas, form = form, selected_option = "")
    else:
        return redirect("/")

@app.route('/filtrarAlarmas',methods = ['POST']) 
def FiltrarAlarmas():
    if session["usuario"]:
        if request.method == 'POST':
            form = InfoForm()
            form_data = request.form
            tipo_alarma = form_data.getlist('alertTypes')[0]
            selected_option = tipo_alarma

            if tipo_alarma == "disconnection_alert":
                tipo_alarma = "Desconexión de equipo"
            if tipo_alarma == "wifi_alert":
                tipo_alarma = "Velocidad Wifi"
            if tipo_alarma == "ethernet_alert":
                tipo_alarma = "Velocidad Ethernet"
            if tipo_alarma == "hardDisk_alert":
                tipo_alarma = "Espacio en disco HDD"

            fecha_inicio = form_data.getlist('startdate')[0]
            fecha_fin = form_data.getlist('enddate')[0]

            print("Valores filtro", tipo_alarma, fecha_inicio, fecha_fin)
            cur = conexion.connection.cursor()

            if tipo_alarma and not (fecha_inicio and fecha_fin):
                print("case1")
                query = "SELECT * FROM alertas WHERE TIPO_ALERTA= '" + tipo_alarma + "'"
            else:
                if fecha_inicio and fecha_fin:
                    if fecha_inicio and fecha_fin and tipo_alarma:
                        query = "SELECT * FROM alertas WHERE TIPO_ALERTA= '" + tipo_alarma + "' AND FECHA <= '" + fecha_fin + "' AND FECHA >= '" + fecha_inicio + "'"
                    else:
                        if fecha_inicio and fecha_fin and not tipo_alarma:
                            query = "SELECT * FROM alertas WHERE FECHA <= '" + fecha_fin + "' AND FECHA >= '" + fecha_inicio + "'"
                else:
                    query = "SELECT * FROM alertas"
                 
        cur.execute(query)
        alertas=cur.fetchall()
        #print(alertas)
        alertas = alertas[::-1]
        global alarmas
        alarmas = alertas
        #print(alertas)  
        return render_template('alarmas.html', alarmas = alertas, form = form, selected_option = selected_option)
    else:
        return redirect("/")

@app.route('/configuracion')
def Configuracion():
    if session["usuario"]:
        cur = conexion.connection.cursor()
        query = "SELECT * FROM configuracion"
        cur.execute(query)
        configuracion=cur.fetchall()
        return render_template('configuracion.html', configuracion = configuracion[0])
    else:
        return redirect("/")

@app.route('/descargarPDF') 
def DescargarPDF():
    if session["usuario"]:
        global alarmas
        values = []
        for alarma in alarmas:
            values.append(alarma[1:6] + (alarma[7],))
        print(values)
        pdf = create_pdf(values)
        response = make_response(pdf.output(dest='S'))
        dt = datetime.now().strftime("%Y-%m-%d")
        response.headers.set('Content-Disposition', 'attachment', filename='alerta_' + dt+ '.pdf')
        response.headers.set('Content-Type', 'application/pdf')
        return response
    else:
        return redirect("/")

@app.route('/informe/<id_dispositivo>') 
def Informes(id_dispositivo):
    if session["usuario"]:
        print("ID:"+id_dispositivo)
        cur = conexion.connection.cursor()
        query = "SELECT IP FROM dispositivos WHERE ID = " + id_dispositivo 
        cur.execute(query)
        us=cur.fetchall()
        informe = create_list(us[0][0])
        return render_template ('informe.html', us = informe)
    else:
        return redirect("/")

@app.route('/usuarios')
@app.route('/usuarios/<menuAgregarUsuario>')
@app.route('/usuarios/<usuario>/<menuAgregarUsuario>')
def VerUsuarios(usuario = None, menuAgregarUsuario = False):
    print(menuAgregarUsuario)
    print(usuario)
    if session["usuario"]:
        cur = conexion.connection.cursor()
        query = "SELECT * FROM usuarios"
        cur.execute(query)
        users=cur.fetchall()
        if usuario:
            usuario = usuario.replace(")","").replace("(","").replace("'","").split(",")
            print(usuario)
        return render_template ('usuarios.html', usuarios = users, menuAgregarUsuario = menuAgregarUsuario, usuario = usuario)
    else:
        return redirect("/")

@app.route('/agregarUsuario',methods = ['POST']) 
def AgregarUsuario():
    if session["usuario"]:
        if request.method == 'POST':
            form_data = request.form
            correo = form_data['correo']
            password = form_data['password']
            cur = conexion.connection.cursor()
            query = "SELECT * FROM usuarios"
            cur.execute(query)
            users=cur.fetchall()
            existUser = False
            for user in users:
                if user[1] == correo:
                    existUser = True
            if not existUser:
                values = [correo, password]
                conn = conexion.connection
                cur = conn.cursor()
                cur.execute("INSERT INTO usuarios (EMAIL, PASSWORD) VALUES (%s, %s)", values)
                conn.commit()
                print("Usuario agregado")
                return VerUsuarios(menuAgregarUsuario=False)
            else:
                print("El usuario ya existe")
                return VerUsuarios(menuAgregarUsuario=False)

    else:
        return redirect("/")

@app.route('/editarUsuario',methods = ['POST'])
def EditarUsuario():
    if session["usuario"]:
        if request.method == 'POST':
            form_data = request.form
            idUsuario = form_data['id']
            correo = form_data['correo']
            password = form_data['password']
            cur = conexion.connection.cursor()
            query = "SELECT * FROM usuarios"
            cur.execute(query)
            users=cur.fetchall()

            existUser = False
            for user in users:
                if str(user[0]) != idUsuario:
                    if user[1] == correo:
                        print("entro")
                        existUser = True

            if not existUser:
                values = [correo, password, idUsuario]
                conn = conexion.connection
                cur = conn.cursor()
                cur.execute("UPDATE usuarios SET EMAIL = %s, PASSWORD= %s WHERE ID = %s", values)
                conn.commit()
                print("Usuario agregado")
                return VerUsuarios(menuAgregarUsuario=False)
            else:
                print("El usuario ya existe")
                return VerUsuarios(menuAgregarUsuario=False)
    else:
        return redirect("/")

@app.route('/eliminarUsuario/<id_usuario>')
def EliminarUsuario(id_usuario):
    if session["usuario"]:
        print(id_usuario)
        conn = conexion.connection
        cur = conn.cursor()
        query = "DELETE FROM usuarios WHERE ID = "+id_usuario
        cur.execute(query)
        conn.commit()
        print("termino consulta")
        return VerUsuarios()
    else:
        return redirect("/")

@app.route('/informeip/<ip_dispositivo>') 
def Informesip(ip_dispositivo):
    if session["usuario"]:
        print("IP:"+ip_dispositivo)
        informe = create_list(ip_dispositivo)
        return render_template ('informe.html', us = informe)
    else:
        return redirect("/")

@app.route('/livehost-result',methods = ['POST'])
def livehost_result():
    if session["usuario"]:
        if request.method == 'POST':
            form_data = request.form
            opt=arp_scan(form_data['url'])
        cur = conexion.connection.cursor()
        cur.execute("SELECT * FROM dispositivos")
        usuarios = cur.fetchall()
        return render_template('dispositivos.html',usuarios=usuarios)
    else:
        return redirect("/")

##########################BOTON CONFIGURACION DE PROGRAMA
@app.route('/update-system-configurations',methods = ['POST'])
def update_system_configurations():
    if session["usuario"]:
        if request.method == 'POST':
            global hardDisk_alert,wifi_alert, ethernet_alert, disconnect_alert
            form_data = request.form
            hardDisk_check_box_value = request.form.getlist('hardDisk_alert')
            wifi_check_box_value = request.form.getlist('wifi_alert')
            ethernet_check_box_value = request.form.getlist('ethernet_alert')
            disconnect_check_box_values = request.form.getlist('disconnect_alert')

            if hardDisk_check_box_value:
                hardDisk_alert = "1" if hardDisk_check_box_value[0] == "on" else "0"
            else:
                hardDisk_alert = "0"

            if wifi_check_box_value:
                wifi_alert = "1" if wifi_check_box_value[0] == "on" else "0"
            else:
                wifi_alert = "0"

            if ethernet_check_box_value:
                ethernet_alert = "1" if ethernet_check_box_value[0] == "on" else "0"
            else:
                ethernet_alert = "0"

            if disconnect_check_box_values:
                disconnect_alert = "1" if disconnect_check_box_values[0] == "on" else "0"
            else:
                disconnect_alert = "0"

            values = [form_data["email_receiver"],form_data["email_sender"],form_data["email_password"],form_data["seconds_interval"],hardDisk_alert,wifi_alert,ethernet_alert,disconnect_alert]
            conn = conexion.connection
            cur = conn.cursor()
            #Cuidar que en la base de datos de configuracion solo exista 1 fila con ID = 1
            cur.execute("UPDATE configuracion SET EMAIL_RECEIVER = %s, EMAIL_SENDER= %s, PASSWORD_SENDER= %s, SECONDS_INTERVAL= %s, HARDDISK_ALERT= %s, WIFI_ALERT=%s ,ETHERNET_ALERT=%s, DISCONNECTION_ALERT=%s WHERE ID = 1", values)
            conn.commit()
        cur = conexion.connection.cursor()
        query = "SELECT * FROM configuracion"
        cur.execute(query)
        configuracion=cur.fetchall()
        return render_template('configuracion.html', configuracion = configuracion[0])
    else:
        return redirect("/")

##########################CONFIGURACION DE CORREO DE ALARMAS
def scan_all_user():
    print("inicio funcion")
    with app.app_context():
        cur = conexion.connection.cursor()
        cur.execute("SELECT * FROM dispositivos")
        usuarios = cur.fetchall()
        print("usuarios activos")
        print(usuarios)
    for user in usuarios:
        print(user)
        if user[1] != "192.168.0.1":
            varBinds = snmp_device_scan(comnty='public', hostip=user[1])
            #Alerta de desconexión de dispositivo
            #IP, TITULO, HORA FECHA, DESCRIPCIÓN
            #print("disconnect_alert",disconnect_alert, "on" if bool(disconnect_alert) else "off")
            if bool(disconnect_alert) and varBinds is None:
                print("Activando alerta desconexion")
                dt = datetime.now()
                date = dt.strftime("%Y-%m-%d")
                time = dt.strftime("%H:%M:%S")
                values = [date, time, user[2], "Crítico", user[1], "Desconexión de equipo", "El dispositivo ha sido desconectado de la red"]
                persist_alert(values)
                send_email(values)
            else:
                #Alerta de baja velocidad wifi
                #print("wifi_alert",wifi_alert, "on" if bool(wifi_alert) else "off")
                if bool(wifi_alert) and varBinds[14][1] < 70 and varBinds[14][1] > 0:
                    print("Activando alerta de velocidad Wifi")
                    dt = datetime.now()
                    date = dt.strftime("%Y-%m-%d")
                    time = dt.strftime("%H:%M:%S")
                    values = [date, time, user[2], "Aviso", user[1], "Velocidad Wifi", str("La velocidad Wifi esta por debajo del rango aceptable: " + str(varBinds[14][1])+ ".")]
                    persist_alert(values)
                    send_email(values)

                #Alerta de baja velocidad ethernet
                #print("ethernet_alert",ethernet_alert, "on" if bool(ethernet_alert) else "off")
                if bool(ethernet_alert) and varBinds[13][1] < 70 and varBinds[13][1] > 0:
                    print("Activando alerta velocidad Ethernet")
                    dt = datetime.now()
                    date = dt.strftime("%Y-%m-%d")
                    time = dt.strftime("%H:%M:%S")
                    values = [date, time, user[2], "Aviso", user[1], "Velocidad Ethernet",  str("La velocidad Ethernet esta por debajo del rango aceptable: " + str(varBinds[14][1]) + ".")]
                    persist_alert(values)
                    send_email(values)

                #Alerta tamaño de disco optimo superado
                #print("hardDisk_alert",hardDisk_alert, "on" if bool(hardDisk_alert) else "off")
                if bool(hardDisk_alert) and (varBinds[9][1] / varBinds[8][1]) >= 0.80:
                    print("Activando alerta espacio en disco HDD")
                    dt = datetime.now()
                    date = dt.strftime("%Y-%m-%d")
                    time = dt.strftime("%H:%M:%S")
                    values = [date, time, user[2], "Aviso", user[1], "Espacio en disco HDD", "El tamaño del disco HDD ha superado el 80% del total de uso."]
                    persist_alert(values)
                    send_email(values)

            
def persist_alert(values):
    with app.app_context():
        conn = conexion.connection
        cur = conn.cursor()
        cur.execute("INSERT INTO alertas (FECHA, HORA, NOMBRE_MAQUINA, NIVEL, IP, TIPO_ALERTA, MENSAJE) VALUES (%s, %s, %s, %s, %s, %s, %s)", values)
        conn.commit()


if __name__ == '__main__':       
    with app.app_context():
        cur = conexion.connection.cursor()
        cur.execute("SELECT SECONDS_INTERVAL, HARDDISK_ALERT, WIFI_ALERT, ETHERNET_ALERT, DISCONNECTION_ALERT FROM configuracion")
        data=cur.fetchall()
        hardDisk_alert = data[0][1]
        wifi_alert = data[0][2]
        ethernet_alert = data[0][3]
        disconnect_alert = data[0][4]

    timer = RepeatTimer(int(data[0][0]), scan_all_user)  
    timer.start() #recalling run  
    app.run(debug=False)