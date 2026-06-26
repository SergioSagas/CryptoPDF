# CryptoPDF - Sistema de Firma Digital y Verificación de Documentos PDF

CryptoPDF es una aplicación web dinámica desarrollada en Python utilizando el framework **Flask**. Su propósito es permitir a los usuarios firmar digitalmente documentos PDF mediante algoritmos de criptografía asimétrica (RSA) y verificar su autenticidad e integridad de manera pública mediante códigos QR.

Este proyecto ha sido desarrollado como parte de las actividades prácticas de la asignatura de **Seguridad Informática**.

---

## 🔒 Características Principales

1. **Generación Automática de Claves RSA**:
   * Al iniciar la aplicación, el sistema comprueba la existencia de un par de claves en formato PEM (`private_key.pem` y `public_key.pem`).
   * Si no existen, genera automáticamente un par de claves RSA de **2048 bits** de forma segura.
2. **Firmado Digital de Documentos PDF**:
   * Calcula el hash criptográfico **SHA-256** del archivo PDF cargado.
   * Firma el hash utilizando la clave privada RSA del servidor bajo el estándar de padding **RSA-PSS** (Probabilistic Signature Scheme) con hashing SHA-256 y longitud máxima de sal.
   * Genera un archivo con extensión `.sig` que contiene la firma codificada.
3. **Registro y Verificación Pública vía QR**:
   * Genera un identificador único (UUID) para cada documento firmado y registra la firma, nombre de archivo, hash y fecha en una base de datos local estructurada en JSON (`registry.json`).
   * Crea un código QR dinámico que contiene metadatos clave y un enlace de verificación pública (`/verify_public/<doc_id>`).
4. **Módulo de Verificación Integrado**:
   * Permite subir un PDF original junto con su firma `.sig` (en binario o texto base64) para comprobar la validez utilizando la clave pública RSA del servidor.
   * Cuenta con la ruta pública para que terceros, escaneando el código QR impreso o digital, puedan constatar de manera rápida que el documento es íntegro y auténtico.

---

## 🛠️ Tecnologías Utilizadas

* **Backend**: Python 3.x, Flask (Servidor Web)
* **Criptografía**: `cryptography` (Generación de claves, firma y verificación)
* **Códigos QR**: `qrcode` (Generador de imágenes QR en memoria)
* **Procesamiento de Imágenes**: `Pillow` / `PyPNG` (Soporte de guardado para códigos QR)
* **Frontend**: HTML5 semántico, CSS3 moderno (Glassmorphism, animaciones fluidas, diseño responsive) y JavaScript Vanilla (AJAX para comunicación asíncrona)
* **Servidor de Producción**: Gunicorn

---

## 📂 Estructura del Repositorio

```text
├── static/
│   ├── css/
│   │   └── style.css      # Estilos visuales de la aplicación web
├── templates/
│   ├── index.html         # Interfaz de usuario principal (Firmar / Verificar)
│   └── public_verify.html # Interfaz pública de verificación por QR
├── app.py                 # Lógica principal del servidor Flask y Criptografía
├── requirements.txt       # Dependencias necesarias para el proyecto
├── .gitignore             # Archivo para evitar subir claves y caché a GitHub
└── README.md              # Documentación detallada del proyecto (Este archivo)
```

---

## 🚀 Instalación y Ejecución en Local

### Prerrequisitos
Tener instalado Python 3.8 o superior y Git.

### 1. Clonar el repositorio
```bash
git clone https://github.com/SergioSagas/CryptoPDF.git
cd CryptoPDF
```

### 2. Configurar entorno virtual (Recomendado)
```bash
# Crear entorno virtual
python -m venv venv

# Activar en Windows
venv\Scripts\activate

# Activar en Linux/macOS
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Ejecutar la aplicación
```bash
python app.py
```
La aplicación estará disponible en tu navegador en la dirección: [http://localhost:5000](http://localhost:5000).

---

## ☁️ Despliegue en Producción (Render)

Este proyecto está listo para ser desplegado en plataformas en la nube como **Render**:

1. Vincula tu cuenta de GitHub con **Render**.
2. Crea un nuevo **Web Service**.
3. Selecciona el repositorio `CryptoPDF`.
4. Establece la siguiente configuración:
   * **Language**: `Python`
   * **Build Command**: `pip install -r requirements.txt`
   * **Start Command**: `gunicorn app:app`
   * **Instance Type**: `Free` (Gratuito).
5. Haz clic en **Create Web Service**. ¡Render proporcionará una URL pública y segura (HTTPS) para el sistema!

---

## 👁️ Aspectos de Seguridad

* **Exclusión de Claves en Git**: El archivo `.gitignore` está configurado para omitir los archivos `private_key.pem`, `public_key.pem` y `registry.json`. Esto evita que las llaves privadas del servidor o la base de datos se expongan públicamente en GitHub, manteniendo la integridad del sistema.
* **Seguridad de la Firma**: Se utiliza **RSA-PSS** en lugar de PKCS#1 v1.5, puesto que PSS ofrece mayor robustez criptográfica basada en esquemas probabilísticos matemáticamente más seguros.
