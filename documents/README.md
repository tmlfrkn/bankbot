# Documents Directory

This directory contains source documents for the BankBot knowledge base ingestion pipeline.

## Document Types and Access Levels

Based on the Access Level Matrix from the Technical Proficiency Test:

| Document Type | Access Level | Description |
|---------------|--------------|-------------|
| Public Product Info | 1 | Publicly available product information |
| Internal Procedures | 2 | Internal operational procedures and workflows |
| Regulatory Docs | 3 | Regulatory compliance documents and guidelines |
| Risk Models | 4 | Risk assessment models and methodologies |
| Executive Reports | 5 | Executive-level reports and strategic documents |
| Investigation Reports | 5 | Investigation reports and sensitive findings |

## File Naming Convention

To properly assign access levels during ingestion, use the following prefixes:

- `public_*` - Level 1 (Public)
- `internal_*` - Level 2 (Internal)
- `regulatory_*` - Level 3 (Confidential)
- `risk_*` - Level 4 (Restricted)
- `executive_*` - Level 5 (Executive)
- `investigation_*` - Level 5 (Executive)

## Supported File Types

- PDF documents (.pdf)
- Text files (.txt)
- Markdown files (.md)

## Usage

1. Place your source documents in this directory
2. Run the ingestion script: `python ingest.py`
3. The script will process all documents and insert them into the database 