Planned Enhancements
Universal Link Parser & Preprocessing
Plan: Implement a preprocessing layer that intercepts all input (file paths and URLs) before format-specific parsers. This layer will handle URL cleaning (strip tracking parameters, redirect chains), validate accessible resources, and route to appropriate parsers.
Expected Result: Any file type (PDF, DOCX, PPTX, Excel, etc.) can be parsed from either local file paths or direct URLs, with automatic cleanup of common URL artifacts. Currently HTML is the only format supporting URL input - this extends that capability universally.
Standardized Markdown Output Format
Plan: Establish conversion rules for complex document elements across all supported formats. Tables (from PDF, Excel, DOCX) convert to markdown table syntax. Charts/diagrams (from PDF, PPTX, embedded Mermaid) convert to properly fenced mermaid code blocks. Images with captions preserve alt-text and descriptive content.
Expected Result: Regardless of input format, output maintains maximum fidelity to source content while conforming to clean, standard markdown conventions. Research papers with mixed charts, tables, and images parse into well-structured, readable markdown documents.
Comprehensive Test Suite
Plan: Create test_links.md (or similar) containing curated URLs to real-world documents alongside existing fixture files. Expand PDF fixtures specifically - include academic papers with complex layouts, forms with tables, documents with mixed text/image content, and edge cases designed to challenge parser stability.
Expected Result: Robust testing coverage that intentionally stress-tests the parser. When the parser “gets destabilized” by unusual formatting, we catch it in tests rather than production use.
Web Interface
Plan: Build a web-based frontend for OmniParser with file upload/URL input, format selection, and result display.
Expected Result: Users can interact with OmniParser through a browser without command-line knowledge. Lowers barrier to entry and enables sharing/demonstration.
Process Visualization
Plan: Add visual progress tracking showing each parsing stage (preprocessing → format detection → extraction → markdown conversion) with intermediate outputs viewable at each step.
Expected Result: Users can observe the transformation pipeline in real-time and debug issues by examining where in the process unexpected results occur. Useful for development and for users understanding what the parser does.