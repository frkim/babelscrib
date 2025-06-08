# Logo Files

This directory contains the logo files for BabelScrib.

## Current Files

- `logo.png` - PNG version of the logo (currently used)
- `logo.svg` - SVG version of the logo (alternative)

## Customizing the Logo

To use your own logo:

1. **Replace the logo file:**
   - For PNG: Replace `logo.png` with your logo file (recommended size: 200x60 pixels)
   - For SVG: Replace `logo.svg` with your SVG logo

2. **Update the HTML template (if needed):**
   - Edit `upload/templates/upload/index.html`
   - To switch to SVG: Change `'images/logo.png'` to `'images/logo.svg'` in the src attribute

3. **Adjust logo sizing:**
   - The CSS class `.logo` controls the logo size (currently set to height: 60px)
   - Modify the height in the CSS if your logo needs different dimensions

## Logo Requirements

- **Format:** PNG or SVG recommended
- **Size:** Optimized for web (under 100KB)
- **Dimensions:** Recommended width: 150-250px, height: 40-80px
- **Background:** Transparent or solid color that works with the page design

## Current Logo Design

The default logo features:
- Blue background (#007cba)
- White "B" icon in a circle
- "BabelScrib" text
- "Document Translation" subtitle

You can create a custom logo that matches your branding while maintaining good readability and professional appearance.
