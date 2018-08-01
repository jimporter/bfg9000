from .iterutils import iterate

lang2cmd = {}
lang2flags = {}

lang2src = {}
lang2hdr = {}

src2lang = {}
hdr2lang = {}


def language(lang, cmd_var=None, flags_var=None, src_exts=[], hdr_exts=[]):
    if cmd_var:
        lang2cmd[lang] = cmd_var
    if flags_var:
        lang2flags[lang] = flags_var

    for exts, fromlang, tolang in ((src_exts, lang2src, src2lang),
                                   (hdr_exts, lang2hdr, hdr2lang)):
        if lang not in fromlang:
            fromlang[lang] = []
        fromlang[lang].extend(exts)

        for i in iterate(exts):
            if i in tolang:
                raise ValueError('{ext} already used by {lang}'.format(
                    ext=i, lang=lang
                ))
            tolang[i] = lang
