"""Generate design_document.xlsx for COBOL2Java project."""
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

wb = Workbook()

# === Shared styles ===
HEADER_FONT = Font(name="Arial", bold=True, size=11, color="FFFFFF")
HEADER_FILL = PatternFill("solid", fgColor="2C3E50")
SUB_HEADER_FILL = PatternFill("solid", fgColor="34495E")
SECTION_FILL = PatternFill("solid", fgColor="D5E8D4")
SECTION_FONT = Font(name="Arial", bold=True, size=10)
BODY_FONT = Font(name="Arial", size=10)
THIN_BORDER = Border(
    left=Side(style="thin"), right=Side(style="thin"),
    top=Side(style="thin"), bottom=Side(style="thin"),
)
WRAP = Alignment(wrap_text=True, vertical="top")
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)


def style_header(ws, row, max_col):
    for c in range(1, max_col + 1):
        cell = ws.cell(row=row, column=c)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = CENTER
        cell.border = THIN_BORDER


def style_body(ws, row, max_col):
    for c in range(1, max_col + 1):
        cell = ws.cell(row=row, column=c)
        cell.font = BODY_FONT
        cell.alignment = WRAP
        cell.border = THIN_BORDER


def style_section(ws, row, max_col, label):
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=max_col)
    cell = ws.cell(row=row, column=1, value=label)
    cell.font = SECTION_FONT
    cell.fill = SECTION_FILL
    cell.border = THIN_BORDER


def auto_width(ws, max_col, widths):
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w


# ============================================================
# Sheet 1: 機能一覧表
# ============================================================
ws1 = wb.active
ws1.title = "機能一覧表"
cols1 = ["機能ID", "カテゴリ", "機能名", "概要", "入力", "出力", "対象モジュール", "対象ユーザー"]
ws1.append(cols1)
style_header(ws1, 1, len(cols1))

