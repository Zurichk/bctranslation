from flask import Flask, render_template, request, abort, send_file
import os
import xml.etree.ElementTree as ET
from googletrans import Translator

if os.environ.get('DOCKER', '') == "yes":
    UPLOAD_FOLDER = '/usr/src/app/traducciones'
    #UPLOAD_FOLDER = 'code\\traducciones'
else:
    UPLOAD_FOLDER = 'traducciones'

ALLOWED_EXTENSIONS = set(['xlf'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/")

def home():
    return render_template('home.html')

@app.route('/uploader', methods = ['POST'])
def upload_file():
    NO_VALID_XML = "No se ha proporcionado una fichero xlf válido."
    if request.method == 'POST' and request.files:
        try:
            new_file_name, errores_encontrados = generar_xml(request.files['filexml'])
            ruta = os.path.join(app.config['UPLOAD_FOLDER'], new_file_name)
            source_count, target_count = contar_etiquetas(ruta)
            #ver en que carpeta estoy
            print(os.getcwd())
            #OFRECER LINK de decarga del fichero generado
            return render_template('results.html', text = new_file_name, text1= "\n" + new_file_name + " generado correctamente." + "\n" + "Cantidad de etiquetas source: " + 
                                   str(source_count) + "\n" + "Cantidad de etiquetas target: " + str(target_count) + "\n" + errores_encontrados)
        except Exception as e:
            print ('Estoy entrando en la expeption')
            return render_template('results.html', text1= "\n" + NO_VALID_XML + "\n" + str(e) + "\nRuta:" + str(UPLOAD_FOLDER))

        # if not os.environ.get('DOCKER', '') == "yes":
        #     myobj = gTTS(text=text, slow=False)
        #     myobj.save(app.config['UPLOAD_FOLDER'] + "/speech.mp3")
        #     playsound(app.config['UPLOAD_FOLDER'] + "/speech.mp3")

        # return render_template('results.html', text=text)
    return render_template('home.html')

#Crear una ruta para descargar el fichero generado
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
    new_file_name = original_name + ".es.xlf"

    # Modificar el atributo target-language a "es-ES"
    file_element.set('target-language', 'es-ES')

    # Inicializar el traductor de Google
    translator = Translator()
    
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
            errores_encontrados += f"Error en la traducción: {e} - {source_text}\n"
            
    # Eliminar los prefijos "ns0" antes de guardar el nuevo árbol
    ET.register_namespace('', 'urn:oasis:names:tc:xliff:document:1.2')
    # Crear un nuevo árbol XML con las modificaciones
    new_tree = ET.ElementTree(root)
    
    # Guardar el nuevo árbol XML en un archivo
    new_file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_file_name)
    new_tree.write(new_file_path, encoding="utf-8", xml_declaration=True)
    
    #new_tree.write(new_file_name, encoding="utf-8", xml_declaration=True)
    
    return new_file_name, errores_encontrados

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