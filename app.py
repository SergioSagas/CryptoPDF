import os
import base64
import hashlib
import uuid
import json
import io
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature
import qrcode

app = Flask(__name__)

# Configuración de rutas para claves y registro de firmas
PRIVATE_KEY_PATH = 'private_key.pem'
PUBLIC_KEY_PATH = 'public_key.pem'
REGISTRY_FILE = 'registry.json'

def generate_keys_if_not_exist():
    """Genera un par de claves RSA de 2048 bits si no existen en el disco."""
    if not os.path.exists(PRIVATE_KEY_PATH) or not os.path.exists(PUBLIC_KEY_PATH):
        print("Generando nuevo par de claves RSA...")
        # Generar clave privada
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        
        # Serializar clave privada a formato PEM
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        # Obtener y serializar clave pública a formato PEM
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        # Guardar en archivos
        with open(PRIVATE_KEY_PATH, 'wb') as f:
            f.write(private_pem)
        with open(PUBLIC_KEY_PATH, 'wb') as f:
            f.write(public_pem)
        print("Claves RSA generadas y guardadas exitosamente.")
    else:
        print("Claves RSA existentes detectadas.")

# Asegurar la existencia de las claves antes de iniciar
generate_keys_if_not_exist()

def load_private_key():
    """Carga la clave privada RSA desde el archivo PEM."""
    with open(PRIVATE_KEY_PATH, 'rb') as f:
        return serialization.load_pem_private_key(
            f.read(),
            password=None
        )

def load_public_key():
    """Carga la clave pública RSA desde el archivo PEM."""
    with open(PUBLIC_KEY_PATH, 'rb') as f:
        return serialization.load_pem_public_key(
            f.read()
        )

