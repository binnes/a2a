# Documentation Rules

## Documentation Location

**CRITICAL RULE**: All project documentation MUST be added to the MkDocs documentation in the `docs/` directory.

### Requirements

1. **No Standalone Documentation Files**: Do not create standalone documentation files (like DEPLOYMENT_PLAN.md, DEPLOYMENT_SUMMARY.md, etc.) in project directories
2. **Brief READMEs Only**: Only create brief README.md files in project directories that:
   - Provide a quick overview
   - Link to the full documentation in `docs/`
   - Include essential quick-start commands
3. **MkDocs Integration**: All comprehensive documentation must be:
   - Written as Markdown files in `docs/docs/`
   - Added to the navigation in `docs/mkdocs.yml`
   - Properly structured and organized

### Documentation Structure

```
docs/
├── mkdocs.yml              # Navigation configuration
├── docs/
│   ├── index.md           # Home page
│   ├── architecture/      # Architecture docs
│   ├── protocols/         # Protocol docs
│   ├── rag/              # RAG agent docs
│   └── deployment/       # Deployment docs (add here)
└── site/                 # Generated site (gitignored)
```

### Process

When creating documentation:

1. **Create MkDocs Pages**: Write comprehensive documentation in `docs/docs/[section]/`
2. **Update Navigation**: Add pages to `docs/mkdocs.yml` nav section
3. **Create Brief README**: Add minimal README in project directory with:
   - One-paragraph overview
   - Link to full docs
   - Essential commands only
4. **No Duplication**: Never duplicate content between README and MkDocs docs

### Example README Format

```markdown
# [Component Name]

Brief one-paragraph description.

## Quick Start

```bash
# Essential commands only
command1
command2
```

## Documentation

For complete documentation, see [Component Documentation](../../docs/docs/section/page.md).
```

### Enforcement

- Always check if documentation should go in MkDocs before creating files
- If creating comprehensive docs, use MkDocs
- If creating quick reference, use brief README with link to MkDocs
- Never create standalone documentation files like PLAN.md, SUMMARY.md, GUIDE.md, etc.