"""
GUI Model layer.
GUIアプリケーションの状態と変換オプションを管理する。
View/Controllerから分離されたデータモデル。
"""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ConversionConfig:
    """変換設定を保持するデータクラス."""
    input_dir: str = ""
    output_dir: str = ""
    package_name: str = "com.migrated"
    encoding: str = "utf-8"
    extensions: str = ".cbl,.cob,.cobol,.CBL,.COB"
    vendor: str = "auto"

    # Generation options
    generate_getters_setters: bool = True
    use_big_decimal: bool = True
    generate_javadoc: bool = True
    generate_toString: bool = True
    extract_data_classes: bool = True
    extract_enums: bool = True
    extract_services: bool = True
    extract_file_handlers: bool = True

    def get_extension_list(self) -> List[str]:
        return [e.strip() for e in self.extensions.split(",")]


@dataclass
class ConversionState:
    """変換処理の実行状態."""
    is_running: bool = False
    cancel_flag: bool = False
    progress: float = 0.0
    current_file: str = ""
    success_count: int = 0
    error_count: int = 0

    def reset(self):
        self.is_running = False
        self.cancel_flag = False
        self.progress = 0.0
        self.current_file = ""
        self.success_count = 0
        self.error_count = 0


VENDOR_OPTIONS = [
    ("auto", "Auto Detect"),
    ("standard", "COBOL Standard"),
    ("ibm", "IBM Enterprise COBOL"),
    ("fujitsu", "Fujitsu NetCOBOL"),
    ("nec", "NEC ACOS COBOL"),
    ("hitachi", "Hitachi VOS3 COBOL"),
    ("microfocus", "Micro Focus Visual COBOL"),
    ("unisys", "Unisys MCP/ClearPath"),
    ("bull", "Bull/Atos GCOS"),
    ("hp", "HP NonStop COBOL"),
    ("gnucobol", "GnuCOBOL"),
]
