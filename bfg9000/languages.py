from .iterutils import iterate

ext2lang = {}


def lang_exts(lang, exts):
    for i in iterate(exts):
        if i in ext2lang:
            raise ValueError('{ext} already used by {lang}'.format(
                ext=i, lang=lang
            ))
        ext2lang[i] = lang
