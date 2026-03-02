#!/usr/bin/env python3
"""
Crawl OCA Thailand Localization
================================

Crawl OCA l10n-thailand for Thai Odoo developers.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.mcp_tools import SourceTools

print("=== Crawl OCA Thailand Localization ===\n")

# OCA Thailand URLs
thailand_urls = [
    # Main repo
    "https://github.com/OCA/l10n-thailand",
    "https://github.com/OCA/l10n-thailand/blob/17.0/README.md",
    
    # Key modules
    "https://github.com/OCA/l10n-thailand/tree/17.0/l10n_thailand_tax_invoice",
    "https://github.com/OCA/l10n-thailand/tree/17.0/l10n_thailand_withholding_tax",
    "https://github.com/OCA/l10n-thailand/tree/17.0/l10n_thailand_account_tax",
    "https://github.com/OCA/l10n-thailand/tree/17.0/l10n_thailand_gov_purchase_request",
    "https://github.com/OCA/l10n-thailand/tree/17.0/l10n_thailand_gov_tier_validation",
    "https://github.com/OCA/l10n-thailand/tree/17.0/l10n_thailand_partner_address",
    "https://github.com/OCA/l10n-thailand/tree/17.0/l10n_thailand_promptpay",
    "https://github.com/OCA/l10n-thailand/tree/17.0/l10n_thailand_bank_payment_export",
    
    # Wiki and docs
    "https://github.com/OCA/l10n-thailand/wiki",
]

print(f"[Step 1/2] Preparing {len(thailand_urls)} URLs...")

# Create source
tools = SourceTools()

# Delete if exists
existing = tools.list_sources()
if any(s['name'] == 'oca_thailand' for s in existing):
    print("Source exists, deleting old...")
    tools.delete_source('oca_thailand')

print("[Step 2/2] Creating source...")

result = tools.add_source(
    name='oca_thailand',
    urls=thailand_urls,
    category='oca',
    description='OCA Thailand Localization - Thai Odoo modules',
    chunk_size=1000
)

if result['success']:
    print(f"✅ Source created: {result['name']}")
    print(f"   URLs: {result['urls_count']}")
    print("\nModules included:")
    print("  - Tax Invoice (ใบกำกับภาษี)")
    print("  - Withholding Tax (ภาษีหัก ณ ที่จ่าย)")
    print("  - PromptPay (พร้อมเพย์)")
    print("  - Government Purchase (งานราชการ)")
    print("\nRun MCP server to crawl and index")
else:
    print(f"❌ Failed: {result.get('error')}")
