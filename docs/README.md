# L2M Thesis Defense Presentation

This directory contains presentation materials for the L2M thesis defense.

## Files

- **`project_documentation.md`** - Full thesis documentation in journal article format
- **`presentation_slides.md`** - Presentation slides (23 slides)

## Presentation Slides

The slides are created in **Marp** markdown format for easy editing and conversion to various formats.

### Viewing Options

#### Option 1: Convert to PowerPoint (Recommended)

**Using Marp CLI:**

```bash
# Install Marp CLI
npm install -g @marp-team/marp-cli

# Convert to PowerPoint
marp presentation_slides.md -o presentation_slides.pptx

# Or convert to PDF
marp presentation_slides.md -o presentation_slides.pdf
```

#### Option 2: View as HTML

```bash
# Generate HTML presentation
marp presentation_slides.md -o presentation_slides.html

# Open in browser
open presentation_slides.html
```

#### Option 3: Use Marp for VS Code

1. Install the "Marp for VS Code" extension
2. Open `presentation_slides.md`
3. Click "Open Preview" or press `Cmd+K V`
4. Export to PowerPoint/PDF from the preview

#### Option 4: Manual Transfer to PowerPoint

1. Open PowerPoint
2. Create a new presentation with minimalistic theme
3. Copy slide content from `presentation_slides.md`
4. Apply consistent formatting

### Slide Structure (23 slides)

1. **Title Slide** - Project title and author
2. **The Challenge** - Problem statement
3. **Our Solution** - L2M overview
4. **Example** - Quick demonstration
5. **Agenda** - Presentation outline
6. **Part 1 Divider** - Background & Related Work
7. **Why This Matters** - Motivation
8. **Related Work Evolution** - Literature review table
9. **Research Gap** - Our contribution
10. **Part 2 Divider** - System Architecture
11. **Pipeline Overview** - Mermaid diagram
12. **Stage 1-2** - Lyrics parsing & emotion analysis
13. **Stage 3** - Melody generation
14. **Emotion-to-Key Mapping** - Reference table
15. **Stage 4-6** - Output generation
16. **Part 3 Divider** - Implementation
17. **Technology Stack** - Tech overview
18. **Key Components** - System modules
19. **Prompt Engineering** - LLM techniques
20. **Part 4 Divider** - Evaluation & Results
21. **Evaluation Methodology** - Test approach
22. **Results Summary** - Metrics table
23. **Example Output** - Hopeful lyrics demo
24. **Strengths** - System advantages
25. **Limitations** - Known constraints
26. **Part 5 Divider** - Future Directions
27. **Future Enhancements** - Roadmap
28. **Conclusion Divider** - Final thoughts
29. **Key Contributions** - Summary of contributions
30. **Thank You** - Closing slide

### Design Principles

The presentation follows **minimalistic design**:

- Clean, uncluttered layouts
- Consistent typography
- Strategic use of emojis for visual interest
- Limited color palette (grayscale + accents)
- Clear hierarchy with headers and bullet points
- Visual elements (diagrams, tables) for clarity
- "Lead" slides for section dividers

### Customization

To customize the presentation:

1. **Colors**: Edit the frontmatter at the top of `presentation_slides.md`
   ```yaml
   backgroundColor: #fff
   color: #333
   ```

2. **Theme**: Change the theme in the frontmatter
   ```yaml
   theme: gaia  # or uncover, default, etc.
   ```

3. **Fonts**: Add custom CSS in a separate theme file

4. **Slide Content**: Edit the markdown directly

### Presentation Tips

- **Timing**: ~25-30 minutes for 23 slides (~1-1.5 min per slide)
- **Focus**: Emphasize architecture, results, and contributions
- **Demo**: Consider live demo of the system during "Example" slide
- **Q&A**: Prepare for questions about LLM dependency, fallback quality, and evaluation

### Converting to Other Formats

**PDF:**
```bash
marp presentation_slides.md --pdf --allow-local-files -o presentation.pdf
```

**PNG Images (one per slide):**
```bash
marp presentation_slides.md --images png -o slides
```

**Google Slides:**
1. Convert to PPTX first
2. Upload to Google Drive
3. Open with Google Slides

## Additional Resources

- Full documentation: `thesis_documentation.md`
- Original project README: `../README.md`
- Example code: `../example_usage.py`

---

**For questions or issues, please contact the author.**