features = [
    # --- 変換エンジン ---
    ["F-001", "変換エンジン", "COBOLソース解析", "COBOLソースファイルを読み込み、4つのDIVISIONを検出・分割し構造化ASTを生成する。固定形式/自由形式の自動判別、継続行の結合、コメント除去を含む。", ".cbl/.cob/.cobol ファイル", "CobolProgram (AST)", "cobol_parser.py, division_parser.py", "変換実行ユーザー"],
    ["F-002", "変換エンジン", "DATA DIVISION構造化解析", "DATA DIVISIONのデータ項目定義（レベル番号、PIC句、USAGE句、VALUE句、OCCURS句、REDEFINES句）を正規表現ベースの句抽出により解析する。88レベル条件項目にも対応。", "前処理済みソース行", "DataItem リスト", "lark_data_parser.py", "変換実行ユーザー"],
    ["F-003", "変換エンジン", "PROCEDURE DIVISION構造化解析", "PROCEDURE DIVISIONの文をセクション/パラグラフ/文ツリーに構造化する。宣言的動詞レジストリによる文分類と、IF/EVALUATE/READブロックの再帰下降解析を行う。", "前処理済みソース行", "Section/Paragraph/Statement ツリー", "lark_procedure_parser.py", "変換実行ユーザー"],
    ["F-004", "変換エンジン", "OOP変換", "手続き型COBOL ASTをJava OOPモデル（データクラス、列挙型、サービスクラス、ファイルハンドラ）に変換する。グループ項目→クラス、88レベル→Enum、関連パラグラフ→サービス層への自動分離を行う。", "CobolProgram (AST)", "JavaProject (OOPモデル)", "oop_transformer.py", "変換実行ユーザー"],
    ["F-005", "変換エンジン", "Javaソースコード生成", "JavaProjectモデルからパッケージ構造付きの.javaファイルを生成する。import文、Javadoc、getter/setter、toString()、コンストラクタを含む完全なJavaクラスを出力する。", "JavaProject (OOPモデル)", ".java ファイル群", "java_generator.py", "変換実行ユーザー"],
    ["F-006", "変換エンジン", "EXEC SQL変換", "COBOL埋め込みSQL（SELECT/INSERT/UPDATE/DELETE/CURSOR操作/COMMIT/ROLLBACK）をJDBC PreparedStatementまたはJPA EntityManager呼び出しに変換する。ホスト変数のバインド処理を含む。", "ExecBlock (EXEC SQL)", "Java SQLコード", "conversion_strategies.py, vendor_extensions.py", "変換実行ユーザー"],
    ["F-007", "変換エンジン", "EXEC CICS変換", "CICS端末I/O（SEND/RECEIVE MAP）、ファイルI/O（READ/WRITE/REWRITE/DELETE/BROWSE）、プログラム制御（LINK/XCTL/RETURN）、一時記憶域操作を抽象CICSインタフェースにマッピングする。", "ExecBlock (EXEC CICS)", "Java CICSコード", "conversion_strategies.py, vendor_extensions.py", "変換実行ユーザー"],
    ["F-008", "変換エンジン", "EXEC DLI変換", "IMS/DLI呼び出しをTODOコメント付きのJavaコードとして出力する。JPA/Hibernate変換への手動移行を推奨する。", "ExecBlock (EXEC DLI)", "Java TODOコメント", "vendor_extensions.py", "変換実行ユーザー"],
    ["F-009", "変換エンジン", "ファイルI/O変換", "COBOL OPEN/CLOSE/READ/WRITE文をjava.io/java.nioベースのファイルハンドラクラスに変換する。VSAM→データベーステーブルへの変換戦略も選択可能。", "Statement (OPEN/CLOSE/READ/WRITE)", "Java FileHandler クラス", "conversion_strategies.py, java_generator.py", "変換実行ユーザー"],
    ["F-010", "変換エンジン", "ベンダー方言処理", "10種のCOBOLベンダー方言（IBM/富士通/NEC/日立/Micro Focus/Unisys/Bull/HP/GnuCOBOL/標準）固有の拡張を処理する。ベンダー固有のPIC型マッピング、EXEC解析・生成を含む。", "ソースコード + ベンダー指定", "ベンダー固有Java変換結果", "vendor_extensions.py", "変換実行ユーザー"],
    ["F-011", "変換エンジン", "ベンダー自動検出", "ソースコードのパターン（EXEC CICS/SQL/DLI、PIC N、CBL_*呼び出し等）からCOBOLベンダー方言を自動判別する。", "ソースコード行リスト", "VendorType", "vendor_extensions.py", "変換実行ユーザー"],
    ["F-012", "変換エンジン", "COPY文検出", "IDENTIFICATION/ENVIRONMENT/DATA各DIVISIONのCOPY文を検出し、メンバー名を記録する。COPY文自体の展開は行わない。", "ソースコード行", "copy_members リスト", "cobol_parser.py, division_parser.py", "変換実行ユーザー"],
    ["F-013", "変換エンジン", "再帰的サブフォルダ変換", "入力フォルダ内のサブフォルダを再帰的に走査し、ディレクトリ構造を維持したまま出力フォルダにJavaファイルを生成する。", "入力フォルダパス", "出力フォルダ内Java群", "gui_controller.py, main.py", "変換実行ユーザー"],
    # --- 変換戦略(Strategy) ---
    ["F-020", "拡張ポイント", "ファイルI/O戦略切替", "FileIoStrategy インタフェースにより、ファイルI/O変換ロジックをDefaultFileIoStrategy(java.io)からVsamToDatabaseStrategy(JDBC)等にプラグイン的に差し替え可能。", "Strategy実装クラス", "変換ロジック差替", "conversion_strategies.py", "開発者/アーキテクト"],
    ["F-021", "拡張ポイント", "SQL変換戦略切替", "SqlConversionStrategy インタフェースにより、EXEC SQL変換をJdbcSqlStrategy(PreparedStatement)からJpaSqlStrategy(EntityManager)等に差し替え可能。", "Strategy実装クラス", "変換ロジック差替", "conversion_strategies.py", "開発者/アーキテクト"],
    ["F-022", "拡張ポイント", "CICS変換戦略切替", "CicsConversionStrategy インタフェースにより、EXEC CICS変換ロジックをカスタム実装に差し替え可能。", "Strategy実装クラス", "変換ロジック差替", "conversion_strategies.py", "開発者/アーキテクト"],
    ["F-023", "拡張ポイント", "戦略レジストリ", "ConversionStrategyRegistryにより、ファイルI/O・SQL・CICSの3戦略を一括管理し、TransformerとGeneratorに注入する。", "Strategy各実装", "統合レジストリ", "conversion_strategies.py", "開発者/アーキテクト"],
    # --- GUI ---
    ["F-030", "GUI", "GUIメイン画面", "tkinterベースのデスクトップGUI。入出力フォルダ選択、変換オプション設定、プログレスバー、リアルタイムログ表示を提供する。MVCアーキテクチャで実装。", "ユーザー操作", "画面表示", "gui_view.py, gui_controller.py, gui_model.py", "変換実行ユーザー"],
    ["F-031", "GUI", "59言語UI切替", "UIラベル・メッセージを59言語で動的に切り替える多言語対応機能。ComboBoxで言語選択するとリアルタイムに全テキストが更新される。", "言語選択", "UIテキスト更新", "i18n.py, gui_view.py", "変換実行ユーザー"],
    ["F-032", "GUI", "変換実行・キャンセル", "変換処理をバックグラウンドスレッドで実行し、GUIのフリーズを防止する。キャンセルボタンで実行中の変換を中断可能。", "変換開始/キャンセルボタン", "変換結果/中断", "gui_controller.py", "変換実行ユーザー"],
    ["F-033", "GUI", "変換ログ表示", "変換の進捗をリアルタイムにログパネルに表示する。info/success/warning/error/headerの5種のタグで色分けされたシンタックスハイライト付き。", "変換イベント", "ログテキスト", "gui_view.py, gui_controller.py", "変換実行ユーザー"],
    # --- CLI ---
    ["F-040", "CLI", "コマンドライン実行", "-i (入力) と -o (出力) オプション指定によりGUIなしでヘッドレス変換を実行する。CI/CDパイプラインへの組み込みに対応。", "CLI引数", "Java出力 + コンソールログ", "main.py", "開発者/CI/CDシステム"],
    ["F-041", "CLI", "ベンダー指定オプション", "--vendor オプション (auto/standard/ibm/fujitsu/nec/hitachi/microfocus/unisys/bull/hp/gnucobol) でベンダー方言を指定可能。", "CLI --vendor 引数", "ベンダー固有処理適用", "main.py", "開発者/CI/CDシステム"],
    ["F-042", "CLI", "生成オプション制御", "--no-getters, --no-javadoc, --no-bigdecimal 等の否定フラグで生成内容を制御する。", "CLI --no-* 引数", "生成内容制御", "main.py", "開発者/CI/CDシステム"],
]

for r, row_data in enumerate(features, 2):
    for c, val in enumerate(row_data, 1):
        ws1.cell(row=r, column=c, value=val)
    style_body(ws1, r, len(cols1))

auto_width(ws1, len(cols1), [10, 14, 22, 65, 25, 25, 30, 18])
ws1.freeze_panes = "A2"
ws1.auto_filter.ref = f"A1:{get_column_letter(len(cols1))}{len(features)+1}"


# ============================================================
# Sheet 2: API仕様書 (CLI引数 + 内部API)
# ============================================================
ws2 = wb.create_sheet("API仕様書")
cols2 = ["API ID", "種別", "エンドポイント/メソッド", "パラメータ", "戻り値/出力", "処理概要", "所属モジュール"]
ws2.append(cols2)
style_header(ws2, 1, len(cols2))

