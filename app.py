import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from PIL import Image
import pytesseract
import io
import uuid


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB maximum file size
app.secret_key = b'7527886838752'


ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'password'


def process_image(image):
    text = pytesseract.image_to_string(Image.open(image))
    return text.strip()


def generate_shareable_link(filename, text):
    # Generate a unique identifier (UUID) for the shareable link
    shareable_id = str(uuid.uuid4())
    session[shareable_id] = {
        'filename': filename,
        'text': text
    }
    return shareable_id

# Routes

# Admin Login and Logout Routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            flash('Logged in successfully.', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('admin_login.html')



@app.route('/admin/logout')
def admin_logout():
    session.pop('logged_in', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy_policy.html')

@app.route('/blog')
def blog():
    return render_template('blog.html')

@app.route('/admin')
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))

    uploads = os.listdir(app.config['UPLOAD_FOLDER'])
    num_uploads = len(uploads)
    return render_template('admin.html', num_uploads=num_uploads, uploads=uploads)


# New route for file deletion
@app.route('/admin/delete_file/<filename>', methods=['POST'])
def delete_file(filename):
    if not session.get('logged_in'):
        flash('Please log in to delete files.', 'error')
        return redirect(url_for('admin_login'))

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            flash(f'{filename} has been deleted.', 'success')
        except Exception as e:
            flash(f'Error deleting {filename}: {str(e)}', 'error')
    else:
        flash(f'File not found: {filename}', 'error')

    return redirect(url_for('admin'))


# New route for handling deletion of multiple files
@app.route('/admin/delete_files', methods=['POST'])
def delete_files():
    if not session.get('logged_in'):
        flash('Please log in to delete files.', 'error')
        return redirect(url_for('admin_login'))

    files_to_delete = request.form.getlist('files_to_delete')

    for filename in files_to_delete:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                flash(f'{filename} has been deleted.', 'success')
            except Exception as e:
                flash(f'Error deleting {filename}: {str(e)}', 'error')
        else:
            flash(f'File not found: {filename}', 'error')

    return redirect(url_for('admin'))


# Shareable Link Page
@app.route('/shareable_link/<shareable_id>')
def shareable_link(shareable_id):
    data = session.get(shareable_id)
    if data:
        # If the shareable_id exists in the session, render the shareable_link.html template
        return render_template('shareable_link.html', data=data)
    else:
        # If the shareable_id is not found in the session, redirect to the index page
        flash('Shareable link not found.', 'error')
        return redirect(url_for('index'))
    


# Helper Functions
def process_image(image):
    text = pytesseract.image_to_string(Image.open(image))
    formatted_text = ""

    # Add line breaks based on periods
    lines = text.split(".")
    for i, line in enumerate(lines):
        line = line.strip()
        if line:
            formatted_text += line + "."
            if i < len(lines) - 1:
                formatted_text += "\n\n"  # Add double line break after each period (end of sentence)

    return formatted_text.strip()


# Upload and Process Image
@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('index'))

    # Check file size
    if len(file.read()) > app.config['MAX_CONTENT_LENGTH']:
        flash('File size exceeds the limit of 5MB', 'error')
        return redirect(url_for('index'))

    # Reset file cursor position to read again during processing
    file.seek(0)

    if file:
        filename = file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        text = process_image(file_path)

        # Generate the shareable link
        shareable_id = generate_shareable_link(filename, text)

        return render_template('index.html', filename=filename, text=text, shareable_id=shareable_id)




if __name__ == '__main__':
    app.run(debug=True)
