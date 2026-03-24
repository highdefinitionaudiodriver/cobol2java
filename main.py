"""
COBOL to Java Migration Tool
A GUI application that converts COBOL source code to Java (59 languages supported)

Architecture:
  - Model: src/gui_model.py (ConversionConfig, ConversionState)
  - View:  src/gui_view.py  (CobolToJavaView - widget creation/layout)
  - Controller: src/gui_controller.py (ConversionController - event handling/logic)
"""
import os
import sys
import traceback
import argparse

# Support running as script or frozen exe
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, BASE_DIR)

from src.cobol_parser import CobolParser
from src.oop_transformer import OopTransformer, TransformOptions
from src.java_generator import JavaCodeGenerator
from src.vendor_extensions import (
    VendorType, VENDOR_DISPLAY_NAMES, detect_vendor
)


def run_cli(args):
    """Execute conversion without GUI."""
    print("=" * 60)
    print("COBOL to Java Migration - Starting (CLI Mode)")
    print("=" * 60)

    input_dir = args.input.strip()
    output_dir = args.output.strip()

    if not os.path.isdir(input_dir):
        print(f"[ERROR] Input directory does not exist: {input_dir}")
        sys.exit(1)

    print(f"Input:  {input_dir}")
    print(f"Output: {output_dir}")
    print(f"Vendor: {args.vendor}")
    print(f"Package: {args.package}")

    extensions = [e.strip() for e in args.ext.split(",")]
    cobol_files = []
    for root_dir, dirs, files in os.walk(input_dir):
        for f in files:
            if any(f.endswith(ext) for ext in extensions):
                cobol_files.append(os.path.join(root_dir, f))

    if not cobol_files:
        print(f"[WARNING] No COBOL files found with extensions: {extensions}")
        sys.exit(0)

    print(f"Found {len(cobol_files)} COBOL file(s).")

    options = TransformOptions(
        package_name=args.package,
        generate_getters_setters=not args.no_getters,
        use_big_decimal=not args.no_bigdecimal,
        generate_javadoc=not args.no_javadoc,
        generate_toString=not args.no_tostring,
        extract_data_classes=not args.no_classes,
        extract_enums=not args.no_enums,
        extract_file_handlers=not args.no_filehandlers,
        group_related_paragraphs=not args.no_services,
        vendor_type=args.vendor,
    )

    parser = CobolParser(encoding=args.encoding)
    transformer = OopTransformer(options)
    generator = JavaCodeGenerator(options)

    success_count = 0
    error_count = 0

    for filepath in cobol_files:
        filename = os.path.basename(filepath)
        print(f"\n--- Processing: {filename} ---")
        try:
            program = parser.parse_file(filepath)

            if args.vendor == "auto":
                try:
                    with open(filepath, "r", encoding=args.encoding, errors="replace") as vf:
                        src_lines = vf.readlines()
                    detected = detect_vendor(src_lines)
                    program.vendor_type = detected.value
                    vendor_name = VENDOR_DISPLAY_NAMES.get(detected, detected.value)
                    print(f"  Vendor detected: {vendor_name}")
                except Exception as e:
                    print(f"  Warning: Vendor detection failed: {str(e)}")
            else:
                program.vendor_type = args.vendor

            project = transformer.transform(program)

            rel_dir = os.path.relpath(os.path.dirname(filepath), input_dir)
            if rel_dir == ".":
                file_output_dir = output_dir
            else:
                file_output_dir = os.path.join(output_dir, rel_dir)

            generator.generate_project(project, file_output_dir)
            success_count += 1
            print("  Success.")

        except Exception as e:
            error_count += 1
            print(f"  [ERROR] {str(e)}")
            traceback.print_exc()

    print(f"\n{'=' * 60}")
    print("Migration Complete")
    print(f"{'=' * 60}")
    print(f"  Success: {success_count} file(s)")
    if error_count > 0:
        print(f"  Errors:  {error_count} file(s)")
        sys.exit(1)


def run_gui():
    """Launch GUI application using MVC architecture."""
    import tkinter as tk
    from src.i18n import I18n
    from src.gui_view import CobolToJavaView
    from src.gui_controller import ConversionController

    root = tk.Tk()

    icon_path = os.path.join(BASE_DIR, "icon.ico")
    if os.path.exists(icon_path):
        root.iconbitmap(icon_path)

    i18n = I18n("en")
    view = CobolToJavaView(root, i18n)
    controller = ConversionController(view, i18n)

    root.mainloop()


def main():
    parser = argparse.ArgumentParser(description="COBOL to Java Migration Tool")
    parser.add_argument("-i", "--input", help="Input folder containing COBOL files (CLI execution)")
    parser.add_argument("-o", "--output", help="Output folder for generated Java files")
    parser.add_argument("-p", "--package", default="com.migrated", help="Package name for generated classes (default: com.migrated)")
    parser.add_argument("-e", "--encoding", default="utf-8", help="Source encoding (default: utf-8)")
    parser.add_argument("--ext", default=".cbl,.cob,.cobol,.CBL,.COB", help="Comma-separated file extensions to process (default: .cbl,.cob,.cobol,.CBL,.COB)")
    parser.add_argument("--vendor", default="auto", choices=["auto", "standard", "ibm", "fujitsu", "nec", "hitachi", "microfocus", "unisys", "bull", "hp", "gnucobol"], help="Vendor dialect (default: auto)")

    parser.add_argument("--no-getters", action="store_true", help="Disable generating Getters/Setters")
    parser.add_argument("--no-bigdecimal", action="store_true", help="Disable using BigDecimal for decimals")
    parser.add_argument("--no-javadoc", action="store_true", help="Disable generating Javadoc comments")
    parser.add_argument("--no-tostring", action="store_true", help="Disable generating toString()")
    parser.add_argument("--no-classes", action="store_true", help="Disable extracting Data Classes")
    parser.add_argument("--no-enums", action="store_true", help="Disable extracting Enums")
    parser.add_argument("--no-services", action="store_true", help="Disable extracting Services")
    parser.add_argument("--no-filehandlers", action="store_true", help="Disable extracting File Handlers")

    args = parser.parse_args()

    # If standard inputs are provided, run CLI, else GUI
    if args.input and args.output:
        run_cli(args)
    elif args.input or args.output:
        print("[ERROR] Both -i/--input and -o/--output must be provided for CLI execution.")
        sys.exit(1)
    else:
        run_gui()


if __name__ == "__main__":
    main()
