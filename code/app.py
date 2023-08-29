from flask import Flask, render_template, request, abort, send_file
import os
import xml.etree.ElementTree as ET
from googletrans import Translator
import requests
import uuid
import json

if os.environ.get('DOCKER', '') == "yes":
    UPLOAD_FOLDER = '/usr/src/app/traducciones'
    # UPLOAD_FOLDER = 'code\\traducciones'
else:
    UPLOAD_FOLDER = 'traducciones'

ALLOWED_EXTENSIONS = set(['xlf'])

# app = Flask(__name__)
app = Flask(__name__, static_url_path='/static')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def generar_xml(xml_file):
    errores_encontrados = ""
    xml_file = request.files['filexml']

    # Parsear el archivo XML
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Namespace a utilizar para las etiquetas
    ns = {'ns0': 'urn:oasis:names:tc:xliff:document:1.2'}

    # Obtener el nombre del archivo de la etiqueta <file> y agregar "-ES.xlf"
    file_element = root.find('ns0:file', ns)
    original_name = file_element.get('original')
    new_file_name = original_name + ".g-es.xlf"

    # Modificar el atributo target-language a "es-ES"
    file_element.set('target-language', 'es-ES')

    # Cargar el diccionario de traducciones desde un archivo (diccionario.txt)
    translation_dict = {}
    try:
        with open('diccionarioprevio.txt', 'r', encoding='utf-8') as dict_file:
            for line in dict_file:
                key, value = line.strip().split('~')
                # Comprobamos si la palabra ya existe en el diccionario si no existe la añadimos
                if key not in translation_dict:
                    translation_dict[key] = value
    except FileNotFoundError:
        print("El archivo de diccionario no se encontró.")

    try:
        with open('diccionario.txt', 'r', encoding='utf-8') as dict_file:
            for line in dict_file:
                key, value = line.strip().split('~')
                if key not in translation_dict:
                    translation_dict[key] = value

    except FileNotFoundError:
        print("El archivo de diccionario no se encontró.")

    translation_dict_Individual = {}
    try:
        with open('diccionario_arreglos.txt', 'r', encoding='utf-8') as dict_file:
            for line in dict_file:
                key, value = line.strip().split('~')
                translation_dict_Individual[key] = value
                # print(key, value)
    except FileNotFoundError:
        print("El archivo de diccionario no se encontró.")

    # Recorrer las 5 primeras lineas de translation_dict
    # for key, value in list(translation_dict_Individual.items())[:2]:
    #     print("::::::::::::::::::::::::::: "+key + " - " + value)

    contador1 = 0
    contador2 = 0
    contador3 = 0
    symbols_to_check = ['¿', '¡', '!', '?', '.']

    for trans_unit in root.findall('.//ns0:trans-unit', ns):
        source = trans_unit.find('ns0:source', ns)
        try:
            if source is not None:
                source_text = source.text
                # print("Texto a traducir: " + source_text)

                for key, value in translation_dict.items():
                    if source_text.lower() == key.lower().strip(" "):
                        target = ET.Element('target')
                        if not any(value.startswith(symbol) for symbol in symbols_to_check):
                            target.text = str(value).strip(" ").capitalize()
                        else:
                            target.text = str(value).strip(" ")
                        print(
                            "Encuentro la traducción en el diccionario " + target.text)
                        contador1 += 1
                        break
                    else:
                        target = None

                if target is None:
                    # Inicializar el traductor de Google
                    translator = Translator()
                    translation = translator.translate(
                        source_text, src='en', dest='es')
                    # translation = translator.translate(source_text)
                    # Crear un nuevo elemento <target> y agregar la traducción
                    target = ET.Element('target')
                    target.text = translation.text
                    # si dentro de alguna palabras de las frases de target.text esta dentro de translation_dict_Individual cambiar
                    # por la traduccion de translation_dict_Individual
                    for key, value in translation_dict_Individual.items():
                        print("[" + target.text.lower() + "] [" +
                              key.lower().strip(" ") + "]")
                        if key.lower().strip(" ") in target.text.lower():
                            # Verificar si no empieza con un símbolo antes de capitalizar
                            if not any(value.startswith(symbol) for symbol in symbols_to_check):
                                # Cambiar la parte que coincide por la traducción y capitalizar
                                target.text = target.text.lower().replace(
                                    key.lower().strip(" "), value.strip(" ")).capitalize()
                            else:
                                # Cambiar la parte que coincide por la traducción sin capitalizar
                                target.text = target.text.lower().replace(
                                    key.lower().strip(" "), value.strip(" "))
                            contador3 += 1
                            # print(
                            #     "Encuentro la traducción en el diccionario Individual " + str(value))
                    contador2 += 1

                # Insertar el elemento <target> justo después del elemento <source>
                index_source = list(trans_unit).index(source)
                trans_unit.insert(index_source + 1, target)
                target.tail = "\n" + ("\t" * 5)

        except Exception as e:
            print(f"Error en la traducción: {e} - {source_text}")
            errores_encontrados += f"Error en la traducción: {e} - {source_text} - linea {contador2} + {contador1} \n"

    # Eliminar los prefijos "ns0" antes de guardar el nuevo árbol
    ET.register_namespace('', 'urn:oasis:names:tc:xliff:document:1.2')
    # Crear un nuevo árbol XML con las modificaciones
    new_tree = ET.ElementTree(root)

    # Guardar el nuevo árbol XML en un archivo
    new_file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_file_name)
    new_tree.write(new_file_path, encoding="utf-8", xml_declaration=True)

    # new_tree.write(new_file_name, encoding="utf-8", xml_declaration=True)
    print("Contador1 " + str(contador1) + " - Contador2 " + str(contador2))
    return new_file_name, errores_encontrados, contador1, contador2, contador3


