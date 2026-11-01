PRESETS={
    'Personalizzato':{},
    'Riduci dimensione':{'quality':65,'width':1280,'height':720,'bitrate':'128k','fps':30},
    'Alta qualità':{'quality':98,'width':None,'height':None,'bitrate':'320k','fps':None},
    'Solo audio':{'audio_only':True,'bitrate':'192k'},
    'Immagini per il web':{'quality':80,'width':1600,'height':1600},
}


def default_format(path,audio_only=False):
    from engine import kind,FORMATS
    category=kind(path)
    preferred={'image':'jpg','raw':'jpg','vector':'png','audio':'mp3','video':'mp3' if audio_only else 'mp4',
               'text':'txt','docx':'pdf','office':'pdf','presentation':'pdf','spreadsheet':'xlsx','legacy_sheet':'xlsx',
               'table':'csv','pdf':'txt','archive':'zip','web':'txt','ebook':'txt','subtitle':'srt'}
    return preferred.get(category,FORMATS.get(category,('',))[0])