apis = [
    # CLI
    ["CLI-001", "CLI引数", "-i, --input <path>", "フォルダパス (必須)", "N/A", "入力フォルダ（COBOL源泉）を指定する。-oと共に指定するとCLIモードで起動。", "main.py"],
    ["CLI-002", "CLI引数", "-o, --output <path>", "フォルダパス (必須)", "N/A", "出力フォルダ（Java出力先）を指定する。", "main.py"],
    ["CLI-003", "CLI引数", "-p, --package <name>", "パッケージ名 (default: com.migrated)", "N/A", "生成Javaクラスのパッケージ名を指定する。", "main.py"],
    ["CLI-004", "CLI引数", "-e, --encoding <enc>", "エンコーディング (default: utf-8)", "N/A", "COBOLソースのファイルエンコーディングを指定する。", "main.py"],
    ["CLI-005", "CLI引数", "--ext <exts>", "カンマ区切り拡張子 (default: .cbl,.cob,.cobol,.CBL,.COB)", "N/A", "処理対象のファイル拡張子を指定する。", "main.py"],
    ["CLI-006", "CLI引数", "--vendor <type>", "auto|standard|ibm|fujitsu|nec|hitachi|microfocus|unisys|bull|hp|gnucobol", "N/A", "COBOLベンダー方言を指定する。autoの場合はソースから自動検出。", "main.py"],
    ["CLI-007", "CLI引数", "--no-getters", "フラグ (store_true)", "N/A", "getter/setter生成を無効化する。", "main.py"],
    ["CLI-008", "CLI引数", "--no-bigdecimal", "フラグ (store_true)", "N/A", "BigDecimal使用を無効化し、doubleで代替する。", "main.py"],
    ["CLI-009", "CLI引数", "--no-javadoc", "フラグ (store_true)", "N/A", "Javadocコメント生成を無効化する。", "main.py"],
    ["CLI-010", "CLI引数", "--no-tostring", "フラグ (store_true)", "N/A", "toString()メソッド生成を無効化する。", "main.py"],
    ["CLI-011", "CLI引数", "--no-classes", "フラグ (store_true)", "N/A", "データクラス抽出を無効化する。", "main.py"],
    ["CLI-012", "CLI引数", "--no-enums", "フラグ (store_true)", "N/A", "Enum抽出を無効化する。", "main.py"],
    ["CLI-013", "CLI引数", "--no-services", "フラグ (store_true)", "N/A", "サービスクラス抽出を無効化する。", "main.py"],
    ["CLI-014", "CLI引数", "--no-filehandlers", "フラグ (store_true)", "N/A", "ファイルハンドラ抽出を無効化する。", "main.py"],
    # 内部API - パーサー
    ["API-001", "内部API", "CobolParser(encoding, use_lark)", "encoding: str, use_lark: bool=True", "CobolParser", "COBOLパーサーを初期化する。use_lark=Trueで構造化パーサーを使用、Falseでレガシー正規表現パーサーにフォールバック。", "cobol_parser.py"],
    ["API-002", "内部API", "CobolParser.parse_file(filepath)", "filepath: str", "CobolProgram", "COBOLソースファイルを解析しASTを返す。前処理→DIVISION検出→各DIVISION解析の順に実行。", "cobol_parser.py"],
    ["API-003", "内部API", "CobolParser.parse_string(source)", "source: str", "CobolProgram", "COBOL文字列を解析しASTを返す。テスト用途向け。", "cobol_parser.py"],
    ["API-004", "内部API", "LarkDataParser.parse_statement(stmt)", "stmt: str", "Optional[DataItem]", "1つのデータ定義文を解析しDataItemを返す。レベル番号、PIC、USAGE、VALUE、OCCURS、REDEFINES句を抽出。", "lark_data_parser.py"],
    ["API-005", "内部API", "LarkDataParser.parse_statements(stmts)", "stmts: List[str]", "List[DataItem]", "複数のデータ定義文を一括解析しDataItemリストを返す。", "lark_data_parser.py"],
    ["API-006", "内部API", "StatementClassifier.classify(text)", "text: str", "Optional[Statement]", "COBOL文テキストを動詞レジストリに基づきStatementType付きのStatement objectに分類する。", "lark_procedure_parser.py"],
    ["API-007", "内部API", "BlockParser.parse_block(stmts, idx, stmt)", "stmts: List[str], idx: int, stmt: Statement", "int (next idx)", "IF/EVALUATE/READブロック構造を再帰下降で解析し、children/else_children/when_blocksを構築する。", "lark_procedure_parser.py"],
    ["API-008", "内部API", "ProcedureDivisionParser.parse(stmts, program)", "stmts: List[str], program: CobolProgram", "None (programを変更)", "PROCEDURE DIVISION全体をセクション→パラグラフ→文ツリーに解析する。EXEC/CALLフラグも追跡。", "lark_procedure_parser.py"],
    ["API-009", "内部API", "DivisionRouter.parse(lines, program)", "lines: List[str], program: CobolProgram", "None (programを変更)", "プログラム全体のDIVISION境界を検出し、各DIVISIONパーサーにディスパッチする。", "division_parser.py"],
    ["API-010", "内部API", "CobolPreprocessor.process(raw_lines)", "raw_lines: List[str]", "List[str]", "固定形式/自由形式判別、コメント除去、継続行結合を行う。", "division_parser.py"],
    # 内部API - 変換
    ["API-011", "内部API", "OopTransformer(options, strategy_registry)", "options: TransformOptions, strategy_registry: ConversionStrategyRegistry", "OopTransformer", "OOP変換器を初期化する。変換オプションと戦略レジストリを受け取る。", "oop_transformer.py"],
    ["API-012", "内部API", "OopTransformer.transform(program)", "program: CobolProgram", "JavaProject", "COBOL ASTをJava OOPモデルに変換する。データクラス→Enum→ファイルハンドラ→メインクラス→サービスの順。", "oop_transformer.py"],
    ["API-013", "内部API", "JavaCodeGenerator(options, strategy_registry)", "options: TransformOptions, strategy_registry: ConversionStrategyRegistry", "JavaCodeGenerator", "Javaコードジェネレーターを初期化する。", "java_generator.py"],
    ["API-014", "内部API", "JavaCodeGenerator.generate_project(project, output_dir)", "project: JavaProject, output_dir: str", "None (.javaファイル出力)", "JavaProjectの全クラスをパッケージ構造に従いファイル出力する。", "java_generator.py"],
    ["API-015", "内部API", "JavaCodeGenerator.generate_class(cls)", "cls: JavaClass", "str", "1つのJavaClassから完全なJavaソースコード文字列を生成する。", "java_generator.py"],
    # 内部API - ベンダー/戦略
    ["API-016", "内部API", "detect_vendor(source_lines)", "source_lines: List[str]", "VendorType", "ソースコードのパターンマッチングによりベンダー方言を自動検出する。", "vendor_extensions.py"],
    ["API-017", "内部API", "parse_exec_block(text)", "text: str", "Optional[ExecBlock]", "EXEC...END-EXECブロックを解析しExecBlock構造体を返す。SQL/CICS/DLIに対応。", "vendor_extensions.py"],
    ["API-018", "内部API", "ConversionStrategyRegistry()", "N/A", "ConversionStrategyRegistry", "デフォルト戦略(DefaultFileIo, JdbcSql, DefaultCics)で初期化された戦略レジストリを生成する。", "conversion_strategies.py"],
    # 内部API - GUI MVC
    ["API-019", "内部API", "CobolToJavaView(root, i18n)", "root: tk.Tk, i18n: I18n", "CobolToJavaView", "GUIのView層を初期化する。全ウィジェットの生成・配置を行い、バインドAPIを公開する。", "gui_view.py"],
    ["API-020", "内部API", "ConversionController(view, i18n)", "view: CobolToJavaView, i18n: I18n", "ConversionController", "Controller層を初期化する。Viewのイベントバインドと変換ロジックを担当。", "gui_controller.py"],
    ["API-021", "内部API", "I18n(lang)", "lang: str (言語コード)", "I18n", "多言語翻訳エンジンを初期化する。i18n.t(key) で翻訳テキストを取得。", "i18n.py"],
]

