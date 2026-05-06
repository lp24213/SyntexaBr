class CodeValidator:
    """
    Validador simples de código: aplica filtros básicos antes da execução.
    """

    def is_safe_python(self, code: str) -> bool:
        """
        Filtro defensivo (não é segurança perfeita).
        Objetivo: impedir IO/FS/rede/processos/reflexão óbvia antes de executar em subprocesso.
        """
        lowered = (code or "").lower()
        banned = [
            # sistema/processos/FS
            "import os",
            "from os",
            "import sys",
            "from sys",
            "subprocess",
            "shutil",
            "pathlib",
            "open(",
            "path(",
            # reflexão/execução dinâmica
            "__import__(",
            "eval(",
            "exec(",
            "compile(",
            "globals(",
            "locals(",
            "vars(",
            "getattr(",
            "setattr(",
            "delattr(",
            # rede/HTTP
            "import socket",
            "from socket",
            "requests",
            "urllib",
            "http.client",
            "ftplib",
            # serialização perigosa
            "pickle",
            "marshal",
            # bindings nativos
            "ctypes",
            "cffi",
            # paralelismo que foge do timeout
            "multiprocessing",
            "threading",
            "asyncio",
        ]
        return not any(bad in lowered for bad in banned)

