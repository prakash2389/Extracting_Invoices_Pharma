# Invoice Processing System

A Python-based system for extracting and processing information from invoice PDFs using multiple AI models including OpenAI's GPT and Anthropic's Claude.

## Overview

This system processes invoice PDFs to extract key fields and line items using a combination of AI models and text processing techniques. It supports extraction of vendor details, invoice information, GST details, and line items with their respective HSN codes, descriptions, and tax information.

## Features

- PDF text extraction with layout preservation
- Key field extraction including:
  - Vendor information (name, address, GST number)
  - Invoice details (number, date, amounts)
  - Billing and shipping addresses
  - Tax information (CGST, SGST, IGST)
- Line item extraction with:
  - HSN/SAC codes
  - Item descriptions and codes
  - Quantities and prices
  - Tax breakdowns
- Support for both CGST+SGST and IGST scenarios
- Output in both DataFrame and JSON formats

## Prerequisites

```python
pip install openai
pip install pandas
pip install anthropic
pip install unstract-llmwhisperer
```

## Configuration

The system requires the following API keys:

1. Azure OpenAI API:
   - API Type: Azure
   - Base URL: Your Azure OpenAI endpoint
   - API Version: 2023-03-15-preview
   - API Key: Your Azure OpenAI key

2. Anthropic Claude API:
   - API Key: Your Anthropic API key

3. LLM Whisperer API:
   - Base URL: LLM Whisperer endpoint
   - API Key: Your LLM Whisperer key

## Usage

1. Import the required modules:
```python
from invoice_processor import run
```

2. Prepare your input parameters:
```python
file_path = "path/to/your/invoice.pdf"
key_fields = "Vendor name, Vendor Address, PO Number, ..."
key_fields_description = """Your field descriptions..."""
```

3. Run the processor:
```python
outputs = run(file_path, key_fields, key_fields_description)
```

4. Handle the outputs:
```python
if len(outputs) == 3:
    read_output, keypairs_df, linetable_df = outputs
    # Process both key-value pairs and line items
else:
    read_output, keypairs_df = outputs
    # Process only key-value pairs
```

## Output Format

The system provides two main output DataFrames:

1. `keypairs_df`: Contains extracted key-value pairs
   - Columns: ["Field", "Extracted Value"]

2. `linetable_df`: Contains line item details
   - Columns: ["item_id", "HSN/SAC Code", "Item_Description", "Item_Code", "Pack", "MRP", "Quantity", "Unit Price", "Total Tax", "CGST Rate", "CGST Amount", "SGST Rate", "SGST Amount", "IGST Rate", "IGST Amount", "Total Amount"]

## Error Handling

The system includes:
- API error handling for both OpenAI and Claude
- Retry mechanism for line item extraction
- Validation for HSN/SAC codes
- Proper handling of missing data

## Limitations

- Requires valid API keys for all services
- PDF must be text-searchable
- Performance depends on PDF quality and layout
- Rate limits apply based on API provider restrictions

## Best Practices

1. Keep API keys secure and never commit them to version control
2. Monitor API usage and costs
3. Validate extracted data before use in production
4. Handle potential API timeouts and errors gracefully
5. Regular testing with different invoice formats

## Contributing

Feel free to submit issues and enhancement requests.

## License

[Specify your license here]