def contar_etiquetas(new_file_name):
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
    return source_count, target_count


@app.route("/")
def home():
    return render_template('home.html')


@app.route('/uploader', methods=['POST'])
def upload_file():
    NO_VALID_XML = "No se ha proporcionado una fichero xlf válido."
    if request.method == 'POST' and request.files:
        try:
            new_file_name, errores_encontrados, contadorStandar, contadorGoogle, contadorModificados = generar_xml(
                request.files['filexml'])
            ruta = os.path.join(app.config['UPLOAD_FOLDER'], new_file_name)
            source_count, target_count, = contar_etiquetas(ruta)
            # OFRECER LINK de decarga del fichero generado
            if errores_encontrados != "":
                return render_template('results.html', text=new_file_name, text1="\n" + new_file_name + " generado correctamente." + "\nCantidad de etiquetas source: " +
                                       str(source_count) + "\nCantidad de etiquetas target: " + str(target_count) +
                                       "\nTraducciones realizadas con el diccionario del Standard: " + str(contadorStandar) +
                                       "\nTraducciones realizadas con el Traductor de Google: " + str(contadorGoogle) +
                                       "\nArreglos realizados con el diccionario de arreglos: " + str(contadorModificados) +
                                       "\nErrores encontrados:\n" + errores_encontrados)
            else:
                return render_template('results.html', text=new_file_name, text1="\n" + new_file_name + " generado correctamente." + "\nCantidad de etiquetas source: " +
                                       str(source_count) + "\nCantidad de etiquetas target: " + str(target_count) +
                                       "\nTraducciones realizadas con el diccionario del Standard: " + str(contadorStandar) +
                                       "\nTraducciones realizadas con el Traductor de Google: " + str(contadorGoogle) +
                                       "\nArreglos realizados con el diccionario de arreglos: " + str(contadorModificados))
        except Exception as e:
            return render_template('results.html', text1="\n" + NO_VALID_XML + "\n" + str(e) + "\nRuta:" + str(UPLOAD_FOLDER))
    return render_template('home.html')

# Crear una ruta para descargar el fichero generado


@app.route('/download/<path:filename>', methods=['GET', 'POST'])
def download(filename):
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        print("Error en la descarga:", e)
        abort(500)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