for r, row_data in enumerate(apis, 2):
    for c, val in enumerate(row_data, 1):
        ws2.cell(row=r, column=c, value=val)
    style_body(ws2, r, len(cols2))

auto_width(ws2, len(cols2), [10, 10, 42, 45, 30, 55, 24])
ws2.freeze_panes = "A2"
ws2.auto_filter.ref = f"A1:{get_column_letter(len(cols2))}{len(apis)+1}"


# ============================================================
# Sheet 3: テーブル定義書 (データクラス/dataclass)
# ============================================================
ws3 = wb.create_sheet("データ構造定義書")
cols3 = ["構造体ID", "クラス/dataclass名", "フィールド名", "型", "デフォルト値", "制約/備考", "所属モジュール"]
ws3.append(cols3)
style_header(ws3, 1, len(cols3))

tables = [
    # CobolProgram
    ["DC-001", "CobolProgram", "program_id", "str", '""', "PROGRAM-IDから取得", "cobol_parser.py"],
    ["DC-001", "CobolProgram", "author", "str", '""', "AUTHOR句から取得", "cobol_parser.py"],
    ["DC-001", "CobolProgram", "date_written", "str", '""', "DATE-WRITTEN句から取得", "cobol_parser.py"],
    ["DC-001", "CobolProgram", "source_file", "str", '""', "解析元ファイルパス", "cobol_parser.py"],
    ["DC-001", "CobolProgram", "files", "List[FileDefinition]", "[]", "FILE SECTIONのファイル定義", "cobol_parser.py"],
    ["DC-001", "CobolProgram", "working_storage", "List[DataItem]", "[]", "WORKING-STORAGEのデータ項目", "cobol_parser.py"],
    ["DC-001", "CobolProgram", "local_storage", "List[DataItem]", "[]", "LOCAL-STORAGEのデータ項目", "cobol_parser.py"],
    ["DC-001", "CobolProgram", "linkage_section", "List[DataItem]", "[]", "LINKAGE SECTIONのデータ項目", "cobol_parser.py"],
    ["DC-001", "CobolProgram", "screen_section", "List[DataItem]", "[]", "SCREEN SECTIONのデータ項目", "cobol_parser.py"],
    ["DC-001", "CobolProgram", "sections", "List[Section]", "[]", "PROCEDURE DIVISIONのセクション", "cobol_parser.py"],
    ["DC-001", "CobolProgram", "paragraphs", "List[Paragraph]", "[]", "PROCEDURE DIVISIONのパラグラフ", "cobol_parser.py"],
    ["DC-001", "CobolProgram", "copy_members", "List[str]", "[]", "検出されたCOPYメンバー名", "cobol_parser.py"],
    ["DC-001", "CobolProgram", "called_programs", "List[str]", "[]", "CALL文で呼び出されるプログラム名", "cobol_parser.py"],
    ["DC-001", "CobolProgram", "vendor_type", "str", '"standard"', "ベンダー方言識別子", "cobol_parser.py"],
    ["DC-001", "CobolProgram", "has_exec_sql", "bool", "False", "EXEC SQLブロックの有無", "cobol_parser.py"],
    ["DC-001", "CobolProgram", "has_exec_cics", "bool", "False", "EXEC CICSブロックの有無", "cobol_parser.py"],
    ["DC-001", "CobolProgram", "has_exec_dli", "bool", "False", "EXEC DLIブロックの有無", "cobol_parser.py"],
    ["DC-001", "CobolProgram", "has_class_id", "bool", "False", "OO COBOL CLASS-IDの有無", "cobol_parser.py"],
    ["DC-001", "CobolProgram", "class_id", "str", '""', "OO COBOLのクラスID", "cobol_parser.py"],
    # DataItem
    ["DC-002", "DataItem", "level", "int", "N/A", "レベル番号 (01-88)", "cobol_parser.py"],
    ["DC-002", "DataItem", "name", "str", "N/A", "データ項目名", "cobol_parser.py"],
    ["DC-002", "DataItem", "picture", "str", '""', "PIC句 (例: 9(5), X(10))", "cobol_parser.py"],
    ["DC-002", "DataItem", "usage", "str", '""', "USAGE句 (COMP-3, POINTER等)", "cobol_parser.py"],
    ["DC-002", "DataItem", "value", "Optional[str]", "None", "VALUE句の値", "cobol_parser.py"],
    ["DC-002", "DataItem", "occurs", "int", "0", "OCCURS回数 (0=なし)", "cobol_parser.py"],
    ["DC-002", "DataItem", "occurs_depending", "str", '""', "OCCURS DEPENDING ON変数名", "cobol_parser.py"],
    ["DC-002", "DataItem", "redefines", "str", '""', "REDEFINES対象名", "cobol_parser.py"],
    ["DC-002", "DataItem", "is_filler", "bool", "False", "FILLER項目かどうか", "cobol_parser.py"],
    ["DC-002", "DataItem", "children", "List[DataItem]", "[]", "子データ項目 (グループ項目)", "cobol_parser.py"],
    ["DC-002", "DataItem", "is_88_level", "bool", "False", "88レベル条件名かどうか", "cobol_parser.py"],
    ["DC-002", "DataItem", "condition_values", "List[str]", "[]", "88レベルのVALUE値リスト", "cobol_parser.py"],
    # Statement
    ["DC-003", "Statement", "type", "StatementType", "N/A", "文種別 (35種のEnum値)", "cobol_parser.py"],
    ["DC-003", "Statement", "raw_text", "str", "N/A", "生のCOBOLテキスト", "cobol_parser.py"],
    ["DC-003", "Statement", "tokens", "List[str]", "[]", "トークン分割結果", "cobol_parser.py"],
    ["DC-003", "Statement", "children", "List[Statement]", "[]", "子文 (IFのTHEN節等)", "cobol_parser.py"],
    ["DC-003", "Statement", "else_children", "List[Statement]", "[]", "ELSE節/AT END節", "cobol_parser.py"],
    ["DC-003", "Statement", "when_blocks", "List[tuple]", "[]", "EVALUATE WHEN (条件, 文リスト)", "cobol_parser.py"],
    # FileDefinition
    ["DC-004", "FileDefinition", "select_name", "str", '""', "SELECT句のファイル名", "cobol_parser.py"],
    ["DC-004", "FileDefinition", "assign_to", "str", '""', "ASSIGN TO先", "cobol_parser.py"],
    ["DC-004", "FileDefinition", "organization", "str", '"SEQUENTIAL"', "ORGANIZATION (SEQUENTIAL/INDEXED/RELATIVE)", "cobol_parser.py"],
    ["DC-004", "FileDefinition", "access_mode", "str", '"SEQUENTIAL"', "ACCESS MODE (SEQUENTIAL/RANDOM/DYNAMIC)", "cobol_parser.py"],
    ["DC-004", "FileDefinition", "file_status", "str", '""', "FILE STATUS変数名", "cobol_parser.py"],
    ["DC-004", "FileDefinition", "fd_name", "str", '""', "FD名", "cobol_parser.py"],
    # ExecBlock
    ["DC-005", "ExecBlock", "exec_type", "str", "N/A", "EXEC種別 (SQL/CICS/DLI)", "vendor_extensions.py"],
    ["DC-005", "ExecBlock", "command", "str", "N/A", "コマンド動詞 (SELECT/SEND等)", "vendor_extensions.py"],
    ["DC-005", "ExecBlock", "raw_text", "str", "N/A", "生のEXECテキスト", "vendor_extensions.py"],
    ["DC-005", "ExecBlock", "parameters", "Dict[str,str]", "{}", "パラメータ辞書", "vendor_extensions.py"],
    # Java OOPモデル
    ["DC-010", "JavaField", "name", "str", "N/A", "Javaフィールド名 (camelCase)", "oop_transformer.py"],
    ["DC-010", "JavaField", "java_type", "str", "N/A", "Java型名 (int/String/BigDecimal等)", "oop_transformer.py"],
    ["DC-010", "JavaField", "initial_value", "Optional[str]", "None", "初期値 (Javaリテラル)", "oop_transformer.py"],
    ["DC-010", "JavaField", "is_array", "bool", "False", "配列かどうか (OCCURS由来)", "oop_transformer.py"],
    ["DC-010", "JavaField", "array_size", "int", "0", "配列サイズ", "oop_transformer.py"],
    ["DC-010", "JavaField", "access", "str", '"private"', "アクセス修飾子", "oop_transformer.py"],
    ["DC-010", "JavaField", "original_cobol_name", "str", '""', "元のCOBOLデータ名", "oop_transformer.py"],
    ["DC-010", "JavaField", "original_picture", "str", '""', "元のPIC句", "oop_transformer.py"],
    # JavaMethod
    ["DC-011", "JavaMethod", "name", "str", "N/A", "Javaメソッド名 (camelCase)", "oop_transformer.py"],
    ["DC-011", "JavaMethod", "return_type", "str", '"void"', "戻り値型", "oop_transformer.py"],
    ["DC-011", "JavaMethod", "parameters", "List[tuple]", "[]", "引数リスト (型, 名前)", "oop_transformer.py"],
    ["DC-011", "JavaMethod", "body_statements", "List[Statement]", "[]", "メソッド本体のStatement", "oop_transformer.py"],
    ["DC-011", "JavaMethod", "access", "str", '"public"', "アクセス修飾子", "oop_transformer.py"],
    ["DC-011", "JavaMethod", "original_paragraph", "str", '""', "元のCOBOLパラグラフ名", "oop_transformer.py"],
    ["DC-011", "JavaMethod", "is_main_entry", "bool", "False", "main()エントリかどうか", "oop_transformer.py"],
    # JavaClass
    ["DC-012", "JavaClass", "name", "str", "N/A", "Javaクラス名 (PascalCase)", "oop_transformer.py"],
    ["DC-012", "JavaClass", "package_name", "str", '""', "パッケージ名", "oop_transformer.py"],
    ["DC-012", "JavaClass", "imports", "Set[str]", "set()", "import文セット", "oop_transformer.py"],
    ["DC-012", "JavaClass", "fields", "List[JavaField]", "[]", "フィールド定義", "oop_transformer.py"],
    ["DC-012", "JavaClass", "methods", "List[JavaMethod]", "[]", "メソッド定義", "oop_transformer.py"],
    ["DC-012", "JavaClass", "is_data_class", "bool", "False", "データクラスかどうか", "oop_transformer.py"],
    ["DC-012", "JavaClass", "is_enum", "bool", "False", "Enumクラスかどうか", "oop_transformer.py"],
    ["DC-012", "JavaClass", "enum_values", "List[str]", "[]", "Enum値リスト", "oop_transformer.py"],
    # JavaProject
    ["DC-013", "JavaProject", "main_class", "Optional[JavaClass]", "None", "メインクラス", "oop_transformer.py"],
    ["DC-013", "JavaProject", "data_classes", "List[JavaClass]", "[]", "データクラス群", "oop_transformer.py"],
    ["DC-013", "JavaProject", "service_classes", "List[JavaClass]", "[]", "サービスクラス群", "oop_transformer.py"],
    ["DC-013", "JavaProject", "enum_classes", "List[JavaClass]", "[]", "Enumクラス群", "oop_transformer.py"],
    ["DC-013", "JavaProject", "file_handler_classes", "List[JavaClass]", "[]", "ファイルハンドラクラス群", "oop_transformer.py"],
    # ConversionConfig
    ["DC-020", "ConversionConfig", "input_dir", "str", '""', "入力ディレクトリパス", "gui_model.py"],
    ["DC-020", "ConversionConfig", "output_dir", "str", '""', "出力ディレクトリパス", "gui_model.py"],
    ["DC-020", "ConversionConfig", "package_name", "str", '"com.migrated"', "Javaパッケージ名", "gui_model.py"],
    ["DC-020", "ConversionConfig", "encoding", "str", '"utf-8"', "ソースエンコーディング", "gui_model.py"],
    ["DC-020", "ConversionConfig", "vendor", "str", '"auto"', "ベンダー方言", "gui_model.py"],
    ["DC-020", "ConversionConfig", "generate_getters_setters", "bool", "True", "getter/setter生成", "gui_model.py"],
    ["DC-020", "ConversionConfig", "use_big_decimal", "bool", "True", "BigDecimal使用", "gui_model.py"],
    ["DC-020", "ConversionConfig", "generate_javadoc", "bool", "True", "Javadoc生成", "gui_model.py"],
    # ConversionState
    ["DC-021", "ConversionState", "is_running", "bool", "False", "変換実行中フラグ", "gui_model.py"],
    ["DC-021", "ConversionState", "cancel_flag", "bool", "False", "キャンセル要求フラグ", "gui_model.py"],
    ["DC-021", "ConversionState", "progress", "float", "0.0", "進捗率 (0.0-100.0)", "gui_model.py"],
    ["DC-021", "ConversionState", "success_count", "int", "0", "成功ファイル数", "gui_model.py"],
    ["DC-021", "ConversionState", "error_count", "int", "0", "エラーファイル数", "gui_model.py"],
    # TransformOptions
    ["DC-022", "TransformOptions", "package_name", "str", '"com.migrated"', "生成パッケージ名", "oop_transformer.py"],
    ["DC-022", "TransformOptions", "generate_getters_setters", "bool", "True", "getter/setter生成制御", "oop_transformer.py"],
    ["DC-022", "TransformOptions", "use_big_decimal", "bool", "True", "BigDecimal使用制御", "oop_transformer.py"],
    ["DC-022", "TransformOptions", "generate_javadoc", "bool", "True", "Javadoc生成制御", "oop_transformer.py"],
    ["DC-022", "TransformOptions", "generate_toString", "bool", "True", "toString()生成制御", "oop_transformer.py"],
    ["DC-022", "TransformOptions", "extract_data_classes", "bool", "True", "データクラス抽出制御", "oop_transformer.py"],
    ["DC-022", "TransformOptions", "extract_enums", "bool", "True", "Enum抽出制御", "oop_transformer.py"],
    ["DC-022", "TransformOptions", "extract_file_handlers", "bool", "True", "ファイルハンドラ抽出制御", "oop_transformer.py"],
    ["DC-022", "TransformOptions", "group_related_paragraphs", "bool", "True", "サービスクラス抽出制御", "oop_transformer.py"],
    ["DC-022", "TransformOptions", "vendor_type", "str", '"standard"', "ベンダー方言指定", "oop_transformer.py"],
]

