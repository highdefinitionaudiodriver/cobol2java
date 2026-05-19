"""Quick test script to verify conversion works."""
import os
import sys
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.cobol_parser import CobolParser
from src.oop_transformer import OopTransformer, TransformOptions
from src.java_generator import JavaCodeGenerator


def test_conversion():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    samples_dir = os.path.join(base_dir, "samples")
    # Use temp dir to avoid Google Drive sync locks
    import tempfile
    output_dir = os.path.join(tempfile.gettempdir(), "cobol2java_test_output")

    # Clean output
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir, ignore_errors=True)
    os.makedirs(output_dir, exist_ok=True)

    options = TransformOptions(
        package_name="com.example.migrated",
        generate_getters_setters=True,
        use_big_decimal=True,
        generate_javadoc=True,
        extract_data_classes=True,
        extract_enums=True,
        extract_file_handlers=True,
        group_related_paragraphs=True,
    )

    parser = CobolParser(encoding="utf-8")
    transformer = OopTransformer(options)
    generator = JavaCodeGenerator(options)

    for filename in os.listdir(samples_dir):
        if filename.endswith((".cbl", ".cob", ".cobol")):
            filepath = os.path.join(samples_dir, filename)
            print(f"\n{'='*60}")
            print(f"Processing: {filename}")
            print(f"{'='*60}")

            # Parse
            program = parser.parse_file(filepath)
            print(f"  Program ID: {program.program_id}")
            print(f"  Working Storage: {len(program.working_storage)} items")
            print(f"  Paragraphs: {len(program.paragraphs)}")
            print(f"  Sections: {len(program.sections)}")
            print(f"  Files: {len(program.files)}")

            # Transform
            project = transformer.transform(program)
            print(f"  Main class: {project.main_class.name if project.main_class else 'None'}")
            print(f"  Data classes: {[c.name for c in project.data_classes]}")
            print(f"  Enums: {[c.name for c in project.enum_classes]}")
            print(f"  File handlers: {[c.name for c in project.file_handler_classes]}")
            print(f"  Services: {[c.name for c in project.service_classes]}")

            # Generate
            file_output = os.path.join(output_dir, program.program_id or "unknown")
            generator.generate_project(project, file_output)
            print(f"  Output: {file_output}")

    # List generated files
    print(f"\n{'='*60}")
    print("Generated files:")
    print(f"{'='*60}")
    for root, dirs, files in os.walk(output_dir):
        level = root.replace(output_dir, "").count(os.sep)
        indent = "  " * level
        print(f"{indent}{os.path.basename(root)}/")
        sub_indent = "  " * (level + 1)
        for f in files:
            size = os.path.getsize(os.path.join(root, f))
            print(f"{sub_indent}{f} ({size} bytes)")

    print("\nTest complete!")


if __name__ == "__main__":
    test_conversion()
