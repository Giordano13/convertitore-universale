"""Additional controls live in the existing scrollable settings panel."""
from PyQt6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QComboBox,QCheckBox,
 QLineEdit,QSpinBox,QDoubleSpinBox,QHeaderView,QMenu)
from ui_components import field,spin
from presets import PRESETS

def add_features(w):
    layout=w.options_scroll.widget().layout()
    w.preset_combo=QComboBox();w.preset_combo.addItems(PRESETS)
    for name in w.store.recipes():w.preset_combo.addItem('Sequenza: '+name)
    layout.insertWidget(0,QLabel('PRESET / SEQUENZA'));layout.insertWidget(1,w.preset_combo)
    w.preset_combo.currentTextChanged.connect(w.apply_preset)
    w.mixed_check=QCheckBox('Formato diverso per ogni file');layout.insertWidget(2,w.mixed_check)
    w.mixed_check.toggled.connect(w.selection_changed)
    w.mixed_check.toggled.connect(lambda checked:w.table.setColumnHidden(4,not checked))
    w.table.setColumnCount(5);w.table.setHorizontalHeaderLabels(['FILE','TIPO','DIMENSIONE','STATO','FORMATO'])
    w.table.horizontalHeader().setSectionResizeMode(4,QHeaderView.ResizeMode.ResizeToContents)
    w.table.setColumnHidden(4,True)
    w.advanced_toggle=QPushButton('Impostazioni avanzate ▾');w.advanced_toggle.setCheckable(True)
    layout.insertWidget(layout.count()-1,w.advanced_toggle)
    w.advanced=QWidget();extra=QVBoxLayout(w.advanced);extra.setContentsMargins(0,0,0,0);extra.setSpacing(10)
    w.metadata_combo=QComboBox();w.metadata_combo.addItem('Rimuovi EXIF / metadati','remove');w.metadata_combo.addItem('Conserva metadati compatibili','keep')
    field('Metadati immagini / media',w.metadata_combo,extra)
    w.target_mb=QDoubleSpinBox();w.target_mb.setRange(0,100000);w.target_mb.setSpecialValueText('Disattivato');w.target_mb.setSuffix(' MB');field('Peso video indicativo',w.target_mb,extra)
    w.denoise_check=QCheckBox('Riduci rumore video');extra.addWidget(w.denoise_check)
    row=QHBoxLayout();w.trim_start=QDoubleSpinBox();w.trim_end=QDoubleSpinBox()
    for name,control in [('Da',w.trim_start),('A',w.trim_end)]:
        control.setRange(0,864000);control.setDecimals(2);control.setSuffix(' s');row.addWidget(QLabel(name));row.addWidget(control)
    w.trim_end.setSpecialValueText('Fine');extra.addWidget(QLabel('Taglio audio / video'));extra.addLayout(row)
    w.crop_check=QCheckBox('Ritaglia immagine (pixel)');extra.addWidget(w.crop_check)
    row=QHBoxLayout();w.crop_spins=[]
    for name,value in [('X',0),('Y',0),('L',500),('H',500)]:
        item=spin(0 if name in ('X','Y') else 1,100000,value);item.setPrefix(name+' ');item.setAccessibleName('Ritaglio '+name);w.crop_spins.append(item);row.addWidget(item)
    extra.addLayout(row)
    w.watermark_text=QLineEdit();w.watermark_text.setPlaceholderText('Testo filigrana (facoltativo)');extra.addWidget(w.watermark_text)
    w.watermark_logo=QLineEdit();w.watermark_logo.setPlaceholderText('Percorso logo PNG');row=QHBoxLayout();row.addWidget(w.watermark_logo)
    logo=QPushButton('Scegli');logo.clicked.connect(w.choose_logo);row.addWidget(logo);extra.addLayout(row)
    w.watermark_opacity=spin(0,100,70);w.watermark_opacity.setSuffix('%');field('Opacità filigrana',w.watermark_opacity,extra)
    w.naming_check=QCheckBox('Rinomina risultati');extra.addWidget(w.naming_check)
    w.naming_pattern=QLineEdit('{name}_{n:03d}');field('Schema: {name}, {n}, {n:03d}',w.naming_pattern,extra)
    w.preserve_check=QCheckBox('Conserva sottocartelle importate');w.preserve_check.setChecked(True);extra.addWidget(w.preserve_check)
    # These controls remain accessible even when the selected format is not OCR.
    language=QComboBox()
    for i in range(w.language_combo.count()):language.addItem(w.language_combo.itemText(i),w.language_combo.itemData(i))
    language.currentIndexChanged.connect(w.language_combo.setCurrentIndex);w.language_combo.currentIndexChanged.connect(language.setCurrentIndex)
    field('Lingua OCR degli strumenti PDF',language,extra)
    dpi=spin(72,300,w.dpi_spin.value());dpi.valueChanged.connect(w.dpi_spin.setValue);w.dpi_spin.valueChanged.connect(dpi.setValue);field('DPI OCR / PDF',dpi,extra)
    save=QPushButton('Salva come sequenza');save.clicked.connect(w.save_recipe);extra.addWidget(save)
    note=QLabel('Sequenza immagini: ritaglio → ridimensionamento → filigrana → conversione. Il peso video è una stima, non un limite esatto.');note.setWordWrap(True);extra.addWidget(note)
    layout.insertWidget(layout.count()-1,w.advanced);w.advanced.hide();w.advanced_toggle.toggled.connect(w.advanced.setVisible)
    bar=QHBoxLayout();w.feature_buttons=[]
    for text,callback in [('Cartella',w.open_folder),('Strumenti',w.open_tools),('Cronologia',w.open_history),('Confronta',w.open_comparison),('Info',w.open_info),('SHA-256',w.verify_file)]:
        button=QPushButton(text);button.clicked.connect(callback);bar.addWidget(button);w.feature_buttons.append(button)
    w.drop_zone.parentWidget().layout().insertLayout(1,bar)
    w.watch_btn=QPushButton('Sorveglia cartella');w.watch_btn.clicked.connect(w.toggle_watch)
    layout.insertWidget(3,w.watch_btn)
    w.support_btn=QPushButton('Sostieni il progetto');w.support_btn.clicked.connect(w.open_support)
    w.support_btn.setToolTip('Una donazione volontaria aiuta lo sviluppo del convertitore.')
    extra.addWidget(w.support_btn)