for r, row_data in enumerate(tables, 2):
    for c, val in enumerate(row_data, 1):
        ws3.cell(row=r, column=c, value=val)
    style_body(ws3, r, len(cols3))

auto_width(ws3, len(cols3), [10, 20, 26, 22, 18, 40, 20])
ws3.freeze_panes = "A2"
ws3.auto_filter.ref = f"A1:{get_column_letter(len(cols3))}{len(tables)+1}"


# ============================================================
# Sheet 4: エラー・ログ定義書
# ============================================================
ws4 = wb.create_sheet("エラー・ログ定義書")
cols4 = ["ID", "レベル", "出力先", "メッセージ/パターン", "発生条件", "対処方法", "所属モジュール"]
ws4.append(cols4)
style_header(ws4, 1, len(cols4))

errors = [
    # CLI エラー
    ["ERR-001", "ERROR", "stderr+exit(1)", "[ERROR] Input directory does not exist: {path}", "CLI実行時に-iで指定したディレクトリが存在しない", "正しいパスを指定する", "main.py"],
    ["ERR-002", "ERROR", "stderr+exit(1)", "[ERROR] Both -i/--input and -o/--output must be provided for CLI execution.", "-iまたは-oの片方のみ指定された", "両方のオプションを指定する", "main.py"],
    ["ERR-003", "WARNING", "stdout", "[WARNING] No COBOL files found with extensions: {ext}", "指定フォルダ内に対象拡張子のファイルが存在しない", "フォルダパスと拡張子設定を確認する", "main.py"],
    ["ERR-004", "ERROR", "stdout", "[ERROR] {error_message}", "個別ファイルの変換処理中に例外が発生", "エラーメッセージとスタックトレースを確認する", "main.py"],
    # GUI エラー (messagebox)
    ["ERR-010", "WARNING", "messagebox", "warn_no_input (i18n)", "入力フォルダが未指定で変換ボタンが押された", "入力フォルダを選択する", "gui_controller.py"],
    ["ERR-011", "WARNING", "messagebox", "warn_no_output (i18n)", "出力フォルダが未指定で変換ボタンが押された", "出力フォルダを選択する", "gui_controller.py"],
    ["ERR-012", "ERROR", "messagebox", "error_no_input_dir (i18n) {path}", "指定された入力フォルダが存在しない", "正しいパスを指定する", "gui_controller.py"],
    # GUI ログ出力 (info)
    ["LOG-001", "HEADER", "ログパネル", "COBOL to Java Migration - Starting", "変換処理開始時", "N/A", "gui_controller.py"],
    ["LOG-002", "INFO", "ログパネル", "log_input / log_output {path}", "入出力パスの確認表示", "N/A", "gui_controller.py"],
    ["LOG-003", "INFO", "ログパネル", "log_found_files {count}", "変換対象ファイル数の表示", "N/A", "gui_controller.py"],
    ["LOG-004", "INFO", "ログパネル", "log_parsing", "ファイル解析開始", "N/A", "gui_controller.py"],
    ["LOG-005", "INFO", "ログパネル", "log_vendor_detected {vendor}", "ベンダー自動検出結果", "N/A", "gui_controller.py"],
    ["LOG-006", "INFO", "ログパネル", "log_program_id / ws_items / paragraphs / sections / files", "解析結果サマリー表示", "N/A", "gui_controller.py"],
    ["LOG-007", "INFO", "ログパネル", "log_exec_sql / log_exec_cics / log_exec_dli", "EXEC SQL/CICS/DLI検出通知", "N/A", "gui_controller.py"],
    ["LOG-008", "INFO", "ログパネル", "log_transforming", "OOP変換開始", "N/A", "gui_controller.py"],
    ["LOG-009", "INFO", "ログパネル", "log_main_class / fields / methods / data_classes / enum_classes / service_classes / file_handlers", "変換結果サマリー表示", "N/A", "gui_controller.py"],
    ["LOG-010", "INFO", "ログパネル", "log_generating", "Javaコード生成開始", "N/A", "gui_controller.py"],
    ["LOG-011", "SUCCESS", "ログパネル", "log_generated {count}", "ファイル変換成功", "N/A", "gui_controller.py"],
    ["LOG-012", "WARNING", "ログパネル", "log_no_files {ext}", "対象ファイルが見つからない", "拡張子設定を確認する", "gui_controller.py"],
    ["LOG-013", "WARNING", "ログパネル", "log_cancel_request / log_cancelled", "キャンセル要求/完了", "N/A", "gui_controller.py"],
    ["LOG-014", "ERROR", "ログパネル", "ERROR: {error_message} + traceback", "個別ファイル変換失敗", "スタックトレースを確認する", "gui_controller.py"],
    ["LOG-015", "ERROR", "ログパネル", "Fatal error: {error_message}", "変換ループ全体の致命的エラー", "バグ報告を推奨", "gui_controller.py"],
    ["LOG-016", "HEADER", "ログパネル", "Migration Complete / Success: {n} / Errors: {n}", "変換処理完了サマリー", "N/A", "gui_controller.py"],
    # パーサー警告
    ["LOG-020", "WARNING", "stdout(CLI)", "Warning: Vendor detection failed: {error}", "ベンダー自動検出処理中に例外が発生", "--vendorで明示指定する", "main.py"],
    # コード生成 TODO
    ["GEN-001", "TODO", "生成Javaコード内", "// TODO: Manual conversion required", "未対応のEXECブロックがある", "生成後にJava側を手動で実装する", "java_generator.py"],
    ["GEN-002", "TODO", "生成Javaコード内", "// TODO: EXEC DLI - manual conversion to JPA/Hibernate recommended", "EXEC DLIブロック検出", "JPA/Hibernateで手動実装する", "vendor_extensions.py"],
]

