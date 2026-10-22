"""Build a legacy Blender add-on ZIP, without native dependencies or environments."""
import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "work" / "b-cad-experimental.zip")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(args.output, "w", ZIP_DEFLATED) as archive:
        archive.write(ROOT / "blender_addon/b_cad/__init__.py", "b_cad/__init__.py")
        for source in sorted((ROOT / "bcad").glob("*.py")):
            archive.write(source, "b_cad/bcad/" + source.name)
        archive.write(ROOT / "LICENSE", "b_cad/LICENSE")
        archive.write(ROOT / "NOTICE", "b_cad/NOTICE")
    print(args.output.resolve())


if __name__ == "__main__":
    main()
