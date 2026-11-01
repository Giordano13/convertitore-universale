# Interfaccia 1.1

La gerarchia mette al primo posto l'azione «Aggiungi file», poi la coda e
le impostazioni della selezione. Le azioni di rimozione hanno un'enfasi
minore delle azioni di conversione. I colori di successo/errore sono
accompagnati da icone e testo.

Spazi regolari, superfici distinte, bordi arrotondati e un accento viola.
Tema chiaro e scuro condividono la stessa disposizione. I controlli
rimangono widget Qt reali, utilizzabili con mouse e tastiera.

File della grafica:
- ui_components.py: disposizione dei pannelli e controlli.
- ui_theme.py: palette e stili QSS.
- ui_icons.py: icone vettoriali originali, renderizzate con Qt SVG.
- assets/: frecce e segni di spunta SVG dei controlli.

Riferimenti consultati:
- Microsoft, Content layout and spacing:
  https://learn.microsoft.com/en-us/windows/apps/design/basics/content-basics
- Microsoft, Design guidelines:
  https://learn.microsoft.com/en-us/windows/apps/design/guidelines-overview
- Qt, Style Sheets Reference:
  https://doc.qt.io/qt-6/stylesheet-reference.html

Le anteprime sono schermate dell'app con file di prova. Le dipendenze
FFmpeg, LibreOffice e Tesseract sono descritte nel README.
