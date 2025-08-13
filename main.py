from flask import Flask, request, jsonify, send_file, render_template_string
from werkzeug.utils import secure_filename
import ocrmypdf
import tempfile
import os
import uuid
import logging
from pathlib import Path
import subprocess

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# HTML Template for the frontend
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OCRmyPDF - Online PDF OCR Converter</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }

        .container {
            max-width: 900px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
        }

        .header {
            text-align: center;
            margin-bottom: 40px;
        }

        .header h1 {
            font-size: 2.5em;
            color: #4a5568;
            margin-bottom: 10px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .header p {
            color: #718096;
            font-size: 1.1em;
            line-height: 1.6;
        }

        .upload-section {
            background: linear-gradient(135deg, #f7fafc, #edf2f7);
            border: 2px dashed #cbd5e0;
            border-radius: 12px;
            padding: 40px;
            text-align: center;
            margin-bottom: 30px;
            transition: all 0.3s ease;
            cursor: pointer;
        }

        .upload-section:hover {
            border-color: #667eea;
            background: linear-gradient(135deg, #f7fafc, #e6fffa);
            transform: translateY(-2px);
        }

        .upload-section.dragover {
            border-color: #667eea;
            background: linear-gradient(135deg, #e6fffa, #f0fff4);
        }

        .upload-icon {
            font-size: 3em;
            color: #667eea;
            margin-bottom: 15px;
            display: block;
        }

        .file-input {
            display: none;
        }

        .upload-button {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 8px;
            font-size: 1.1em;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-top: 10px;
        }

        .upload-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }

        .options-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 25px;
            margin-bottom: 30px;
        }

        .option-card {
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            border: 1px solid #e2e8f0;
            transition: all 0.3s ease;
        }

        .option-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        }

        .option-card h3 {
            color: #4a5568;
            margin-bottom: 15px;
            font-size: 1.2em;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .option-icon {
            width: 24px;
            height: 24px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 0.9em;
        }

        .form-group {
            margin-bottom: 20px;
        }

        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: #4a5568;
            font-weight: 500;
        }

        .form-control {
            width: 100%;
            padding: 10px 15px;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            font-size: 1em;
            transition: border-color 0.3s ease;
            background: #f7fafc;
        }

        .form-control:focus {
            outline: none;
            border-color: #667eea;
            background: white;
        }

        .checkbox-group {
            display: flex;
            align-items: center;
            margin-bottom: 15px;
            cursor: pointer;
            padding: 10px;
            border-radius: 8px;
            transition: background-color 0.3s ease;
        }

        .checkbox-group:hover {
            background: #f7fafc;
        }

        .checkbox-group input[type="checkbox"] {
            margin-right: 10px;
            transform: scale(1.2);
            accent-color: #667eea;
        }

        .checkbox-group label {
            margin: 0;
            cursor: pointer;
            flex: 1;
        }

        .help-text {
            font-size: 0.9em;
            color: #718096;
            margin-top: 5px;
            line-height: 1.4;
        }

        .convert-section {
            text-align: center;
            padding: 30px;
            background: linear-gradient(135deg, #f7fafc, #edf2f7);
            border-radius: 12px;
            margin-top: 20px;
        }

        .convert-button {
            background: linear-gradient(135deg, #48bb78, #38a169);
            color: white;
            border: none;
            padding: 15px 40px;
            border-radius: 10px;
            font-size: 1.2em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .convert-button:hover:not(:disabled) {
            transform: translateY(-3px);
            box-shadow: 0 12px 25px rgba(72, 187, 120, 0.4);
        }

        .convert-button:disabled {
            background: #a0aec0;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }

        .progress-container {
            display: none;
            margin-top: 20px;
        }

        .progress-bar {
            width: 100%;
            height: 8px;
            background: #e2e8f0;
            border-radius: 4px;
            overflow: hidden;
            margin-bottom: 10px;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            width: 0%;
            transition: width 0.3s ease;
            position: relative;
        }

        .progress-fill::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            bottom: 0;
            right: 0;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
            animation: shimmer 2s infinite;
        }

        @keyframes shimmer {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }

        .status-message {
            color: #4a5568;
            font-size: 1em;
        }

        .result-section {
            display: none;
            margin-top: 30px;
            padding: 25px;
            background: linear-gradient(135deg, #f0fff4, #e6fffa);
            border-radius: 12px;
            border: 1px solid #9ae6b4;
        }

        .download-button {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 8px;
            font-size: 1.1em;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
        }

        .download-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
        }

        .error-message {
            background: #fed7d7;
            color: #c53030;
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
            border: 1px solid #fc8181;
        }

        .language-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 10px;
            margin-top: 10px;
        }

        .language-item {
            display: flex;
            align-items: center;
            padding: 8px;
            border-radius: 6px;
            transition: background-color 0.3s ease;
        }

        .language-item:hover {
            background: #f7fafc;
        }

        .language-item input {
            margin-right: 8px;
            accent-color: #667eea;
        }

        @media (max-width: 768px) {
            .container {
                padding: 20px;
                margin: 10px;
            }
            
            .options-grid {
                grid-template-columns: 1fr;
            }
            
            .header h1 {
                font-size: 2em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📄 OCRmyPDF Online</h1>
            <p>Transform your scanned PDFs into searchable, text-enabled documents with powerful OCR technology. Upload your PDF and let our tool make it searchable!</p>
        </div>

        <div class="upload-section" id="uploadSection">
            <div class="upload-icon">📄</div>
            <h3>Drop your PDF here or click to browse</h3>
            <p>Supports PDF files and images (JPG, PNG, TIFF) • Max size: 50MB</p>
            <input type="file" id="fileInput" class="file-input" accept=".pdf,.jpg,.jpeg,.png,.tiff,.tif">
            <button class="upload-button" onclick="document.getElementById('fileInput').click()">Choose File</button>
            <div id="fileInfo" style="margin-top: 15px; display: none;"></div>
        </div>

        <div class="options-grid">
            <!-- Language Options -->
            <div class="option-card">
                <h3><span class="option-icon">🌍</span>Language Settings</h3>
                <div class="form-group">
                    <label>OCR Languages:</label>
                    <div class="language-grid">
                        <div class="language-item">
                            <input type="checkbox" id="lang-eng" value="eng" checked>
                            <label for="lang-eng">English</label>
                        </div>
                        <div class="language-item">
                            <input type="checkbox" id="lang-spa" value="spa">
                            <label for="lang-spa">Spanish</label>
                        </div>
                        <div class="language-item">
                            <input type="checkbox" id="lang-fra" value="fra">
                            <label for="lang-fra">French</label>
                        </div>
                        <div class="language-item">
                            <input type="checkbox" id="lang-deu" value="deu">
                            <label for="lang-deu">German</label>
                        </div>
                        <div class="language-item">
                            <input type="checkbox" id="lang-ita" value="ita">
                            <label for="lang-ita">Italian</label>
                        </div>
                        <div class="language-item">
                            <input type="checkbox" id="lang-chi-sim" value="chi_sim">
                            <label for="lang-chi-sim">Chinese (Simplified)</label>
                        </div>
                    </div>
                    <div class="help-text">Select the languages present in your document. Multiple languages can be selected for multilingual documents.</div>
                </div>
            </div>

            <!-- Image Processing Options -->
            <div class="option-card">
                <h3><span class="option-icon">🖼️</span>Image Processing</h3>
                <div class="checkbox-group">
                    <input type="checkbox" id="deskew">
                    <label for="deskew">
                        <strong>Deskew Pages</strong>
                        <div class="help-text">Fix pages that are rotated or tilted</div>
                    </label>
                </div>
                <div class="checkbox-group">
                    <input type="checkbox" id="rotate-pages">
                    <label for="rotate-pages">
                        <strong>Auto-Rotate Pages</strong>
                        <div class="help-text">Detect and fix page orientation automatically</div>
                    </label>
                </div>
                <div class="checkbox-group">
                    <input type="checkbox" id="remove-background">
                    <label for="remove-background">
                        <strong>Remove Background</strong>
                        <div class="help-text">Clean up noisy backgrounds (not recommended for photos)</div>
                    </label>
                </div>
                <div class="checkbox-group">
                    <input type="checkbox" id="clean">
                    <label for="clean">
                        <strong>Clean Images</strong>
                        <div class="help-text">Apply cleaning operations to improve text recognition</div>
                    </label>
                </div>
            </div>

            <!-- Output Options -->
            <div class="option-card">
                <h3><span class="option-icon">📤</span>Output Settings</h3>
                <div class="form-group">
                    <label for="output-type">Output Format:</label>
                    <select id="output-type" class="form-control">
                        <option value="pdfa">PDF/A (Archival)</option>
                        <option value="pdf">Regular PDF</option>
                    </select>
                    <div class="help-text">PDF/A is recommended for long-term storage</div>
                </div>
                <div class="form-group">
                    <label for="optimize">Optimization Level:</label>
                    <select id="optimize" class="form-control">
                        <option value="1">Level 1 (Lossless)</option>
                        <option value="2">Level 2 (Some lossy compression)</option>
                        <option value="3">Level 3 (Aggressive compression)</option>
                    </select>
                    <div class="help-text">Higher levels create smaller files but may reduce image quality</div>
                </div>
            </div>

            <!-- Advanced Options -->
            <div class="option-card">
                <h3><span class="option-icon">⚙️</span>Advanced Options</h3>
                <div class="form-group">
                    <label for="title">Document Title:</label>
                    <input type="text" id="title" class="form-control" placeholder="Optional document title">
                </div>
                <div class="form-group">
                    <label for="pages">Process Specific Pages:</label>
                    <input type="text" id="pages" class="form-control" placeholder="e.g., 1-5,8,10-12 (leave empty for all pages)">
                    <div class="help-text">Specify page ranges using commas and hyphens</div>
                </div>
                <div class="checkbox-group">
                    <input type="checkbox" id="force-ocr">
                    <label for="force-ocr">
                        <strong>Force OCR</strong>
                        <div class="help-text">Replace any existing text with fresh OCR results</div>
                    </label>
                </div>
            </div>
        </div>

        <div class="convert-section">
            <button class="convert-button" id="convertButton" onclick="startConversion()" disabled>
                🚀 Start OCR Conversion
            </button>
            <div class="progress-container" id="progressContainer">
                <div class="progress-bar">
                    <div class="progress-fill" id="progressFill"></div>
                </div>
                <div class="status-message" id="statusMessage">Processing...</div>
            </div>
        </div>

        <div class="result-section" id="resultSection">
            <h3>✅ Conversion Complete!</h3>
            <p>Your PDF has been successfully processed with OCR. The text is now searchable and copy-pasteable.</p>
            <a class="download-button" id="downloadLink" href="#" download>📥 Download OCR'd PDF</a>
            <div style="margin-top: 15px;">
                <small><strong>Processing Summary:</strong> <span id="processingInfo"></span></small>
            </div>
        </div>

        <div id="errorSection" style="display: none;"></div>
    </div>

    <script>
        let selectedFile = null;

        // File upload handling
        document.getElementById('fileInput').addEventListener('change', handleFileSelect);
        
        // Upload section click handler
        document.getElementById('uploadSection').addEventListener('click', (e) => {
            if (e.target === e.currentTarget || e.target.classList.contains('upload-icon') || e.target.tagName === 'H3' || e.target.tagName === 'P') {
                document.getElementById('fileInput').click();
            }
        });

        // Drag and drop handling
        const uploadSection = document.getElementById('uploadSection');
        
        uploadSection.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadSection.classList.add('dragover');
        });

        uploadSection.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadSection.classList.remove('dragover');
        });

        uploadSection.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadSection.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFileSelect({ target: { files: files } });
            }
        });

        function handleFileSelect(event) {
            const file = event.target.files[0];
            if (file) {
                // Validate file type
                const validTypes = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png', 'image/tiff'];
                const fileType = file.type.toLowerCase();
                const fileName = file.name.toLowerCase();
                
                const isValidType = validTypes.includes(fileType) || 
                                  fileName.endsWith('.pdf') || 
                                  fileName.endsWith('.jpg') || 
                                  fileName.endsWith('.jpeg') || 
                                  fileName.endsWith('.png') || 
                                  fileName.endsWith('.tiff') || 
                                  fileName.endsWith('.tif');
                
                if (!isValidType) {
                    showError('Please select a PDF or image file (JPG, PNG, TIFF)');
                    return;
                }

                // Validate file size (50MB limit)
                if (file.size > 50 * 1024 * 1024) {
                    showError('File size must be less than 50MB');
                    return;
                }

                selectedFile = file;
                const fileInfo = document.getElementById('fileInfo');
                fileInfo.innerHTML = `
                    <div style="background: #e6fffa; padding: 10px; border-radius: 8px; border: 1px solid #9ae6b4;">
                        <strong>📄 ${file.name}</strong><br>
                        Size: ${(file.size / 1024 / 1024).toFixed(2)} MB<br>
                        Type: ${file.type || 'Unknown'}
                    </div>
                `;
                fileInfo.style.display = 'block';
                document.getElementById('convertButton').disabled = false;
                hideError();
            }
        }

        function startConversion() {
            if (!selectedFile) {
                showError('Please select a file first!');
                return;
            }

            const formData = new FormData();
            formData.append('file', selectedFile);
            
            // Collect options
            const selectedLanguages = Array.from(document.querySelectorAll('input[type="checkbox"][id^="lang-"]:checked'))
                .map(cb => cb.value);
            formData.append('languages', selectedLanguages.join('+'));
            
            formData.append('deskew', document.getElementById('deskew').checked);
            formData.append('rotate_pages', document.getElementById('rotate-pages').checked);
            formData.append('remove_background', document.getElementById('remove-background').checked);
            formData.append('clean', document.getElementById('clean').checked);
            formData.append('force_ocr', document.getElementById('force-ocr').checked);
            formData.append('output_type', document.getElementById('output-type').value);
            formData.append('optimize', document.getElementById('optimize').value);
            formData.append('title', document.getElementById('title').value);
            formData.append('pages', document.getElementById('pages').value);

            // Show progress
            document.getElementById('convertButton').disabled = true;
            document.getElementById('progressContainer').style.display = 'block';
            document.getElementById('resultSection').style.display = 'none';
            hideError();
            
            const progressFill = document.getElementById('progressFill');
            const statusMessage = document.getElementById('statusMessage');
            
            // Simulate progress
            progressFill.style.width = '10%';
            statusMessage.textContent = 'Uploading file...';

            // Make request to backend
            fetch('/process', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(data => {
                        throw new Error(data.error || 'Processing failed');
                    });
                }
                return response.blob();
            })
            .then(blob => {
                progressFill.style.width = '100%';
                statusMessage.textContent = 'Conversion complete!';
                
                // Create download link
                const url = URL.createObjectURL(blob);
                const downloadLink = document.getElementById('downloadLink');
                downloadLink.href = url;
                downloadLink.download = selectedFile.name.replace(/\.[^/.]+$/, '') + '_OCR.pdf';
                
                // Show results
                setTimeout(() => {
                    document.getElementById('progressContainer').style.display = 'none';
                    document.getElementById('resultSection').style.display = 'block';
                    
                    const selectedLanguages = Array.from(document.querySelectorAll('input[type="checkbox"][id^="lang-"]:checked'))
                        .map(cb => cb.nextElementSibling.textContent);
                    
                    const processingOptions = [];
                    if (document.getElementById('deskew').checked) processingOptions.push('Deskewed');
                    if (document.getElementById('rotate-pages').checked) processingOptions.push('Auto-rotated');
                    if (document.getElementById('remove-background').checked) processingOptions.push('Background removed');
                    if (document.getElementById('clean').checked) processingOptions.push('Image cleaned');
                    
                    const info = `Languages: ${selectedLanguages.join(', ')}. ${processingOptions.length > 0 ? 'Applied: ' + processingOptions.join(', ') + '.' : ''}`;
                    document.getElementById('processingInfo').textContent = info;
                    
                    document.getElementById('convertButton').disabled = false;
                    document.getElementById('convertButton').innerHTML = '🔄 Process Another File';
                }, 1000);
            })
            .catch(error => {
                console.error('Error:', error);
                document.getElementById('progressContainer').style.display = 'none';
                document.getElementById('convertButton').disabled = false;
                showError('Error: ' + error.message);
            });
        }

        function showError(message) {
            const errorSection = document.getElementById('errorSection');
            errorSection.innerHTML = `<div class="error-message">${message}</div>`;
            errorSection.style.display = 'block';
        }

        function hideError() {
            document.getElementById('errorSection').style.display = 'none';
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'message': 'OCRmyPDF service is running'})

