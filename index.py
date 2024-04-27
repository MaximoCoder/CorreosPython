import schedule
import time
from pytz import timezone
import smtplib
import os
from dotenv import load_dotenv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from conexiondb import *
from datetime import datetime, timedelta
import locale
# Establece la localización en español
locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
#Cargar variables de entorno pass y user
load_dotenv()
remitente = os.getenv('USER')
# Definir tomorrow en el ámbito global
today = None
tomorrow = None
#Checar la fecha para luego traer solo los datos de los clientes que tienen cita el dia de mañana 
def check_date():
    global tomorrow
    global today
    #Traer la fecha actual
    today = datetime.now(timezone('America/Mexico_City')).strftime("%Y-%m-%d")
    #Sumarle un dia a la fecha actual  
    tomorrow = (datetime.strptime(today, '%Y-%m-%d') + timedelta(days=1)).strftime("%Y-%m-%d")
    #print(today)  2024-04-24
    #print(tomorrow) 2024-04-25
    print("Iniciando envio de correos...")

schedule.every().day.at("17:07", timezone("America/Monterrey")).do(check_date) #Realizar cada dia , para despues reutilizar esa fecha y traer los registros que corresponden a esa fecha
#TRAER TODOS LOS DATOS DE LA TABLA DE CITAS
def get_citas():
        global tomorrow
        try: 
            connect = conexion.conexionDB()
            if connect.is_connected():
                cursor = connect.cursor(buffered=True)
                with connect.cursor() as cursor:
                    #SE trae todo de la tabla de citas donde el estado de la cita sea nulo y la fecha sea la del dia de mañana apartir del dia actual y lo ordena por la hora
                    cursor.execute(f"SELECT * FROM citas WHERE estado_cita IS NULL AND fecha = '{tomorrow}' ORDER BY hora ASC") 
                    result = cursor.fetchall()  # Fetch all rows
                    #Convertir los datos en un formato manejable
                    columns = [column[0] for column in cursor.description]
                    rows = [dict(zip(columns, row)) for row in result]
                    #print(rows)
                    return rows
        except mysql.connector.Error as e:
            print("No se pudo conectar", e)
        finally:
            if connect.is_connected():
                cursor.close()
                connect.close()
                #print("MySQL connection is closed")
def obtener_citas_y_enviar_correos():
    global today
    citas = get_citas()  # Llamada a la función para obtener las citas

    for cita in citas:  # Iterar sobre cada cita
        nombre_cliente = cita['nombre_cliente']
        tipo_cita = cita['tipo_cita']
        email_cliente = cita['email_cliente']
        fecha = cita['fecha']
        fecha_str = fecha.strftime("%A, %d de %B de %Y")  # Formatear la fecha a: Lunes, 24 de Abril de 2024
        hora = cita['hora']
        # Convertir la cadena 'today' en un objeto datetime
        today_datetime = datetime.strptime(today, '%Y-%m-%d')
        # Convert the timedelta to a datetime by adding it to today's date
        cita_datetime = today_datetime + hora
        hora_str = cita_datetime.strftime("%I:%M %p")  # Formatear la hora a: 12:00 AM o 12:00 PM
        #Remplazamos los valores dentro del html Reemplazar los valores dentro del HTML
        with open('email.html', 'r') as archivo:
            html = archivo.read()
            html = html.replace('[nombre_cliente]', nombre_cliente)
            html = html.replace('[fecha_str]', fecha_str)
            html = html.replace('[hora_str]', hora_str)
            html = html.replace('[tipo_cita]', tipo_cita)

        # Crear un nuevo archivo con el contenido modificado
        nuevo_archivo = f'email_enviado.html'
        with open(nuevo_archivo, 'w') as nuevo:
            nuevo.write(html)


        # Luego de reemplazar los valores enviamos el correo.
        EnvioCorreos(email_cliente)

# Programar la nueva función para que se ejecute a una hora específica
schedule.every().day.at("17:08", timezone("America/Monterrey")).do(obtener_citas_y_enviar_correos)

def EnvioCorreos(email_cliente):
    destinatario = email_cliente
    asunto = "Confirmación o Cancelación de Cita Dental"
    # Crear un objeto MIMEMultipart
    msg = MIMEMultipart()
    msg['Subject'] = asunto
    msg['From'] = remitente
    msg['To'] = destinatario
    with open('email_enviado.html', 'r') as archivo:
        html = archivo.read()
    #Adjuntar el html al mensaje
    msg.attach(MIMEText(html, 'html'))
    try:
        # Enviar el correo
        server = smtplib.SMTP('smtp.gmail.com', 587)
        #Conexion segura
        server.starttls()
        server.login(remitente, os.getenv('PASS'))
        #Enviando el correo
        server.sendmail(remitente, destinatario, msg.as_string())
        #Cierre del servidor
        server.quit()
        # Imprimir confirmación de envío
        print("Correo enviado a: " + email_cliente + " a las " + str(datetime.now(timezone('America/Mexico_City')).strftime("%H:%M:%S")))
    except Exception as e:
        print(e)
    


while True:
    # Verificar si hay alguna tarea pendiente para ejecutar y si es así, ejecutarla
    schedule.run_pending()
    time.sleep(1)