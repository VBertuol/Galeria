"""Textos do programa nas 11 línguas. O padrão é inglês; a pessoa troca no menu da bandeja.

Os nomes das obras, dos artistas e dos museus não estão aqui: vêm do Wikidata, em `acervo.json`.
Traduções feitas por IA (Claude) em 2026-10-15, sem revisão de falante nativo; correção é bem-vinda.
"""

PADRAO = "en"

# Ordem do menu e o nome de cada língua nela mesma.
LINGUAS = [
    ("en", "English"),
    ("pt", "Português (Brasil)"),
    ("es", "Español"),
    ("fr", "Français"),
    ("de", "Deutsch"),
    ("it", "Italiano"),
    ("zh", "中文（简体）"),
    ("ja", "日本語"),
    ("ar", "العربية"),
    ("ko", "한국어"),
    ("ru", "Русский"),
]

TEXTOS = {
    "en": {
        "sobre": "About this artwork", "proxima": "Next artwork", "pausar": "Pause",
        "trocar": "Change every", "lingua": "Language", "sair": "Quit",
        "nenhuma": "No artwork yet", "desconhecido": "Unknown artist",
        "sem_internet": "No internet connection and no saved artworks yet.",
        "erro": "Could not change the artwork: {erro}",
        "intervalos": ["30 seconds", "1 minute", "2 minutes", "5 minutes", "15 minutes", "30 minutes",
                       "1 hour", "3 hours", "1 day"],
    },
    "pt": {
        "sobre": "Sobre esta obra", "proxima": "Próxima obra", "pausar": "Pausar",
        "trocar": "Trocar a cada", "lingua": "Idioma", "sair": "Sair",
        "nenhuma": "Nenhuma obra ainda", "desconhecido": "Autor desconhecido",
        "sem_internet": "Sem internet e nenhuma obra guardada ainda.",
        "erro": "Não consegui trocar a obra: {erro}",
        "intervalos": ["30 segundos", "1 minuto", "2 minutos", "5 minutos", "15 minutos", "30 minutos",
                       "1 hora", "3 horas", "1 dia"],
    },
    "es": {
        "sobre": "Acerca de esta obra", "proxima": "Siguiente obra", "pausar": "Pausar",
        "trocar": "Cambiar cada", "lingua": "Idioma", "sair": "Salir",
        "nenhuma": "Todavía no hay ninguna obra", "desconhecido": "Autor desconocido",
        "sem_internet": "Sin conexión a internet y sin obras guardadas todavía.",
        "erro": "No se pudo cambiar la obra: {erro}",
        "intervalos": ["30 segundos", "1 minuto", "2 minutos", "5 minutos", "15 minutos", "30 minutos",
                       "1 hora", "3 horas", "1 día"],
    },
    "fr": {
        "sobre": "À propos de cette œuvre", "proxima": "Œuvre suivante", "pausar": "Pause",
        "trocar": "Changer toutes les", "lingua": "Langue", "sair": "Quitter",
        "nenhuma": "Aucune œuvre pour l'instant", "desconhecido": "Artiste inconnu",
        "sem_internet": "Pas de connexion Internet et aucune œuvre enregistrée pour l'instant.",
        "erro": "Impossible de changer l'œuvre : {erro}",
        "intervalos": ["30 secondes", "1 minute", "2 minutes", "5 minutes", "15 minutes", "30 minutes",
                       "1 heure", "3 heures", "1 jour"],
    },
    "de": {
        "sobre": "Über dieses Kunstwerk", "proxima": "Nächstes Kunstwerk", "pausar": "Pausieren",
        "trocar": "Wechseln alle", "lingua": "Sprache", "sair": "Beenden",
        "nenhuma": "Noch kein Kunstwerk", "desconhecido": "Unbekannter Künstler",
        "sem_internet": "Keine Internetverbindung und noch keine gespeicherten Kunstwerke.",
        "erro": "Das Kunstwerk konnte nicht gewechselt werden: {erro}",
        "intervalos": ["30 Sekunden", "1 Minute", "2 Minuten", "5 Minuten", "15 Minuten", "30 Minuten",
                       "1 Stunde", "3 Stunden", "1 Tag"],
    },
    "it": {
        "sobre": "Informazioni su quest'opera", "proxima": "Opera successiva", "pausar": "Pausa",
        "trocar": "Cambia ogni", "lingua": "Lingua", "sair": "Esci",
        "nenhuma": "Ancora nessuna opera", "desconhecido": "Autore sconosciuto",
        "sem_internet": "Nessuna connessione a Internet e nessuna opera salvata.",
        "erro": "Impossibile cambiare l'opera: {erro}",
        "intervalos": ["30 secondi", "1 minuto", "2 minuti", "5 minuti", "15 minuti", "30 minuti",
                       "1 ora", "3 ore", "1 giorno"],
    },
    "zh": {
        "sobre": "关于这幅作品", "proxima": "下一幅作品", "pausar": "暂停",
        "trocar": "更换间隔", "lingua": "语言", "sair": "退出",
        "nenhuma": "还没有作品", "desconhecido": "佚名",
        "sem_internet": "没有网络连接，也还没有已保存的作品。",
        "erro": "无法更换作品：{erro}",
        "intervalos": ["30 秒", "1 分钟", "2 分钟", "5 分钟", "15 分钟", "30 分钟", "1 小时", "3 小时", "1 天"],
    },
    "ja": {
        "sobre": "この作品について", "proxima": "次の作品", "pausar": "一時停止",
        "trocar": "切り替え間隔", "lingua": "言語", "sair": "終了",
        "nenhuma": "まだ作品がありません", "desconhecido": "作者不詳",
        "sem_internet": "インターネットに接続されておらず、保存された作品もまだありません。",
        "erro": "作品を切り替えられませんでした：{erro}",
        "intervalos": ["30 秒", "1 分", "2 分", "5 分", "15 分", "30 分", "1 時間", "3 時間", "1 日"],
    },
    "ar": {
        "sobre": "عن هذا العمل", "proxima": "العمل التالي", "pausar": "إيقاف مؤقت",
        "trocar": "التغيير كل", "lingua": "اللغة", "sair": "خروج",
        "nenhuma": "لا يوجد عمل بعد", "desconhecido": "فنان مجهول",
        "sem_internet": "لا يوجد اتصال بالإنترنت ولا توجد أعمال محفوظة بعد.",
        "erro": "تعذّر تغيير العمل: {erro}",
        "intervalos": ["30 ثانية", "دقيقة واحدة", "دقيقتان", "5 دقائق", "15 دقيقة", "30 دقيقة",
                       "ساعة واحدة", "3 ساعات", "يوم واحد"],
    },
    "ko": {
        "sobre": "이 작품에 대하여", "proxima": "다음 작품", "pausar": "일시 정지",
        "trocar": "변경 간격", "lingua": "언어", "sair": "종료",
        "nenhuma": "아직 작품이 없습니다", "desconhecido": "작자 미상",
        "sem_internet": "인터넷에 연결되어 있지 않고 저장된 작품도 아직 없습니다.",
        "erro": "작품을 바꾸지 못했습니다: {erro}",
        "intervalos": ["30초", "1분", "2분", "5분", "15분", "30분", "1시간", "3시간", "1일"],
    },
    "ru": {
        "sobre": "Об этом произведении", "proxima": "Следующее произведение", "pausar": "Пауза",
        "trocar": "Менять каждые", "lingua": "Язык", "sair": "Выход",
        "nenhuma": "Произведений пока нет", "desconhecido": "Неизвестный автор",
        "sem_internet": "Нет подключения к интернету и пока нет сохранённых произведений.",
        "erro": "Не удалось сменить произведение: {erro}",
        "intervalos": ["30 секунд", "1 минута", "2 минуты", "5 минут", "15 минут", "30 минут",
                       "1 час", "3 часа", "1 день"],
    },
}

