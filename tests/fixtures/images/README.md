# Test Image Fixtures

This directory contains test images for integration testing of AI vision features.

## Required Test Images

Please add **10 test images** to this directory with a good mix of types:

### Recommended Mix:
- **2-3 Diagrams** (flowcharts, architecture diagrams, UML diagrams)
  - Suggested filenames: `diagram_1.png`, `diagram_2.png`, `diagram_3.png`
  - Should contain text labels and connecting lines/arrows

- **2-3 Charts** (bar charts, line graphs, pie charts)
  - Suggested filenames: `chart_1.png`, `chart_2.png`, `chart_3.png`
  - Should contain numerical data visualization

- **2-3 Photos** (real photographs, not screenshots)
  - Suggested filenames: `photo_1.jpg`, `photo_2.jpg`, `photo_3.jpg`
  - Any subject matter (landscapes, objects, people, etc.)

- **2 Screenshots** (UI screenshots, code snippets, terminal output)
  - Suggested filenames: `screenshot_1.png`, `screenshot_2.png`
  - Should contain readable text

## Image Requirements

### Format
- Supported formats: **PNG, JPEG, GIF, WebP**
- PNG recommended for diagrams/charts (better quality)
- JPEG acceptable for photos

### Size
- **Keep files under 1MB each** to minimize API costs
- Recommended dimensions: 800x600 to 1920x1080
- Smaller is better for testing (faster uploads, lower costs)

### Quality
- Images should be **clear and readable**
- Text in images should be **legible**
- Avoid blurry or low-resolution images

## Cost Considerations

Vision API calls are more expensive than text-only calls:
- Each image analysis costs ~$0.01-0.05 depending on model and image size
- 10 images × ~15 test runs = ~150 API calls
- Expected total cost: **$1.50 - $7.50** for full test suite

**Tips to minimize costs:**
- Use smaller images (resize if needed)
- Use haiku models (faster and cheaper)
- Run tests selectively during development

## Where to Find Test Images

### Free Sources:
1. **Unsplash** (https://unsplash.com) - Free photos
2. **Chart.js Examples** - Generate sample charts
3. **Draw.io** - Create simple diagrams
4. **Your own screenshots** - Capture from your desktop

### Quick Generation:
```bash
# Create a simple diagram using Python
python -c "from PIL import Image, ImageDraw, ImageFont
img = Image.new('RGB', (800, 600), color='white')
d = ImageDraw.Draw(img)
d.rectangle([50, 50, 750, 550], outline='black', width=3)
d.text((400, 300), 'Test Diagram', fill='black', anchor='mm')
img.save('tests/fixtures/images/diagram_1.png')"
```

## Current Status

**Images in this directory:**
- Run `ls -lh` in this directory to see current images

**To add images:**
```bash
# Navigate to this directory
cd tests/fixtures/images/

# Copy images from another location
cp /path/to/your/images/*.png .

# Or download from URLs
curl -o diagram_1.png "https://example.com/diagram.png"
```

## Testing

After adding images, run the vision integration tests:
```bash
# Run all vision integration tests
uv run pytest tests/integration/test_ai_vision_integration.py --run-integration -v

# Run a specific test
uv run pytest tests/integration/test_ai_vision_integration.py::TestImageAnalysisIntegration::test_analyze_single_image_anthropic --run-integration -v
```

## Notes

- Images in this directory are **gitignored by default** to avoid bloating the repository
- Add your own `.gitignore` entry if you want to commit specific test images
- For CI/CD, consider using a separate test image repository or generating images programmatically

---

**Last updated:** 2025-01-29