@app.route('/process', methods=['POST'])
def process_pdf():
    temp_files = []
    
    try:
        # Validate file upload
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Secure filename
        filename = secure_filename(file.filename)
        if not filename:
            filename = f"upload_{uuid.uuid4().hex}.pdf"

        # Create temporary input file
        input_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_files.append(input_temp.name)
        
        # Save uploaded file
        file.save(input_temp.name)
        input_temp.close()
        
        logger.info(f"Processing file: {filename} (size: {os.path.getsize(input_temp.name)} bytes)")

        # Create temporary output file
        output_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_files.append(output_temp.name)
        output_temp.close()

        # Parse options from form data
        options = {}
        
        # Language options
        languages = request.form.get('languages', 'eng')
        if languages:
            options['language'] = languages.split('+')
        
        # Boolean options
        bool_options = ['deskew', 'rotate_pages', 'remove_background', 'clean', 'force_ocr']
        for opt in bool_options:
            if request.form.get(opt) == 'true':
                options[opt] = True
        
        # Integer options
        optimize = request.form.get('optimize', '1')
        try:
            options['optimize'] = int(optimize)
        except ValueError:
            options['optimize'] = 1
        
        # String options
        output_type = request.form.get('output_type', 'pdfa')
        if output_type in ['pdf', 'pdfa']:
            options['output_type'] = output_type
        
        title = request.form.get('title', '').strip()
        if title:
            options['title'] = title
            
        pages = request.form.get('pages', '').strip()
        if pages:
            options['pages'] = pages

        logger.info(f"OCR options: {options}")

        # Run OCRmyPDF
        try:
            ocrmypdf.ocr(
                input_temp.name,
                output_temp.name,
                progress_bar=False,
                **options
            )
        except ocrmypdf.exceptions.PriorOcrFoundError:
            # If OCR already exists and force_ocr is not set, try with force_ocr
            if not options.get('force_ocr'):
                logger.info("Prior OCR found, retrying with force_ocr=True")
                options['force_ocr'] = True
                ocrmypdf.ocr(
                    input_temp.name,
                    output_temp.name,
                    progress_bar=False,
                    **options
                )
            else:
                raise

        # Verify output file exists and has content
        if not os.path.exists(output_temp.name) or os.path.getsize(output_temp.name) == 0:
            raise Exception("OCR processing failed - no output generated")

        logger.info(f"OCR completed successfully. Output size: {os.path.getsize(output_temp.name)} bytes")

        # Generate download filename
        base_name = os.path.splitext(filename)[0]
        download_filename = f"{base_name}_OCR.pdf"

        # Send the processed file
        return send_file(
            output_temp.name,
            as_attachment=True,
            download_name=download_filename,
            mimetype='application/pdf'
        )

    except ocrmypdf.exceptions.InputFileError as e:
        logger.error(f"Input file error: {e}")
        return jsonify({'error': f'Invalid input file: {str(e)}'}), 400
    
    except ocrmypdf.exceptions.UnsupportedImageFormatError as e:
        logger.error(f"Unsupported image format: {e}")
        return jsonify({'error': 'Unsupported image format. Please use PDF, JPG, PNG, or TIFF files.'}), 400
    
    except ocrmypdf.exceptions.DpiError as e:
        logger.error(f"DPI error: {e}")
        return jsonify({'error': 'Image resolution too low for OCR. Please use higher quality images.'}), 400
    
    except ocrmypdf.exceptions.OutputFileAccessError as e:
        logger.error(f"Output file error: {e}")
        return jsonify({'error': 'Unable to create output file. Please try again.'}), 500
    
    except Exception as e:
        logger.error(f"Processing error: {e}")
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500
    
    finally:
        # Cleanup temporary files
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    logger.debug(f"Cleaned up temporary file: {temp_file}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temporary file {temp_file}: {e}")

if __name__ == '__main__':
    # Check if required dependencies are available
    try:
        import ocrmypdf
        logger.info("OCRmyPDF library loaded successfully")
        
        # Test Tesseract availability
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            logger.info(f"Tesseract available: {result.stdout.split()[1] if result.stdout else 'Unknown version'}")
        else:
            logger.warning("Tesseract not found or not working properly")
            
    except ImportError as e:
        logger.error(f"Failed to import ocrmypdf: {e}")
    except subprocess.TimeoutExpired:
        logger.warning("Tesseract version check timed out")
    except Exception as e:
        logger.warning(f"Could not verify Tesseract installation: {e}")
    
    # Start the Flask application
    port = int(os.environ.get('PORT', 8000))
    logger.info(f"Starting OCRmyPDF web service on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
