# 📄 OCRmyPDF Online - Replit Implementation

A complete, fully functional web-based OCR service that converts scanned PDFs into searchable documents using OCRmyPDF and Tesseract OCR.

## 🚀 Quick Deploy to Replit

### Method 1: Import from GitHub (Recommended)
1. Create a new GitHub repository
2. Upload these files to your repo:
   - `main.py`
   - `requirements.txt`
   - `.replit`
   - `replit.nix`
   - `README.md`

3. Go to [Replit](https://replit.com) and click "Import from GitHub"
4. Enter your repository URL
5. Wait for installation to complete (2-3 minutes)
6. Click "Run" - your app will be live!

### Method 2: Direct Upload
1. Create a new Python repl on [Replit](https://replit.com)
2. Delete the default `main.py` file
3. Upload all the files from this package
4. Click "Run"

## 🎯 Features

- **✨ Modern Web Interface**: Beautiful, responsive design
- **🔄 Real OCR Processing**: Uses actual OCRmyPDF + Tesseract
- **🌍 Multi-Language Support**: English, Spanish, French, German, Italian, Chinese
- **🖼️ Image Processing**: Deskew, rotate, clean, background removal
- **📤 Multiple Output Formats**: PDF/A for archival, regular PDF
- **⚙️ Advanced Options**: Page selection, optimization levels, metadata
- **📱 Mobile Friendly**: Works on all devices
- **🔒 Secure**: Files processed in memory, automatically cleaned up

## 🛠️ Technology Stack

- **Backend**: Python Flask + OCRmyPDF + Tesseract
- **Frontend**: Modern HTML5/CSS3/JavaScript
- **OCR Engine**: Tesseract 4.x with multiple language packs
- **PDF Processing**: OCRmyPDF, Ghostscript, qpdf
- **Deployment**: Replit (free tier)

## 📊 Supported File Types

- **Input**: PDF, JPG, JPEG, PNG, TIFF
- **Output**: Searchable PDF or PDF/A
- **Max Size**: 50MB per file

## 🎮 Usage

1. **Upload**: Drag & drop or click to select your scanned PDF
2. **Configure**: Choose languages and processing options
3. **Process**: Click "Start OCR Conversion"
4. **Download**: Get your searchable PDF

## 🔧 Configuration Options

### Language Support
- English (default)
- Spanish, French, German, Italian
- Chinese Simplified
- Multiple languages can be selected

### Image Processing
- **Deskew**: Fix tilted/crooked pages
- **Auto-Rotate**: Correct page orientation
- **Remove Background**: Clean noisy backgrounds
- **Clean Images**: Enhance text recognition

### Output Settings
- **PDF/A**: Archival format (recommended)
- **Regular PDF**: Standard format
- **Optimization**: 3 levels of compression

### Advanced Features
- **Page Selection**: Process specific pages (e.g., "1-5,8,10-12")
- **Force OCR**: Replace existing text
- **Custom Titles**: Set PDF metadata

## 🚀 Deployment Options

### Free Hosting
- **Replit**: 500 hours/month free (recommended)
- **Railway**: 500 hours/month free
- **Render**: 750 hours/month free

### Custom Domain (Optional)
- Connect your own domain through Replit
- SSL certificates included
- No additional costs

## 🛡️ Security & Privacy

- Files are processed in memory only
- No files stored on server
- Automatic cleanup after processing
- All processing happens server-side
- HTTPS encryption for file transfers

## 📈 Performance

- **Processing Speed**: ~30 seconds per page (varies by complexity)
- **Concurrent Users**: Replit free tier supports moderate usage
- **File Size Limit**: 50MB (configurable)
- **Memory Usage**: Optimized for small server instances

## 🔍 Troubleshooting

### Common Issues

1. **"Tesseract not found"**
   - Replit should automatically install Tesseract
   - Try restarting the repl if this persists

2. **"Processing failed"**
   - Check file format (PDF, JPG, PNG, TIFF only)
   - Ensure file size is under 50MB
   - Try with fewer processing options

3. **"Out of memory"**
   - Reduce optimization level
   - Process fewer pages at once
   - Use smaller input files

### Debug Mode

To enable detailed logging, modify `main.py`:

```python
app.run(host='0.0.0.0', port=port, debug=True)
```

## 📄 License

This implementation uses:
- **OCRmyPDF**: Mozilla Public License 2.0
- **Tesseract**: Apache License 2.0
- **Frontend Code**: MIT License (free to use and modify)

## 🤝 Contributing

Feel free to:
- Report bugs and issues
- Suggest new features
- Submit pull requests
- Share improvements

## 🌟 Acknowledgments

- **OCRmyPDF Team**: For the excellent OCR library
- **Tesseract Team**: For the OCR engine
- **Replit**: For free hosting platform
- **Community**: For testing and feedback

---

## 🎉 You're Ready!

Your OCRmyPDF service is now live and ready to convert scanned documents into searchable PDFs. Share the link with anyone who needs OCR services!

**Live URL**: Your Replit URL will be: `https://your-repl-name.your-username.repl.co`
