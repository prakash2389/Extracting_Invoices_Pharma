import openai
import json
import re
import os
from dotenv import load_dotenv
import pandas as pd
from unstract.llmwhisperer import LLMWhispererClientV2
from anthropic import Anthropic, APIError

openai.api_type = os.getenv("OPENAI_API_KEY")
openai.api_base = os.getenv("OPENAI_API_KEY")
openai.api_version = "2023-03-15-preview"
openai.api_key = os.getenv("OPENAI_API_KEY")

claude_client = Anthropic(api_key=os.getenv("Anthropic_API_KEY"))

def get_claude_response(prompt):
    try:
        message = claude_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=2000,
            temperature=0,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return message.content[0].text

    except APIError as e:
        print(f"An API error occurred: {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
def get_prompt35_output(prompt):
    input_messages = [
        {"role": "system",
         "content": "You are an Invoice Information Extraction Expert. You have an impeccable performance in Extracting Relevant Information from provided Invoice. "
                    "Extract relevant fields from the provided invoice. Be precise, clear, complete and to the point in your extraction. "
                    "Respond only with information that is explicitly mentioned in the Invoice. Do not include extra details or interpretations outside the Invoice. "
                    "Prioritize accuracy and relevance while generating the response."
         },
        {"role": "user",
         "content": prompt}
    ]
    response = openai.ChatCompletion.create(engine="gpt-35-turbo-16k",
                                            messages=input_messages,
                                            temperature=0,
                                            max_tokens=2000)

    text = response.choices[0].message.content
    return extract_substring_after_first(text, "\n\n")
def run_openai_key(read_output, keypairs, key_fields_Description):
    keypairsprompt = f"Below is a sample of fields description \n {key_fields_Description}.\n\n\n" \
                     f"Extract key-value pairs {keypairs} " \
                     f"from the below text and separate them by line \n\n" \
                     f"Document text: {read_output} \n\n" \
                     f"""Guidelines:\n\n \
                        1. Since, E_Invoice and RCM_Applicability are Yes/No type fields, both should contain only boolean values.
                        2. Return `None` if not able to find it in the Invoice.
                        3. Extract all `Amount` related values without including any thousands separators (e.g., commas or spaces) or currency symbols (e.g., Rs. or $ or ₹) in the output (e.g., "$1,234.56" should be extracted as "1234.56").
                        4. Return all Rate related fields with Percentage sign at the end.
                        5. Standardize the `Currency` field using the three-letter ISO 4217 currency code.\n\n"""\
                     f"Entities:"
    keypairstext = get_prompt35_output(keypairsprompt)
    print(keypairsprompt)
    return keypairstext
def run_openai_line(read_output):
    linetableprompt = f"Extract  HSN/SAC Code, Item_Description, Item_Code, Pack, MRP, Quantity, UnitPrice, Total Tax, CGST Rate, CGST Amount, SGST Rate, SGST Amount, IGST Rate, IGST Amount, Total Amount \n\n \
            from the below text for all line items and separate them by | for each line item and separate by ,, for each field  \
            example: HSN/SAC Code: 1234,,Item_Description: Item1,,Item_Code: 1234,,Pack: 1 Pcs,,MRP: 100.00,,Quantity: 1,,UnitPrice: 100,,Total Tax: 20,,CGST Rate: 10,,CGST Amount: 10,,SGST Rate: 10,,SGST Amount: 10,,IGST Rate: 0,,IGST Amount: 0,,Total Amount: 200,,\n\n \
            Text:{read_output} \n\n \
            Guidelines for extraction: \n \
                1. Carefully identify how many line items are there in the whole invoice and provide your response in accurate format as explained in the example.\n \
                2. Sometimes Item_Code might not present in the Invoice, so return `None` value in that case.\n \
                3. Return all Amount related fields in numerical format such as Integer or Float, without using thousands separator like comma.\n \
                4. If both CGST Rate, SGST Rate, CGST Amount, and SGST Amount are all provided for a particular line item, return both IGST Rate and IGST Amount as `None`.\n \
                5. Conversely, if IGST Rate and IGST Amount are provided, return both CGST Rate, CGST Amount, SGST Rate, and SGST Amount as `None`.\n \
                6. Note that for any given line item, either CGST and SGST (with their respective Rate and Amount) will be provided, or IGST (with its Rate and Amount) will be provided, but **not** both. This means the rates and amounts of CGST & SGST and IGST are mutually exclusive (i.e., one set of rates and amounts will exist, not both).\n \
                7. Identify the invoicing currency and put the `UnitPrice` field with accurate prefix.\n \
                8. Identify the quantity unit accurately and put the `Quantity` field with accurate suffix.\n \
                9. Return all `Rate` related fields with Percentage sign at the end.\n\n \
            Entities:"
    linetabletext = get_prompt35_output(linetableprompt)
    return linetabletext, linetableprompt
def convertlineitems_to_dict(input_string):
    result = {}
    lines = input_string.split('\n')
    keypairs = []
    for line in lines:
        if len(line) < 2:
            continue
        try:
            split_values = line.split(':')  # Split each line by colon (:)
            keypairs.append(split_values[0].strip())
            if len(split_values) == 1:
                if keypairs.count(split_values[0].strip()) == 1:
                    key = split_values[0].strip() + "_1"
                else:
                    key = split_values[0].strip() + "_" + str(keypairs.count(split_values[0].strip()))
                result[key] = ''
            elif len(split_values) == 2:
                if keypairs.count(split_values[0].strip()) == 1:
                    key = split_values[0].strip() + "_1"
                else:
                    key = split_values[0].strip() + "_" + str(keypairs.count(split_values[0].strip()))
                value = split_values[1].strip()
                result[key] = value
            elif len(split_values) > 2:
                if keypairs.count(split_values[0].strip()) == 1:
                    key = split_values[0].strip() + "_1"
                else:
                    key = split_values[0].strip() + "_" + str(keypairs.count(split_values[0].strip()))
                value = ':'.join(split_values[1:]).strip()
                result[key] = value
        except ValueError:
            print(line)
            continue  # Ignore lines that don't contain a colon (:)
    return result
def convert_to_lineitem_dict(input_string):
    result = {}
    line_items = input_string.split("||")
    sequence_number = 1
    for line_item in line_items:
        lines = line_item.split('\n')
        print(len(lines))
        for line in lines:
            if len(line) < 2:
                continue
            try:
                split_values = line.split(':')  # Split each line by colon (:)
                if len(split_values) == 1:
                    key = split_values[0].strip()
                    result[key] = ''
                elif len(split_values) == 2:
                    key = split_values[0].strip()
                    value = split_values[1].strip()
                    result[key] = value
                elif len(split_values) > 2:
                    key = split_values[0].strip()
                    value = ':'.join(split_values[1:]).strip()
                    result[key] = value
            except ValueError:
                print(line)
                continue  # Ignore lines that don't contain a colon (:)
    sequence_number += 1
    return result
def extract_substring_after_first(string, search_substring):
    index = string.find(search_substring)
    if index != -1:
        substring = string[index + len(search_substring):]
        return substring.strip()
    else:
        return string
def analyze_po_order_new(file_path):
    read_output = get_final_text(file_path)
    return read_output
def linetable_dict_convert(linetabletext):
    linetable_dict = convertlineitems_to_dict(linetabletext)
    linetable_dict = {**linetable_dict}
    for key, value in linetable_dict.items():
        if key.startswith('Quantity_'):
            try:
                linetable_dict[key] = re.search(r'\d+(\.\d+)?', str(value)).group()
            except:
                pass
        if key.startswith('Price_'):
            try:
                linetable_dict[key] = re.search(r'\d+(?:,\d+)*(?:\.\d+)?', str(value)).group()
            except:
                pass
        if key.startswith('Tax_'):
            try:
                linetable_dict[key] = re.search(r'\d+(?:,\d+)*(?:\.\d+)?', str(value)).group()
            except:
                pass
        if key.startswith('ExtendedPrice/LineValue/NetValue_'):
            try:
                linetable_dict[key] = re.search(r'\d+(?:,\d+)*(?:\.\d+)?', str(value)).group()
            except:
                pass
    linetable_df = pd.DataFrame(data=linetable_dict, index=[0])
    linetable_df = linetable_df.T
    linetable_df.reset_index(inplace=True)
    linetable_df.columns = ["key", "value"]
    linetable_df['source'] = 'OpenAI Linetable'
    return linetable_dict, linetable_df
def key_dict_convert(keypairstext):
    key_dict = convert_to_lineitem_dict(keypairstext)
    key_dict = {**key_dict}
    try:
        key_dict['Invoice/PO/Order Total'] = re.search(r'\d+(?:,\d+)*(?:\.\d+)?', str(key_dict['Invoice/PO/Order Total'])).group()
    except:
        pass
    keypairs_df = pd.DataFrame(data=key_dict, index=[0])
    keypairs_df = keypairs_df.T
    keypairs_df.reset_index(inplace=True)
    keypairs_df.columns = ["key", "value"]
    keypairs_df['source'] = 'OpenAI KeyValue'
    return keypairs_df
def run(filepath, keypairs, key_fields_Description):
    # read_output = analyze_po_order_new(filepath)
    read_output = get_layout_from_pdf_whisperer(filepath)
    keypairstext = run_openai_key(read_output, keypairs, key_fields_Description)
    keypairs_df = key_dict_convert(keypairstext)
    keypairs_df = keypairs_df[["key", "value"]]
    keypairs_df.columns = ["Field", "Extracted Value"]
    try:
        m = 0
        while True:
            m = m + 1
            linetabletext, linetableprompt = run_openai_line(read_output)
            if ((",," in linetabletext) or m>3):
                break  # Exit the loop if condition is met
            else:
                linetabletext = get_claude_response(linetableprompt)
                if ((",," in linetabletext) or m > 3):
                    break  # Exit the loop if condition is met
        k = []
        for y in [x.split(",,") for x in linetabletext.split("\n")]:
            k.append([i.split(":")[1].strip() for i in y if ":" in i])
        linetable_df = pd.DataFrame(k)
        linetable_df.columns = ["HSN/SAC Code", "Item_Description", "Item_Code", "Pack", "MRP", "Quantity", "Unit Price", "Total Tax", "CGST Rate",
                                "CGST Amount", "SGST Rate", "SGST Amount", "IGST Rate", "IGST Amount", "Total Amount"]
        linetable_df['item_id'] = range(1, len(linetable_df) + 1)
        linetable_df = linetable_df[['item_id'] + [col for col in linetable_df.columns if col != 'item_id']]
        linetable_df['item_id'] = linetable_df['item_id'].astype(str)
        return [read_output, keypairs_df, linetable_df]
    except:
        return [read_output, keypairs_df]
def get_layout_from_pdf_whisperer(file_path):
    whisperer_base_url = "https://llmwhisperer-api.us-central.unstract.com/api/v2"
    # whisperer_api_key = "pU9WJLt-JLYcqpHXXY-uzlaudk1MyIiJuVus6W5plKE" ## Ganesh
    whisperer_api_key = "dK7ncqZd5lEM1T4nmqtAalnUHuiovY76FDty_CPAVok" ## Prakash
    client = LLMWhispererClientV2(base_url=whisperer_base_url, api_key=whisperer_api_key)
    mode = 'high_quality'
    output_mode = 'layout_preserving'
    result = client.whisper(
        file_path=file_path,
        mode=mode,
        output_mode=output_mode if output_mode != "None" else None,
        wait_for_completion=True,
        wait_timeout=200,
    )
    return result.get("extraction", {}).get("result_text", "")



temp_file_path = r"D:\Pharma\Results\Intermedics invoice copy.pdf"

KeyFields = "Vendor name, Vendor Address, PO Number, Billing-Indira IVF address, Shipping-Indira IVF address, Vendor Invoice number, Vendor Invoice date, Sub Total Amount, CGST Amount, SGST Amount, IGST Amount, Grand Total Amount, Vendor GST Number, FSSAI Number, Vendor GST amount, Indira IVF GST number"
key_fields_Description = """
\nField Descriptions are Below

Field: Vendor_Name
Description: The name of the vendor or supplier providing goods or services.

Field: Vendor_Address
Description: The complete address of the vendor, including street name, city, state, and postal code.

Field: PO Number
Description: Purchase order number or Buyer order number

Field: Billing_Indira_IVF_Address
Description: The address where the bill is sent for payment, associated with Indira IVF (assumed to be the company).

Field: Shipping_Indira_IVF_Address
Description: The address where goods or services are delivered, linked to Indira IVF.

Field: Vendor_Invoice_Number
Description: A unique identifier assigned to the invoice by the vendor for tracking and reference purposes.

Field: Vendor_Invoice_Date
Description: The date the invoice was issued by the vendor.

Field: Sub_Total_Amount
Description: The total monetary value of the invoice, excluding GST and any other applicable charges.

Field: CGST_Amount
Description: The total CGST Amount of the invoice.

Field: SGST_Amount
Description: The total SGST Amount of the invoice.

Field: IGST_Amount
Description: The total IGST Amount of the invoice.

Field: Gross_Total_Amount
Description: The total monetary value of the invoice, including GST and any other applicable charges.

Field: Gross_Total_Amount
Description: The total monetary value of the invoice, including GST and any other applicable charges.

Field: Vendor_GST_Number
Description: The vendor's unique GST (Goods and Services Tax) registration number, used for taxation purposes.

Field: FSSAI_Number
Description: The vendor's unique FSSAI (Food Safety and Standards Authority of India) license number, required for food-related businesses.

Field: Vendor_GST_Amount
Description: The portion of the total amount that accounts for GST charged by the vendor.

Field: Indira_IVF_GST_Number
Description: The unique GST registration number associated with Indira IVF for claiming input tax credits and taxation compliance.
\n"""

outputs = run(temp_file_path, KeyFields, key_fields_Description)
if len(outputs) == 3:
    read_output, keypairs_df, linetable_df = outputs
    linetable_df = linetable_df[linetable_df['HSN/SAC Code'].fillna('').str.match(r'^(?=.*\d)[A-Za-z0-9.\-]*$')]
else:
    read_output, keypairs_df = outputs
    linetable_df = None
print(keypairs_df)
print(linetable_df)

keypairs_df.to_json(r"D:\Pharma\Results\keypairs_df.json", orient='records')

keypairs_json_data = keypairs_df.to_json(orient="records")
linetable_json_data = linetable_df.to_json(orient="records")
json_data = "null"

# Safe conversion
if keypairs_df is not None:
    keypairs_json_data = keypairs_df.to_json(orient="records")
else:
    keypairs_json_data = "null"
if linetable_df is not None:
    linetable_json_data = linetable_df.to_json(orient="records")
else:
    linetable_json_data = "null"
