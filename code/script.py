from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
# import csv
import pandas as pd
import xml.etree.ElementTree as ET
from googletrans import Translator
#from translate import Translator

# Configurar las opciones del controlador (driver)
# options = webdriver.ChromeOptions()
# Aquí puedes agregar cualquier opción adicional que necesites, por ejemplo, para inhabilitar las notificaciones del navegador:
# options.add_argument("--disable-notifications")

# Inicializar el controlador (driver) remoto con las opciones configuradas
# driver = webdriver.Remote('http://localhost:4444/wd/hub', options=options)

# pedir por consola el nombre del archivo
#xml_file = input("Ingrese el nombre del archivo: ")

xml_file = "EjProduccion.g.xlf"

# Parsear el archivo XML
tree = ET.parse(xml_file)
root = tree.getroot()

# Namespace a utilizar para las etiquetas
ns = {'ns0': 'urn:oasis:names:tc:xliff:document:1.2'}

# Obtener el nombre del archivo de la etiqueta <file> y agregar "-ES.xlf"
file_element = root.find('ns0:file', ns)
original_name = file_element.get('original')
new_file_name = original_name + ".es.xlf"

# Modificar el atributo target-language a "es-ES"
file_element.set('target-language', 'es-ES')

# Inicializar el traductor de Google
translator = Translator()

# Inicializar el traductor
#translator = Translator(from_lang='en', to_lang='es')

for trans_unit in root.findall('.//ns0:trans-unit', ns):
    source = trans_unit.find('ns0:source', ns)
    try:
        if source is not None:
            source_text = source.text
            translation = translator.translate(source_text, src='en', dest='es')
            #translation = translator.translate(source_text)
            # Crear un nuevo elemento <target> y agregar la traducción
            target = ET.Element('target')
            target.text = translation.text
            #print(translation.text)

            # Insertar el elemento <target> justo después del elemento <source>
            index_source = list(trans_unit).index(source)
            trans_unit.insert(index_source + 1, target)

            target.tail = "\n" + ("\t" * 5)
    except Exception as e:
        print(f"Error en la traducción: {e} - {source_text}")

    # Traducir el texto de inglés a español
    # translation = translator.translate(source_text, src='en', dest='es')


# Eliminar los prefijos "ns0" antes de guardar el nuevo árbol
ET.register_namespace('', 'urn:oasis:names:tc:xliff:document:1.2')
# Crear un nuevo árbol XML con las modificaciones
new_tree = ET.ElementTree(root)

# Guardar el nuevo árbol XML en un archivo
new_tree.write(new_file_name, encoding="utf-8", xml_declaration=True)

# Parsear el archivo XML
tree = ET.parse(new_file_name)
root = tree.getroot()

# Namespace a utilizar para las etiquetas
ns = {'ns0': 'urn:oasis:names:tc:xliff:document:1.2'}

# Contador para las etiquetas <source> y <target>
source_count = 0
target_count = 0

# Recorrer los elementos XML y contar las etiquetas <source> y <target>
for trans_unit in root.findall('.//ns0:trans-unit', ns):
    source = trans_unit.find('ns0:source', ns)
    target = trans_unit.find('ns0:target', ns)

    if source is not None:
        source_count += 1

    if target is not None:
        target_count += 1

print("Cantidad de etiquetas <source>: ", source_count)
print("Cantidad de etiquetas <target>: ", target_count)


# preguntas = pd.read_csv("EjProduccion.g.xlf", delimiter=";", encoding='unicode_escape')
# filas = preguntas.shape[0]  # Nº de filas
# columnas = preguntas.shape[1]  # Nº de filas

# driver.get("https://www.w3schools.com/html/default.asp")
# time.sleep(5)
# all_cookies = driver.get_cookies()
# print(all_cookies)

# # Cerrar el navegador
# driver.quit()
