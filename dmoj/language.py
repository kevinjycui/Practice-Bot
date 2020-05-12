class Language:

    languages = ["ADA", "GAS64", "GAS32", "AWK", "BF", "C", "C#", "C++03", "C++11", "C++14", "C++17", "C11", "Clang", "Clang++", "CBL", "COFFEE", "D", "DART", "F#", "FORTH", "F95", "GO", "Groovy", "HASK", "ICK", "JAVA11", "JAVA8", "KOTLIN", "Lisp", "LUA", "NASM", "NASM64", "OCAML", "PAS", "PERL", "PHP", "PIKE", "PRO", "PYPY2", "PYPY3", "PY2", "PY3", "RKT", "RUBY2", "RUST", "SCALA", "SCM", "SED", "SWIFT", "TCL", "TEXT", "TUR", "V8JS", "VB"]
    languageIds = [42, 58, 56, 43, 30, 9, 14, 2, 13, 33, 69, 72, 35, 36, 39, 45, 29, 37, 40, 49, 19, 16, 64, 15, 50, 74, 25, 67, 70, 22, 20, 62, 23, 10, 6, 5, 68, 47, 17, 18, 1, 8, 63, 21, 44, 52, 41, 60, 54, 38, 51, 24, 27, 34]

    languageToId = {}
    for i, lang in enumerate(languages):
        languageToId[lang] = languageIds[i]

    def getId(self, lang):
        return self.languageToId[lang.upper()]

    def getLanguages(self):
        return self.languages

    def languageExists(self, lang):
        return lang in self.languages