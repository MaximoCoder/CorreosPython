import mysql.connector

class conexion:
    def conexionDB():
        try:
            conexion = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="dentista"
            )
            #print("Conectado a la base de datos")
            #Regresar la variable
            return conexion
        except mysql.connector.Error as e:
            print("Error al conectar a la base de datos:", e)

            return conexion
        
    conexionDB()