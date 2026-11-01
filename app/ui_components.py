"""Desktop layout built from native Qt widgets."""
from PyQt6.QtWidgets import (QWidget,QFrame,QLabel,QPushButton,QVBoxLayout,QHBoxLayout,QGridLayout,
    QComboBox,QSpinBox,QCheckBox,QTableWidget,QHeaderView,QAbstractItemView,QLineEdit,QScrollArea,
    QSplitter,QStackedWidget,QProgressBar,QSizePolicy,QButtonGroup,QFileDialog)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from ui_icons import pixmap


def label(text='', name='muted', parent=None):
    item=QLabel(text,parent);item.setObjectName(name);item.setTextFormat(Qt.TextFormat.PlainText)
    return item


def box(name='card'):
    frame=QFrame();frame.setObjectName(name)
    return frame


def field(title, control, layout):
    layout.addWidget(label(title,'fieldLabel'))
    layout.addWidget(control)


def spin(low,high,value):
    control=QSpinBox();control.setRange(low,high);control.setValue(value)
    return control


class DropZone(QFrame):
    filesDropped=pyqtSignal(list)
    def __init__(self):
        super().__init__();self.setObjectName('dropZone');self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor);self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName('Aggiungi file: premi Invio oppure trascina i file')
        layout=QHBoxLayout(self);layout.setContentsMargins(24,22,24,22);layout.setSpacing(18)
        self.symbol=label();self.symbol.setFixedSize(48,48);self.symbol.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.symbol)
        texts=QVBoxLayout();texts.setSpacing(5)
        texts.addWidget(label('Trascina i file qui','dropTitle'))
        texts.addWidget(label('Oppure clicca per scegliere dal computer.','muted'))
        layout.addLayout(texts);layout.addStretch()
        self.badge=label('SELEZIONE MULTIPLA','pill');layout.addWidget(self.badge)
    def set_dragging(self,value):
        self.setProperty('dragging',value);self.style().unpolish(self);self.style().polish(self);self.update()
    def dragEnterEvent(self,event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction();self.set_dragging(True)
    def dragLeaveEvent(self,event):
        self.set_dragging(False)
    def dropEvent(self,event):
        paths=[u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        if paths:
            self.filesDropped.emit(paths);event.acceptProposedAction()
        self.set_dragging(False)
    def choose_files(self):
        paths,_=QFileDialog.getOpenFileNames(self,'Scegli uno o più file')
        if paths:self.filesDropped.emit(paths)
    def mousePressEvent(self,event):
        if event.button()==Qt.MouseButton.LeftButton:self.choose_files()
    def keyPressEvent(self,event):
        if event.key() in (Qt.Key.Key_Return,Qt.Key.Key_Enter,Qt.Key.Key_Space):self.choose_files()
        else:super().keyPressEvent(event)


def build_interface(w):
    root=QWidget();root.setObjectName('appRoot');w.setCentralWidget(root)
    shell=QHBoxLayout(root);shell.setContentsMargins(0,0,0,0);shell.setSpacing(0)
    w.sidebar=box('sidebar');w.sidebar.setFixedWidth(200)
    nav=QVBoxLayout(w.sidebar);nav.setContentsMargins(16,28,16,22);nav.setSpacing(8)
    brand=QHBoxLayout();brand.setSpacing(8)
    w.brand_icon=label();w.brand_icon.setFixedSize(28,28)
    brand.addWidget(w.brand_icon);brand.addWidget(label('Converti','brand'));nav.addLayout(brand)
    nav.addWidget(label('UNIVERSALE  /  2.1','caption'));nav.addSpacing(30)
    nav.addWidget(label('LA TUA CODA','eyebrow'))
    w.nav_group=QButtonGroup(w);w.nav_group.setExclusive(True);w.nav_buttons={}
    for key,title,symbol in [('all','Tutti i file','files'),('image','Immagini','image'),('media','Audio e video','media'),('document','Documenti','document'),('data','Tabelle e dati','document'),('archive','Archivi','archive')]:
        button=QPushButton(title);button.setObjectName('nav');button.setCheckable(True);button.setIconSize(QSize(20,20))
        button.setProperty('icon_name',symbol);w.nav_buttons[key]=button;w.nav_group.addButton(button)
        button.clicked.connect(lambda checked=False,k=key:w.set_category(k));nav.addWidget(button)
    w.nav_buttons['all'].setChecked(True);nav.addStretch()
    w.tools_btn=QPushButton('Componenti');w.tools_btn.setObjectName('quiet');w.tools_btn.setProperty('icon_name','settings')
    w.tools_btn.clicked.connect(w.check_dependencies);nav.addWidget(w.tools_btn)
    w.update_btn=QPushButton('Aggiornamenti');w.update_btn.setObjectName('quiet');w.update_btn.clicked.connect(w.open_updates);nav.addWidget(w.update_btn)
    w.theme_btn=QPushButton('Tema chiaro');w.theme_btn.setObjectName('theme');w.theme_btn.clicked.connect(w.toggle_theme);nav.addWidget(w.theme_btn)
    nav.addSpacing(12)
    footer=label('I tuoi file restano\nsul tuo computer.','caption');footer.setWordWrap(True);nav.addWidget(footer)
    shell.addWidget(w.sidebar)

    content=QWidget();main=QVBoxLayout(content);main.setContentsMargins(28,26,28,22);main.setSpacing(20)
    heading=QHBoxLayout();texts=QVBoxLayout();texts.setSpacing(7)
    w.hero_title=label('I tuoi file, nel formato giusto.','title');w.hero_title.setWordWrap(True);texts.addWidget(w.hero_title)
    w.hero_subtitle=label('Converti, organizza e verifica. Tutto sul tuo computer.');w.hero_subtitle.setWordWrap(True);texts.addWidget(w.hero_subtitle)
    heading.addLayout(texts,1)
    w.catalog_btn=QPushButton('Formati');w.catalog_btn.clicked.connect(w.open_catalog);heading.addWidget(w.catalog_btn)
    w.compact_tools=QPushButton('Componenti');w.compact_tools.setProperty('icon_name','settings');w.compact_tools.clicked.connect(w.check_dependencies)
    heading.addWidget(w.compact_tools)
    w.compact_updates=QPushButton('Aggiorna');w.compact_updates.clicked.connect(w.open_updates);heading.addWidget(w.compact_updates)
    w.compact_theme=QPushButton();w.compact_theme.setFixedWidth(42);w.compact_theme.clicked.connect(w.toggle_theme)
    heading.addWidget(w.compact_theme)
    w.open_btn=QPushButton('Aggiungi file');w.open_btn.setObjectName('primary');w.open_btn.setProperty('icon_name','plus');w.open_btn.clicked.connect(w.open_files)
    heading.addWidget(w.open_btn);main.addLayout(heading)
    stats=QHBoxLayout();stats.setSpacing(12);w.stat_values={}
    for key,title in [('loaded','FILE CARICATI'),('selected','SELEZIONATI'),('success','CONVERTITI'),('error','ERRORI')]:
        card=box();item=QHBoxLayout(card);item.setContentsMargins(16,12,16,12)
        item.addWidget(label(title,'eyebrow'));item.addStretch()
        value=label('0','statValue');w.stat_values[key]=value;item.addWidget(value);stats.addWidget(card)
    main.addLayout(stats)
    w.splitter=QSplitter(Qt.Orientation.Horizontal);w.splitter.setChildrenCollapsible(False);w.splitter.setHandleWidth(16)
    workspace=QWidget();work=QVBoxLayout(workspace);work.setContentsMargins(0,0,0,0);work.setSpacing(16)
    w.drop_zone=DropZone();w.drop_zone.filesDropped.connect(w.add_files);work.addWidget(w.drop_zone)
    queue=box();q=QVBoxLayout(queue);q.setContentsMargins(16,16,16,14);q.setSpacing(12)
    queue_top=QHBoxLayout();w.queue_title=label('Coda di conversione','sectionTitle');queue_top.addWidget(w.queue_title);queue_top.addStretch()
    w.compact_category=QComboBox();w.compact_category.setMaximumWidth(150)
    for name,key in [('Tutti i file','all'),('Immagini','image'),('Audio / video','media'),('Documenti','document'),('Tabelle e dati','data'),('Archivi','archive')]:w.compact_category.addItem(name,key)
    w.compact_category.currentIndexChanged.connect(lambda _:w.set_category(w.compact_category.currentData()))
    queue_top.addWidget(w.compact_category)
    w.status_filter=QComboBox()
    for title,value in [('Tutti gli stati','all'),('Da convertire','pending'),('Completati','done'),('Errori','error')]:w.status_filter.addItem(title,value)
    w.status_filter.setAccessibleName('Filtra per stato della conversione');w.status_filter.currentIndexChanged.connect(w.apply_filter)
    queue_top.addWidget(w.status_filter)
    w.queue_badge=label('0 file','pill');queue_top.addWidget(w.queue_badge);q.addLayout(queue_top)
    actions=QHBoxLayout()
    w.search=QLineEdit();w.search.setPlaceholderText('Cerca nella coda…');w.search.setClearButtonEnabled(True);w.search.textChanged.connect(w.apply_filter)
    w.search.setMinimumWidth(140);actions.addWidget(w.search,1)
    w.remove_btn=QPushButton('Rimuovi');w.remove_btn.setObjectName('quiet');w.remove_btn.setProperty('icon_name','trash');w.remove_btn.setToolTip('Rimuovi i file selezionati dalla coda')
    w.remove_btn.clicked.connect(w.remove_files);actions.addWidget(w.remove_btn)
    w.clear_btn=QPushButton('Svuota');w.clear_btn.setObjectName('quiet');w.clear_btn.setProperty('icon_name','close');w.clear_btn.clicked.connect(w.clear_files);actions.addWidget(w.clear_btn)
    w.retry_btn=QPushButton('Riprova');w.retry_btn.setObjectName('quiet')
    w.retry_btn.setToolTip('Riprova errori e file annullati dell’ultima coda con le stesse impostazioni')
    w.retry_btn.setEnabled(False);w.retry_btn.clicked.connect(w.retry_failed);actions.addWidget(w.retry_btn)
    q.addLayout(actions)
    w.queue_stack=QStackedWidget();w.table=QTableWidget(0,4)
    w.table.setHorizontalHeaderLabels(['FILE','TIPO','DIMENSIONE','STATO']);w.table.setAlternatingRowColors(True)
    w.table.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeMode.Stretch)
    for col in (1,2,3):w.table.horizontalHeader().setSectionResizeMode(col,QHeaderView.ResizeMode.ResizeToContents)
    w.table.verticalHeader().setVisible(False);w.table.verticalHeader().setDefaultSectionSize(52)
    w.table.setShowGrid(False);w.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    w.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection);w.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    w.table.setIconSize(QSize(24,24));w.table.setMinimumHeight(150)
    w.table.itemSelectionChanged.connect(w.selection_changed);w.table.itemDoubleClicked.connect(w.details)
    empty=QWidget();empty_layout=QVBoxLayout(empty);empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter);empty_layout.setSpacing(12)
    w.empty_icon=label();w.empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter);empty_layout.addWidget(w.empty_icon)
    t=label('La tua coda parte da qui','sectionTitle');t.setAlignment(Qt.AlignmentFlag.AlignCenter);empty_layout.addWidget(t)
    t=label('Aggiungi uno o più file e scegli il formato di destinazione.');t.setWordWrap(True);t.setAlignment(Qt.AlignmentFlag.AlignCenter);empty_layout.addWidget(t)
    w.queue_stack.addWidget(empty);w.queue_stack.addWidget(w.table);q.addWidget(w.queue_stack,1)
    w.no_results=label('Nessun file corrisponde alla ricerca.');w.no_results.setAlignment(Qt.AlignmentFlag.AlignCenter);w.no_results.hide();q.addWidget(w.no_results)
    w.queue_summary=label('Seleziona più file con Ctrl o Shift.','caption');q.addWidget(w.queue_summary)
    work.addWidget(queue,1)
    progress_card=box('progressCard');progress_layout=QVBoxLayout(progress_card);progress_layout.setContentsMargins(16,14,16,14);progress_layout.setSpacing(10)
    row=QHBoxLayout();row.addWidget(label('STATO DELLA CODA','eyebrow'));row.addStretch();w.progress_caption=label('Pronto','caption');row.addWidget(w.progress_caption);progress_layout.addLayout(row)
    w.progress=QProgressBar();w.progress.setRange(0,1);w.progress.setValue(0);w.progress.setTextVisible(False);w.progress.setFixedHeight(6);progress_layout.addWidget(w.progress)
    w.status=label('Aggiungi i file per iniziare.');w.status.setWordWrap(True);w.status.setSizePolicy(QSizePolicy.Policy.Ignored,QSizePolicy.Policy.Preferred);progress_layout.addWidget(w.status)
    work.addWidget(progress_card);w.splitter.addWidget(workspace)

    w.settings_card=box('settingsCard');w.settings_card.setMinimumWidth(304);w.settings_card.setMaximumWidth(370)
    settings=QVBoxLayout(w.settings_card);settings.setContentsMargins(18,20,18,18);settings.setSpacing(14)
    row=QHBoxLayout();row.addWidget(label('Impostazioni','sectionTitle'));row.addStretch();w.selection_badge=label('0 file','pill');row.addWidget(w.selection_badge);settings.addLayout(row)
    w.preview=label(name='preview');w.preview.setAlignment(Qt.AlignmentFlag.AlignCenter);w.preview.setFixedHeight(94);settings.addWidget(w.preview)
    w.selection_summary=label('Nessun file selezionato','selectionSummary');w.selection_summary.setWordWrap(True);settings.addWidget(w.selection_summary)
    w.selection_detail=label('Scegli una riga dalla coda.','caption');w.selection_detail.setWordWrap(True);settings.addWidget(w.selection_detail)
    w.options_scroll=QScrollArea();w.options_scroll.setWidgetResizable(True);w.options_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    options=QWidget();options_layout=QVBoxLayout(options);options_layout.setContentsMargins(0,0,4,0);options_layout.setSpacing(12)
    w.format_combo=QComboBox();w.format_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon);w.format_combo.setMinimumContentsLength(10)
    field('FORMATO DI DESTINAZIONE',w.format_combo,options_layout)
    w.media_options=QWidget();media=QVBoxLayout(w.media_options);media.setContentsMargins(0,0,0,0);media.setSpacing(8)
    w.resize_check=QCheckBox('Ridimensiona');w.resize_check.setToolTip('Mantiene le proporzioni dell’immagine o del video.');media.addWidget(w.resize_check)
    w.width_spin=spin(1,10000,1920);w.height_spin=spin(1,10000,1080)
    sizes=QHBoxLayout();sizes.addWidget(w.width_spin);sizes.addWidget(label('×'));sizes.addWidget(w.height_spin);media.addLayout(sizes)
    w.width_spin.setAccessibleName('Larghezza in pixel');w.height_spin.setAccessibleName('Altezza in pixel')
    w.quality_spin=spin(1,100,90);w.quality_spin.setSuffix('%');field('Qualità',w.quality_spin,media)
    options_layout.addWidget(w.media_options)
    w.audio_options=QWidget();audio=QGridLayout(w.audio_options);audio.setContentsMargins(0,0,0,0);audio.setVerticalSpacing(10)
    w.bitrate_label=label('Bitrate audio','fieldLabel');w.bitrate_combo=QComboBox();w.bitrate_combo.addItems(['128k','192k','256k','320k']);w.bitrate_combo.setCurrentText('192k')
    w.speed_label=label('Velocità audio','fieldLabel');w.speed_spin=spin(50,200,100);w.speed_spin.setSuffix('%')
    w.fps_label=label('FPS video','fieldLabel');w.fps_spin=spin(0,240,0);w.fps_spin.setSpecialValueText('Originale')
    for index,(name,control) in enumerate([(w.bitrate_label,w.bitrate_combo),(w.speed_label,w.speed_spin),(w.fps_label,w.fps_spin)]):audio.addWidget(name,index,0);audio.addWidget(control,index,1)
    options_layout.addWidget(w.audio_options)
    w.table_options=QWidget();table=QVBoxLayout(w.table_options);table.setContentsMargins(0,0,0,0);w.sheet_spin=spin(1,10000,1);field('Foglio Excel (numero)',w.sheet_spin,table);options_layout.addWidget(w.table_options)
    w.ocr_options=QWidget();ocr=QVBoxLayout(w.ocr_options);ocr.setContentsMargins(0,0,0,0);ocr.setSpacing(8)
    w.ocr_check=QCheckBox('PDF scansionato: usa OCR');ocr.addWidget(w.ocr_check)
    w.language_combo=QComboBox()
    for name,code in [('Italiano + inglese','ita+eng'),('Italiano','ita'),('Inglese','eng')]:w.language_combo.addItem(name,code)
    field('Lingua del testo',w.language_combo,ocr);options_layout.addWidget(w.ocr_options)
    w.pdf_options=QWidget();pdf=QVBoxLayout(w.pdf_options);pdf.setContentsMargins(0,0,0,0);w.dpi_spin=spin(72,300,150);w.dpi_spin.setSuffix(' DPI');field('Risoluzione delle pagine',w.dpi_spin,pdf);options_layout.addWidget(w.pdf_options)
    w.format_hint=label(name='hint');w.format_hint.setWordWrap(True);options_layout.addWidget(w.format_hint)
    options_layout.addStretch();w.options_scroll.setWidget(options);settings.addWidget(w.options_scroll,1)
    w.convert_btn=QPushButton('Converti selezionati');w.convert_btn.setObjectName('primary');w.convert_btn.setProperty('icon_name','arrow');w.convert_btn.setMinimumHeight(44);w.convert_btn.clicked.connect(w.start_conversion);settings.addWidget(w.convert_btn)
    row=QHBoxLayout();w.cancel_btn=QPushButton('Ferma coda');w.cancel_btn.setProperty('icon_name','stop');w.cancel_btn.setEnabled(False);w.cancel_btn.clicked.connect(w.cancel_queue);row.addWidget(w.cancel_btn)
    w.folder_btn=QPushButton('Risultati');w.folder_btn.setProperty('icon_name','folder');w.folder_btn.setEnabled(False);w.folder_btn.clicked.connect(w.open_results);row.addWidget(w.folder_btn);settings.addLayout(row)
    w.splitter.addWidget(w.settings_card);w.splitter.setStretchFactor(0,1);w.splitter.setSizes([670,320]);main.addWidget(w.splitter,1)
    shell.addWidget(content,1)
    w.format_combo.currentIndexChanged.connect(w.format_changed)
    w.progress.valueChanged.connect(w.update_progress_caption)
