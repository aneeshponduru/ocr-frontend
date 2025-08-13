{ pkgs }: {
  deps = [
    pkgs.python311Full
    pkgs.replitPackages.prybar-python311
    pkgs.replitPackages.stderred

    # OCR dependencies
    pkgs.tesseract4
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
    
    # Additional Tesseract language data
    pkgs.tesseract4.languages.eng
    pkgs.tesseract4.languages.spa
    pkgs.tesseract4.languages.fra
    pkgs.tesseract4.languages.deu
    pkgs.tesseract4.languages.ita
    pkgs.tesseract4.languages.chi_sim
    pkgs.tesseract4.languages.osd
  ];
  
  env = {
    PYTHON_LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
      pkgs.libjpeg
      pkgs.libpng
      pkgs.libtiff
      pkgs.zlib
      pkgs.freetype
      pkgs.fontconfig
    ];
    TESSDATA_PREFIX = "${pkgs.tesseract4}/share/tessdata";
  };
}
