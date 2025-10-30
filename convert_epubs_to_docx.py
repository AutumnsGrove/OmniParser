#!/usr/bin/env python3
"""
Convert EPUB files to Markdown and DOCX for testing purposes.
"""
from pathlib import Path
from omniparser import parse_document
import sys

def epub_to_markdown(epub_path: Path, output_dir: Path) -> Path:
    """Convert EPUB to markdown file."""
    print(f"📖 Parsing {epub_path.name}...")
    doc = parse_document(str(epub_path))
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate markdown filename
    md_filename = epub_path.stem + ".md"
    md_path = output_dir / md_filename
    
    # Write markdown content
    with open(md_path, 'w', encoding='utf-8') as f:
        # Write metadata as frontmatter
        f.write("---\n")
        f.write(f"title: {doc.metadata.title or 'Unknown'}\n")
        if doc.metadata.author:
            f.write(f"author: {doc.metadata.author}\n")
        if doc.metadata.language:
            f.write(f"language: {doc.metadata.language}\n")
        f.write(f"word_count: {doc.word_count}\n")
        f.write("---\n\n")
        
        # Write title
        if doc.metadata.title:
            f.write(f"# {doc.metadata.title}\n\n")
            if doc.metadata.author:
                f.write(f"*by {doc.metadata.author}*\n\n")
        
        # Write content
        f.write(doc.content)
    
    print(f"✅ Markdown saved: {md_path}")
    return md_path

def markdown_to_docx(md_path: Path, output_dir: Path) -> Path:
    """Convert markdown to DOCX using pandoc."""
    docx_filename = md_path.stem + ".docx"
    docx_path = output_dir / docx_filename
    
    print(f"📝 Converting {md_path.name} to DOCX...")
    
    import subprocess
    try:
        subprocess.run(
            ["pandoc", str(md_path), "-o", str(docx_path)],
            check=True,
            capture_output=True
        )
        print(f"✅ DOCX saved: {docx_path}")
        return docx_path
    except subprocess.CalledProcessError as e:
        print(f"❌ Error converting to DOCX: {e}")
        print(f"stderr: {e.stderr.decode()}")
        raise
    except FileNotFoundError:
        print("❌ pandoc not found. Installing with homebrew...")
        subprocess.run(["brew", "install", "pandoc"], check=True)
        # Retry
        subprocess.run(
            ["pandoc", str(md_path), "-o", str(docx_path)],
            check=True
        )
        print(f"✅ DOCX saved: {docx_path}")
        return docx_path

def main():
    # Input directory with EPUB files
    epub_dir = Path("/Users/mini/Documents/GitHub/OmniParser/tests/fixtures/epub")
    
    # Output directories
    md_output_dir = epub_dir / "markdown_output"
    docx_output_dir = epub_dir / "docx_output"
    
    # Get all EPUB files
    epub_files = list(epub_dir.glob("*.epub"))
    
    if not epub_files:
        print("❌ No EPUB files found!")
        sys.exit(1)
    
    print(f"\n🚀 Found {len(epub_files)} EPUB files to convert\n")
    
    # Process each EPUB file
    for epub_path in epub_files:
        print(f"\n{'='*60}")
        print(f"Processing: {epub_path.name}")
        print(f"{'='*60}\n")
        
        try:
            # Convert to markdown
            md_path = epub_to_markdown(epub_path, md_output_dir)
            
            # Convert to DOCX
            docx_path = markdown_to_docx(md_path, docx_output_dir)
            
            print(f"\n✨ Successfully converted {epub_path.name}")
            
        except Exception as e:
            print(f"\n❌ Failed to convert {epub_path.name}: {e}")
            continue
    
    print(f"\n{'='*60}")
    print(f"✅ Conversion complete!")
    print(f"📁 Markdown files: {md_output_dir}")
    print(f"📁 DOCX files: {docx_output_dir}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