for r, row_data in enumerate(errors, 2):
    for c, val in enumerate(row_data, 1):
        ws4.cell(row=r, column=c, value=val)
    style_body(ws4, r, len(cols4))

auto_width(ws4, len(cols4), [10, 10, 18, 55, 38, 30, 20])
ws4.freeze_panes = "A2"
ws4.auto_filter.ref = f"A1:{get_column_letter(len(cols4))}{len(errors)+1}"


# ============================================================
# Sheet 5: アーキテクチャ図解（Mermaid）
# ============================================================
ws5 = wb.create_sheet("Mermaid図解")
cols5 = ["図の名称", "Mermaidコード"]
ws5.append(cols5)
style_header(ws5, 1, len(cols5))

diagrams = [
    ["システム構成図 (モジュール依存関係)",
"""graph TD
    subgraph Entry["エントリポイント"]
        MAIN["main.py"]
    end

    subgraph MVC["GUI (MVC)"]
        MODEL["gui_model.py<br/>ConversionConfig / ConversionState"]
        VIEW["gui_view.py<br/>CobolToJavaView"]
        CTRL["gui_controller.py<br/>ConversionController"]
    end

    subgraph Parser["解析エンジン"]
        CP["cobol_parser.py<br/>CobolParser"]
        DP["division_parser.py<br/>DivisionRouter"]
        LDP["lark_data_parser.py<br/>LarkDataParser"]
        LPP["lark_procedure_parser.py<br/>ProcedureDivisionParser"]
    end

    subgraph Transform["変換エンジン"]
        OT["oop_transformer.py<br/>OopTransformer"]
        JG["java_generator.py<br/>JavaCodeGenerator"]
        CS["conversion_strategies.py<br/>Strategy Interfaces"]
        VE["vendor_extensions.py<br/>10 Vendor Dialects"]
    end

    I18N["i18n.py<br/>59 Languages"]

    MAIN --> CTRL
    MAIN --> CP
    CTRL --> VIEW
    CTRL --> MODEL
    CTRL --> CP
    CTRL --> OT
    CTRL --> JG
    VIEW --> I18N
    CP --> DP
    CP --> LDP
    CP --> LPP
    OT --> CS
    JG --> CS
    JG --> VE
"""],

    ["変換パイプライン (シーケンス図)",
"""sequenceDiagram
    participant U as ユーザー
    participant C as Controller
    participant P as CobolParser
    participant PP as CobolPreprocessor
    participant DR as DivisionRouter
    participant LDP as LarkDataParser
    participant LPP as ProcedureDivisionParser
    participant T as OopTransformer
    participant G as JavaCodeGenerator
    participant SR as StrategyRegistry

    U->>C: 変換開始
    C->>P: parse_file(filepath)
    P->>PP: process(raw_lines)
    PP-->>P: 前処理済み行
    P->>DR: parse(lines, program)
    DR->>DR: detect_division()
    DR->>LDP: parse_statements() [DATA]
    DR->>LPP: parse(stmts, program) [PROCEDURE]
    LPP->>LPP: classify() + parse_block()
    P-->>C: CobolProgram (AST)
    C->>T: transform(program)
    T->>SR: get file_io/sql/cics strategies
    T-->>C: JavaProject
    C->>G: generate_project(project, dir)
    G->>SR: delegate EXEC SQL/CICS
    G-->>C: .java files written
    C-->>U: 完了ログ表示
"""],

    ["データフロー図 (AST構造)",
"""graph LR
    subgraph COBOL["COBOL Source"]
        ID[IDENTIFICATION<br/>DIVISION]
        ENV[ENVIRONMENT<br/>DIVISION]
        DATA[DATA<br/>DIVISION]
        PROC[PROCEDURE<br/>DIVISION]
    end

    subgraph AST["CobolProgram AST"]
        PID[program_id]
        FD[FileDefinition]
        WS[working_storage<br/>DataItem Tree]
        LS[linkage_section<br/>DataItem Tree]
        SEC[Section]
        PARA[Paragraph]
        STMT[Statement Tree]
    end

    subgraph Java["Java OOP Model"]
        MC[MainClass]
        DC[DataClass]
        EN[EnumClass]
        SC[ServiceClass]
        FH[FileHandlerClass]
    end

    ID --> PID
    ENV --> FD
    DATA --> WS
    DATA --> LS
    PROC --> SEC
    PROC --> PARA
    SEC --> PARA
    PARA --> STMT

    WS -->|"グループ項目"| DC
    WS -->|"88レベル"| EN
    FD -->|"FILE SECTION"| FH
    PARA -->|"パラグラフ群"| MC
    PARA -->|"関連パラグラフ"| SC
    STMT -->|"文ツリー"| MC
"""],

    ["Strategy Pattern (クラス図)",
"""classDiagram
    class FileIoStrategy {
        <<interface>>
        +generate_imports() Set~str~
        +generate_open(handler, mode, indent) List~str~
        +generate_close(handler, indent) List~str~
        +generate_read(handler, record, indent) List~str~
        +generate_write(handler, expr, indent) List~str~
        +generate_handler_class_body() List~str~
    }

    class SqlConversionStrategy {
        <<interface>>
        +generate_imports() Set~str~
        +generate_fields(indent) List~str~
        +generate_select(sql, vars, into, indent) List~str~
        +generate_insert_update_delete(sql, vars, indent) List~str~
        +generate_cursor_declare/open/fetch/close()
        +generate_commit/rollback(indent) List~str~
    }

    class CicsConversionStrategy {
        <<interface>>
        +generate_imports() Set~str~
        +generate_fields(indent) List~str~
        +generate_terminal_io(cmd, params, indent) List~str~
        +generate_file_io(cmd, params, indent) List~str~
        +generate_program_control(cmd, params, indent) List~str~
        +generate_temp_storage(cmd, params, indent) List~str~
    }

    class ConversionStrategyRegistry {
        -_file_io: FileIoStrategy
        -_sql: SqlConversionStrategy
        -_cics: CicsConversionStrategy
        +file_io: property
        +sql: property
        +cics: property
    }

    class DefaultFileIoStrategy
    class VsamToDatabaseStrategy
    class JdbcSqlStrategy
    class JpaSqlStrategy
    class DefaultCicsStrategy

    FileIoStrategy <|.. DefaultFileIoStrategy
    FileIoStrategy <|.. VsamToDatabaseStrategy
    SqlConversionStrategy <|.. JdbcSqlStrategy
    SqlConversionStrategy <|.. JpaSqlStrategy
    CicsConversionStrategy <|.. DefaultCicsStrategy

    ConversionStrategyRegistry --> FileIoStrategy
    ConversionStrategyRegistry --> SqlConversionStrategy
    ConversionStrategyRegistry --> CicsConversionStrategy
"""],

    ["MVC アーキテクチャ (GUI画面遷移)",
"""stateDiagram-v2
    [*] --> 起動
    起動 --> 初期画面: main.py → run_gui()

    state 初期画面 {
        [*] --> 言語選択可能
        言語選択可能 --> UI更新: 言語ComboBox変更
        UI更新 --> 言語選択可能

        言語選択可能 --> フォルダ選択
        フォルダ選択 --> オプション設定
        オプション設定 --> 変換待機: Run可能
    }

    変換待機 --> 変換実行中: Runボタン押下

    state 変換実行中 {
        [*] --> ファイル解析
        ファイル解析 --> OOP変換
        OOP変換 --> Java生成
        Java生成 --> 次ファイル: ファイルあり
        次ファイル --> ファイル解析
        Java生成 --> 完了: 全ファイル完了
    }

    変換実行中 --> 変換キャンセル: Cancelボタン
    変換キャンセル --> 初期画面
    完了 --> 初期画面: 結果ログ表示

    note right of 変換実行中
        バックグラウンドスレッドで実行
        GUIはフリーズしない
        プログレスバー更新
    end note
"""],

    ["StatementType Enum (全35値)",
"""graph LR
    subgraph 算術["算術文"]
        MOVE
        ADD
        SUBTRACT
        MULTIPLY
        DIVIDE
        COMPUTE
    end

    subgraph 制御["制御文"]
        IF
        EVALUATE
        PERFORM
        GO_TO
        STOP_RUN
        GOBACK
        EXIT
        CONTINUE
    end

    subgraph IO["入出力文"]
        DISPLAY
        ACCEPT
        READ
        WRITE
        OPEN
        CLOSE
    end

    subgraph 文字列["文字列操作"]
        STRING
        UNSTRING
        INSPECT
        INITIALIZE
    end

    subgraph 呼出["プログラム呼出"]
        CALL
        INVOKE
        ENTER
    end

    subgraph EXEC["EXEC文"]
        EXEC_SQL
        EXEC_CICS
        EXEC_DLI
        EXEC_OTHER
    end

    subgraph XML_JSON["XML/JSON"]
        XML_GENERATE
        XML_PARSE
        JSON_GENERATE
        JSON_PARSE
    end

    subgraph その他["その他"]
        SET
        UNKNOWN
    end
"""],
]

for r, (name, code) in enumerate(diagrams, 2):
    ws5.cell(row=r, column=1, value=name)
    ws5.cell(row=r, column=2, value=code)
    style_body(ws5, r, 2)
    ws5.row_dimensions[r].height = 400

auto_width(ws5, 2, [35, 120])
ws5.freeze_panes = "A2"


# === Save ===
output_path = r"G:\マイドライブ\claudecode\COBOL2Java\design_document.xlsx"
wb.save(output_path)
print(f"Saved: {output_path}")
