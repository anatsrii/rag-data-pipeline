# Odoo 19 Documentation Example

Example implementation crawling Odoo 19 documentation.

## Files

- `urls.txt` - Discovered URLs from Odoo documentation
- `scheduled_update.py` - Manual update script
- `docs/SCHEDULED_UPDATE.md` - Update guide

## Usage

```bash
cd examples/odoo

# Crawl
python ../../src/pipeline.py --urls urls.txt

# Or use scheduled update
python scheduled_update.py --full
```

See `docs/SCHEDULED_UPDATE.md` for detailed instructions.