def read_registry():
    """Lee el registro JSON de firmas digitales."""
    if not os.path.exists(REGISTRY_FILE):
        return {}
    try:
        with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def write_registry(registry_data):
    """Escribe en el registro JSON de firmas digitales."""
    try:
        with open(REGISTRY_FILE, 'w', encoding='utf-8') as f:
            json.dump(registry_data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error al escribir en el registro: {e}")

@app.route('/')
def index():
    """Renderiza la página principal con la interfaz de firma y verificación."""
    return render_template('index.html')

@app.route('/sign', methods=['POST'])
def sign_pdf():
    """
    Ruta para firmar un documento PDF.
    Espera un archivo PDF en request.files['pdf_file'].
    Calcula el hash SHA-256, firma, registra en BD local, genera un Código QR y retorna JSON.
    """
    if 'pdf_file' not in request.files:
        return jsonify({'success': False, 'error': 'No se proporcionó ningún archivo PDF.'}), 400
        
    pdf_file = request.files['pdf_file']
    if pdf_file.filename == '':
        return jsonify({'success': False, 'error': 'El nombre del archivo está vacío.'}), 400

    try:
        # Leer el contenido del PDF
        pdf_content = pdf_file.read()
        
        # 1. Generar hash SHA-256 del contenido para mostrar al usuario
        sha256_hash = hashlib.sha256(pdf_content).hexdigest()
        
        # Cargar clave privada
        private_key = load_private_key()
        
        # 2. Firmar utilizando el esquema de padding PSS con hashes.SHA256()
        # Lógica requerida por el usuario:
        signature = private_key.sign(
            pdf_content,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        # Codificar la firma en Base64 para transportarla en JSON
        signature_base64 = base64.b64encode(signature).decode('utf-8')
        
        # 3. Integración de Actividad 5: Código QR y Registro para Verificación Pública
        # Generar metadatos
        doc_id = str(uuid.uuid4())
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Construir URL de verificación pública dinámica
        verification_url = f"{request.host_url}verify_public/{doc_id}"
        
        # Guardar en registro local
        registry = read_registry()
        registry[doc_id] = {
            'filename': pdf_file.filename,
            'hash': sha256_hash,
            'date': date_str,
            'signature': signature_base64
        }
        write_registry(registry)
        
        # Datos a codificar en el código QR
        qr_data = (
            f"ID Documento: {doc_id}\n"
            f"Fecha Firma: {date_str}\n"
            f"Hash SHA-256: {sha256_hash}\n"
            f"Verificar en: {verification_url}"
        )
        
        # Generar código QR en memoria
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Convertir a imagen PNG
        qr_img = qr.make_image(fill_color="#0f172a", back_color="#ffffff")
        qr_io = io.BytesIO()
        
        # PyPNGImage y otras implementaciones no aceptan el parámetro 'format', pero PilImage sí
        try:
            qr_img.save(qr_io, format="PNG")  # type: ignore
        except TypeError:
            qr_io.seek(0)
            qr_io.truncate()
            qr_img.save(qr_io)
            
        qr_bytes = qr_io.getvalue()
        
        # Codificar a base64 para envío en JSON
        qr_base64 = base64.b64encode(qr_bytes).decode('utf-8')
        
        return jsonify({
            'success': True,
            'hash': sha256_hash,
            'signature_base64': signature_base64,
            'filename': f"{pdf_file.filename}.sig",
            'doc_id': doc_id,
            'date': date_str,
            'verification_url': verification_url,
            'qr_base64': qr_base64
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f"Error al firmar: {str(e)}"}), 500

@app.route('/verify', methods=['POST'])
def verify_signature():
    """
    Ruta para verificar la firma de un documento PDF.
    Espera un archivo PDF en request.files['pdf_file'] y el archivo de firma en request.files['signature_file'].
    Calcula el hash SHA-256 del PDF y verifica usando la clave pública correspondiente.
    """
    if 'pdf_file' not in request.files or 'signature_file' not in request.files:
        return jsonify({'success': False, 'error': 'Debe subir tanto el PDF original como la firma (.sig).'}), 400
        
    pdf_file = request.files['pdf_file']
    sig_file = request.files['signature_file']
    
    if pdf_file.filename == '' or sig_file.filename == '':
        return jsonify({'success': False, 'error': 'Ninguno de los archivos puede estar vacío.'}), 400
        
    try:
        pdf_content = pdf_file.read()
        sig_content = sig_file.read()
        
        # Calcular el hash SHA-256 del PDF para visualización del usuario
        sha256_hash = hashlib.sha256(pdf_content).hexdigest()
        
        # Cargar clave pública
        public_key = load_public_key()
        
        # Intentar decodificar en base64 en caso de que la firma se haya enviado como texto base64
        if len(sig_content) != 256:
            try:
                cleaned_sig = sig_content.strip()
                sig_content_decoded = base64.b64decode(cleaned_sig)
                if len(sig_content_decoded) == 256:
                    sig_content = sig_content_decoded
            except Exception:
                pass
        
        # Verificar la firma utilizando la clave pública correspondiente
        try:
            public_key.verify(
                sig_content,
                pdf_content,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            is_valid = True
            message = "Firma Válida. El documento no ha sido modificado y proviene del poseedor de la clave privada."
        except InvalidSignature:
            is_valid = False
            message = "Firma Inválida. La firma no coincide con el documento o fue alterada."
        
        return jsonify({
            'success': True,
            'hash': sha256_hash,
            'valid': is_valid,
            'message': message
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f"Error durante la verificación: {str(e)}"}), 500

@app.route('/verify_public/<doc_id>', methods=['GET'])
def verify_public(doc_id):
    """
    Ruta pública para verificar un documento por su ID UUID.
    Busca los metadatos en el registro y comprueba la autenticidad del mismo.
    """
    registry = read_registry()
    doc_info = registry.get(doc_id)
    
    if doc_info:
        return render_template(
            'public_verify.html',
            found=True,
            doc_id=doc_id,
            filename=doc_info.get('filename'),
            hash=doc_info.get('hash'),
            date=doc_info.get('date'),
            signature=doc_info.get('signature')
        )
    else:
        return render_template(
            'public_verify.html',
            found=False,
            doc_id=doc_id
        )

if __name__ == '__main__':
    # Ejecutar servidor de desarrollo local
    app.run(debug=True, port=5000)
