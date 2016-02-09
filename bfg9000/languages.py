from .iterutils import iterate

ext2lang = {}
lang_link = {}


def language(lang, exts, link):
    for i in iterate(exts):
        if i in ext2lang:
            raise ValueError('{ext} already used by {lang}'.format(
                ext=i, lang=lang
            ))
        ext2lang[i] = lang
    lang_link[lang] = link