# Fonte do Windows para a legenda: a Segoe UI cobre latim, cirílico e árabe; as do leste asiático
# cobrem também o latim, então um título que caiu para o inglês sai certo nelas.
FONTES = {
    "zh": ("msyhbd.ttc", "msyh.ttc", "msyh.ttc"),
    "ja": ("YuGothB.ttc", "YuGothM.ttc", "YuGothM.ttc"),
    "ko": ("malgunbd.ttf", "malgun.ttf", "malgun.ttf"),
    "ar": ("segoeuib.ttf", "segoeui.ttf", "segoeui.ttf"),  # a Segoe UI itálica não tem árabe
}
FONTES_PADRAO = ("segoeuib.ttf", "segoeui.ttf", "segoeuii.ttf")  # título, autor, museu
DIREITA_PARA_ESQUERDA = {"ar"}
# entre artistas e antes do ano: vírgula árabe no árabe, vírgula de largura cheia no chinês, 、 no japonês
SEPARADOR = {"ar": "، ", "zh": "，", "ja": "、"}


def separador(lingua):
    return SEPARADOR.get(lingua, ", ")


def t(lingua, chave):
    return TEXTOS.get(lingua, TEXTOS[PADRAO]).get(chave, TEXTOS[PADRAO][chave])


def da_obra(campo, lingua):
    """Um campo multilíngue do acervo ({língua: texto}): a língua pedida, senão inglês, senão qualquer uma."""
    if not campo:
        return None
    return campo.get(lingua) or campo.get(PADRAO) or next(iter(campo.values()))
