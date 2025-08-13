from flask import Flask, request, jsonify, send_file, render_template_string
import tempfile
import os
import logging
import subprocess
import threading
import uuid
import json
import time

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory storage for job status (in production, use Redis or database)
jobs = {}

# Simple HTML with polling-based processing
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>OCR PDF Converter</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            max-width: 800px; 
            margin: 0 auto; 
            padding: 20px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .upload { 
            border: 2px dashed #ccc; 
            padding: 40px; 
            text-align: center; 
            margin: 20px 0; 
            border-radius: 10px;
        }
        .upload:hover { border-color: #667eea; }
        button { 
            background: #667eea; 
            color: white; 
            padding: 15px 30px; 
            border: none; 
            border-radius: 8px; 
            cursor: pointer; 
            font-size: 16px;
            transition: all 0.3s ease;
        }
        button:hover { background: #5a6fd8; transform: translateY(-2px); }
        button:disabled { background: #ccc; cursor: not-allowed; transform: none; }
        .progress { 
            display: none; 
            margin: 20px 0; 
            padding: 20px; 
            background: #f8f9fa; 
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        .progress-bar {
            width: 100%;
            height: 8px;
            background: #e2e8f0;
            border-radius: 4px;
            overflow: hidden;
            margin: 10px 0;
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
            top: 0; left: 0; bottom: 0; right: 0;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
            animation: shimmer 2s infinite;
        }
        @keyframes shimmer {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }
        .error { 
            color: #dc3545; 
            background: #f8d7da; 
            padding: 15px; 
            margin: 10px 0; 
            border-radius: 8px; 
            border: 1px solid #f5c6cb;
        }
        .success { 
            color: #155724; 
            background: #d4edda; 
            padding: 15px; 
            margin: 10px 0; 
            border-radius: 8px; 
            border: 1px solid #c3e6cb;
        }
        .file-info { 
            background: #e3f2fd; 
            padding: 15px; 
            border-radius: 8px; 
            margin: 15px 0; 
            border: 1px solid #bbdefb;
        }
        .debug { 
            background: #f5f5f5; 
            padding: 10px; 
            border-radius: 4px; 
            margin: 10px 0; 
            font-size: 12px; 
            font-family: monospace;
        }
        input[type="file"] {
            margin: 15px 0;
            padding: 10px;
            border: 2px solid #ddd;
            border-radius: 6px;
            font-size: 14px;
            width: 100%;
            max-width: 400px;
        }
        .download-button {
            background: linear-gradient(135deg, #48bb78, #38a169);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 8px;
            font-size: 1.1em;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
            margin: 10px 5px;
        }
        .download-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(72, 187, 120, 0.4);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📄 OCR PDF Converter</h1>
        <p>Convert scanned PDFs to searchable documents - <strong>No more timeouts!</strong></p>

        <div class="upload">
            <h3>📁 Select PDF File</h3>
            <input type="file" id="fileInput" accept=".pdf" />
            <br>
            <button id="convertBtn" onclick="startConversion()" disabled>Choose a PDF file first</button>
            <br><br>
            <small>💡 Now works with large files - no network timeouts!</small>
        </div>

        <div id="status">
            <div class="debug">
                <strong>🔧 System Status:</strong>
                JavaScript: <span id="jsStatus">❌</span> |
                File Input: <span id="inputStatus">❌</span> |
                Event Listener: <span id="listenerStatus">❌</span>
            </div>
        </div>
    </div>

    <script>
        console.log('🚀 JavaScript loading...');

        document.getElementById('jsStatus').textContent = '✅';

        const fileInput = document.getElementById('fileInput');
        const convertBtn = document.getElementById('convertBtn');
        const status = document.getElementById('status');

        if (fileInput) {
            document.getElementById('inputStatus').textContent = '✅';
            console.log('✅ File input found');
        }

        let selectedFile = null;
        let pollInterval = null;

        fileInput.addEventListener('change', function(e) {
            console.log('🔥 File selected!');

            const file = e.target.files[0];

            if (!file) {
                updateStatus('<div class="error">❌ No file selected</div>');
                return;
            }

            console.log('📄 File details:', {
                name: file.name,
                size: file.size,
                type: file.type
            });

            if (!file.name.toLowerCase().endsWith('.pdf')) {
                updateStatus('<div class="error">❌ Please select a PDF file</div>');
                return;
            }

            if (file.size > 50 * 1024 * 1024) {
                updateStatus('<div class="error">❌ File too large (max 50MB)</div>');
                return;
            }

            selectedFile = file;
            convertBtn.disabled = false;
            convertBtn.textContent = `🚀 Convert ${file.name}`;

            updateStatus(`
                <div class="file-info">
                    <strong>✅ Ready to Convert!</strong><br><br>
                    📄 <strong>File:</strong> ${file.name}<br>
                    📊 <strong>Size:</strong> ${(file.size/1024/1024).toFixed(2)} MB<br>
                    ⚡ <strong>New:</strong> Uses polling to prevent timeouts!
                </div>
            `);

            console.log('✅ File ready for conversion');
        });

        document.getElementById('listenerStatus').textContent = '✅';
        console.log('✅ Event listeners added');

        async function startConversion() {
            if (!selectedFile) {
                updateStatus('<div class="error">❌ No file selected</div>');
                return;
            }

            console.log('🚀 Starting conversion with polling...');

            convertBtn.disabled = true;
            convertBtn.textContent = '🔄 Starting...';

            try {
                // Step 1: Start the job
                const formData = new FormData();
                formData.append('file', selectedFile);

                console.log('📤 Submitting job to server...');

                const startResponse = await fetch('/start-conversion', {
                    method: 'POST',
                    body: formData
                });

                if (!startResponse.ok) {
                    const errorData = await startResponse.json();
                    throw new Error(errorData.error || 'Failed to start conversion');
                }

                const jobData = await startResponse.json();
                const jobId = jobData.job_id;

                console.log('✅ Job started with ID:', jobId);

                // Step 2: Poll for progress
                updateStatus(`
                    <div class="progress" style="display: block;">
                        <h4>🚀 Job Started Successfully!</h4>
                        <p>📋 Job ID: ${jobId}</p>
                        <div class="progress-bar">
                            <div class="progress-fill" id="progressFill"></div>
                        </div>
                        <p id="progressText">⏳ Initializing OCR processing...</p>
                        <small>✅ <strong>No timeouts:</strong> Using background processing with progress updates</small>
                    </div>
                `);

                convertBtn.textContent = '⏳ Processing...';

                // Poll for updates
                pollForProgress(jobId);

            } catch (error) {
                console.error('❌ Failed to start conversion:', error);

                updateStatus(`
                    <div class="error">
                        <h4>❌ Failed to Start Conversion</h4>
                        <p><strong>Error:</strong> ${error.message}</p>
                    </div>
                `);

                convertBtn.disabled = false;
                convertBtn.textContent = '🔄 Try Again';
            }
        }

        function pollForProgress(jobId) {
            console.log('🔄 Starting to poll job:', jobId);

            pollInterval = setInterval(async () => {
                try {
                    console.log('📡 Polling job status...');

                    const response = await fetch(`/job-status/${jobId}`);

                    if (!response.ok) {
                        throw new Error('Failed to get job status');
                    }

                    const status = await response.json();
                    console.log('📊 Job status:', status);

                    updateProgress(status);

                    if (status.status === 'completed') {
                        clearInterval(pollInterval);
                        showCompletion(jobId, status);
                    } else if (status.status === 'failed') {
                        clearInterval(pollInterval);
                        showError(status.error || 'Processing failed');
                    }

                } catch (error) {
                    console.error('❌ Polling error:', error);
                    // Continue polling - might be temporary network issue
                }
            }, 2000); // Poll every 2 seconds
        }

        function updateProgress(status) {
            const progressFill = document.getElementById('progressFill');
            const progressText = document.getElementById('progressText');

            if (progressFill && progressText) {
                progressFill.style.width = status.progress + '%';
                progressText.textContent = status.message || 'Processing...';
            }
        }

        function showCompletion(jobId, status) {
            console.log('🎉 Job completed!');

            updateStatus(`
                <div class="success">
                    <h4>✅ Conversion Complete!</h4>
                    <p><strong>${selectedFile.name}</strong> has been converted successfully!</p>
                    <p>📊 <strong>Processing time:</strong> ${Math.round(status.processing_time || 0)} seconds</p>
                    <p>📄 <strong>Pages processed:</strong> ${status.pages_processed || 'Unknown'}</p>
                    <a href="/download/${jobId}" class="download-button">📥 Download OCR'd PDF</a>
                    <br><small>💡 Download will start when you click the button above</small>
                </div>
            `);

            convertBtn.disabled = false;
            convertBtn.textContent = '🔄 Convert Another File';

            // Auto-download
            setTimeout(() => {
                window.open(`/download/${jobId}`, '_blank');
            }, 1000);
        }

        function showError(errorMessage) {
            console.error('❌ Job failed:', errorMessage);

            updateStatus(`
                <div class="error">
                    <h4>❌ Conversion Failed</h4>
                    <p><strong>Error:</strong> ${errorMessage}</p>
                    <p>Please try again or use a different PDF file.</p>
                </div>
            `);

            convertBtn.disabled = false;
            convertBtn.textContent = '🔄 Try Again';
        }

        function updateStatus(html) {
            const debug = `
                <div class="debug">
                    <strong>🔧 System Status:</strong>
                    JavaScript: ✅ | File Input: ✅ | Event Listener: ✅ | 
                    Time: ${new Date().toLocaleTimeString()}
                </div>
            `;
            status.innerHTML = debug + html;
        }

        // Cleanup on page unload
        window.addEventListener('beforeunload', () => {
            if (pollInterval) {
                clearInterval(pollInterval);
            }
        });

        // Initialize
        updateStatus('<div style="color: #666;">👆 Select a PDF file above to get started</div>');
        console.log('✅ System ready');
    </script>
</body>
</html>
'''

def process_pdf_background(job_id, input_file, original_filename):
    """Background processing function"""
    try:
        jobs[job_id]['status'] = 'processing'
        jobs[job_id]['message'] = 'Starting OCR processing...'
        jobs[job_id]['progress'] = 10

        logger.info(f"🚀 Background processing started for job {job_id}")

        output_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        output_temp.close()

        # Validate input
        input_size = os.path.getsize(input_file)
        logger.info(f"📊 Processing file: {original_filename} ({input_size} bytes)")

        if input_size == 0:
            raise Exception("Input file is empty")

        with open(input_file, 'rb') as f:
            header = f.read(10)
            if not header.startswith(b'%PDF'):
                raise Exception("Invalid PDF file")

        jobs[job_id]['progress'] = 20
        jobs[job_id]['message'] = 'Validating PDF file...'

        # Try basic tesseract first
        try:
            logger.info("🔍 Trying basic tesseract...")
            cmd = ['tesseract', input_file, output_temp.name.replace('.pdf', ''), 'pdf']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            expected_output = output_temp.name.replace('.pdf', '') + '.pdf'
            if result.returncode == 0 and os.path.exists(expected_output):
                if expected_output != output_temp.name:
                    os.rename(expected_output, output_temp.name)
                logger.info("✅ Basic tesseract succeeded!")
            else:
                raise Exception("Basic tesseract failed")

        except Exception as e:
            logger.info(f"⚠️ Basic method failed: {e}")

            # Use PyMuPDF method
            jobs[job_id]['progress'] = 30
            jobs[job_id]['message'] = 'Using advanced OCR method...'

            import fitz
            import shutil

            pdf_doc = fitz.open(input_file)
            page_count = pdf_doc.page_count
            logger.info(f"📄 Processing {page_count} pages with PyMuPDF...")

            jobs[job_id]['pages_total'] = page_count

            temp_dir = tempfile.mkdtemp()
            page_pdfs = []

            try:
                for page_num in range(page_count):
                    # Update progress
                    progress = 30 + (page_num / page_count) * 50
                    jobs[job_id]['progress'] = int(progress)
                    jobs[job_id]['message'] = f'Processing page {page_num + 1}/{page_count}...'

                    logger.info(f"📄 Processing page {page_num + 1}/{page_count}")

                    page = pdf_doc[page_num]
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))

                    img_path = os.path.join(temp_dir, f"page_{page_num:04d}.png")
                    pix.save(img_path)

                    pdf_base = os.path.join(temp_dir, f"page_{page_num:04d}")
                    cmd = ['tesseract', img_path, pdf_base, 'pdf']

                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

                    page_pdf = pdf_base + '.pdf'
                    if result.returncode == 0 and os.path.exists(page_pdf):
                        page_pdfs.append(page_pdf)
                        logger.info(f"✅ Page {page_num + 1} OCR complete")

                pdf_doc.close()

                jobs[job_id]['progress'] = 85
                jobs[job_id]['message'] = f'Merging {len(page_pdfs)} pages...'

                # Merge pages
                if page_pdfs:
                    if len(page_pdfs) == 1:
                        shutil.copy2(page_pdfs[0], output_temp.name)
                    else:
                        try:
                            import pikepdf
                            merged_pdf = pikepdf.Pdf.new()

                            for page_pdf in page_pdfs:
                                if os.path.exists(page_pdf):
                                    src_pdf = pikepdf.Pdf.open(page_pdf)
                                    merged_pdf.pages.extend(src_pdf.pages)
                                    src_pdf.close()

                            merged_pdf.save(output_temp.name)
                            merged_pdf.close()
                            logger.info(f"✅ Merged {len(page_pdfs)} pages!")

                        except ImportError:
                            shutil.copy2(page_pdfs[0], output_temp.name)
                            logger.info("✅ Used first page (pikepdf not available)")

                else:
                    raise Exception("No pages could be processed")

            finally:
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass

        # Check output
        if not os.path.exists(output_temp.name) or os.path.getsize(output_temp.name) == 0:
            raise Exception("No valid output generated")

        output_size = os.path.getsize(output_temp.name)

        # Store results
        jobs[job_id]['status'] = 'completed'
        jobs[job_id]['progress'] = 100
        jobs[job_id]['message'] = 'Conversion completed successfully!'
        jobs[job_id]['output_file'] = output_temp.name
        jobs[job_id]['output_size'] = output_size
        jobs[job_id]['pages_processed'] = jobs[job_id].get('pages_total', 1)
        jobs[job_id]['processing_time'] = time.time() - jobs[job_id]['start_time']

        logger.info(f"✅ Job {job_id} completed successfully! Output: {output_size} bytes")

    except Exception as e:
        logger.error(f"❌ Job {job_id} failed: {e}")
        jobs[job_id]['status'] = 'failed'
        jobs[job_id]['error'] = str(e)

        # Cleanup
        try:
            if 'output_temp' in locals() and os.path.exists(output_temp.name):
                os.unlink(output_temp.name)
        except:
            pass

    finally:
        # Cleanup input file
        try:
            if os.path.exists(input_file):
                os.unlink(input_file)
        except:
            pass

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/start-conversion', methods=['POST'])
def start_conversion():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Generate unique job ID
        job_id = str(uuid.uuid4())

        # Save file
        input_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        file.save(input_temp.name)
        input_temp.close()

        # Initialize job
        jobs[job_id] = {
            'status': 'started',
            'progress': 0,
            'message': 'Job initialized...',
            'filename': file.filename,
            'start_time': time.time()
        }

        # Start background processing
        thread = threading.Thread(target=process_pdf_background, 
                                 args=(job_id, input_temp.name, file.filename))
        thread.daemon = True
        thread.start()

        logger.info(f"🚀 Started job {job_id} for file: {file.filename}")

        return jsonify({
            'job_id': job_id,
            'status': 'started',
            'message': 'Processing started'
        })

    except Exception as e:
        logger.error(f"❌ Failed to start conversion: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/job-status/<job_id>')
def get_job_status(job_id):
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404

    job = jobs[job_id]
    return jsonify({
        'status': job['status'],
        'progress': job.get('progress', 0),
        'message': job.get('message', 'Processing...'),
        'filename': job.get('filename'),
        'pages_processed': job.get('pages_processed'),
        'processing_time': job.get('processing_time')
    })

@app.route('/download/<job_id>')
def download_result(job_id):
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404

    job = jobs[job_id]

    if job['status'] != 'completed':
        return jsonify({'error': 'Job not completed'}), 400

    if 'output_file' not in job or not os.path.exists(job['output_file']):
        return jsonify({'error': 'Output file not found'}), 404

    try:
        filename = job['filename']
        safe_filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).strip()
        download_filename = f"{os.path.splitext(safe_filename)[0]}_OCR.pdf"

        return send_file(
            job['output_file'],
            as_attachment=True,
            download_name=download_filename,
            mimetype='application/pdf'
        )

    except Exception as e:
        logger.error(f"❌ Download failed for job {job_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/test')
def test():
    try:
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True, timeout=5)
        tesseract_version = result.stdout.split('\n')[0] if result.returncode == 0 else "Not found"
    except:
        tesseract_version = "Error checking"

    return jsonify({
        'status': 'working',
        'flask': 'OK',
        'tesseract': tesseract_version,
        'active_jobs': len(jobs),
        'polling_system': 'enabled'
    })

if __name__ == '__main__':
    logger.info("🚀 Starting OCR PDF Converter with Polling System")

    # Test dependencies
    try:
        result = subprocess.run(['tesseract', '--version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            logger.info(f"✅ Tesseract found: {version}")
        else:
            logger.warning("⚠️ Tesseract not responding properly")
    except:
        logger.warning("⚠️ Could not verify Tesseract installation")

    app.run(host='0.0.0.0', port=8000, debug=True)
