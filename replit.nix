{ pkgs }: {
  deps = [
    pkgs.python311Full
    pkgs.replitPackages.prybar-python311
    pkgs.replitPackages.stderred

    # OCR dependencies - Use tesseract5 for newer version
    pkgs.tesseract5
    pkgs.ghostscript
    pkgs.unpaper
    pkgs.qpdf
    pkgs.pngquant
    pkgs.jbig2dec
    
    # Image processing libraries
    pkgs.libjpeg
    pkgs.libpng
    pkgs.libtiff
    pkgs.zlib
    pkgs.freetype
    pkgs.fontconfig
    pkgs.leptonica
    
    # Additional Tesseract language data for version 5
    pkgs.tesseract5.languages.eng
    pkgs.tesseract5.languages.spa  
    pkgs.tesseract5.languages.fra
    pkgs.tesseract5.languages.deu
    pkgs.tesseract5.languages.ita
    pkgs.tesseract5.languages.chi_sim
    pkgs.tesseract5.languages.osd
  ];
  
  env = {
    PYTHON_LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
      pkgs.libjpeg
      pkgs.libpng
      pkgs.libtiff
      pkgs.zlib
      pkgs.freetype
      pkgs.fontconfig
      pkgs.leptonica
    ];
    TESSDATA_PREFIX = "${pkgs.tesseract5}/share/tessdata";
    PATH = "${pkgs.tesseract5}/bin:${pkgs.ghostscript}/bin:${pkgs.qpdf}/bin:$PATH";
  };
}
