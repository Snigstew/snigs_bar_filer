# snigs_bar_filer

Digital filing of barcoded documents

# Barcode Filing System

This script is a simple barcode filing system designed to organize scanned documents based on detected barcodes. It processes image files, converts them if needed, and files them into folders based on user-defined rules.

## Features

- Processes images in a target directory using the `PIL` and `pdf2image` libraries.
- Supports barcode recognition and sorting based on regular expressions.
- Redirects unprocessable or ambiguous scans to a separate review directory.
- Automatically generates a `.json` preferences file from user-supplied data files.

## Directory Structure

The script uses three main directories:

1. **Target Directory**  
   The location of images to be processed. Images are resampled to reduce scanning error. Valid barcodes are matched using the regex pattern provided in `regex.txt`. Images without valid or unambiguous barcodes are excluded.

2. **Review Directory**  
   Stores images with failed scans: either no valid barcode was detected or multiple valid barcodes were found (making the result ambiguous).

3. **Working Directory**  
   The script's execution folder. This must include:
   - Required data files (see below)
   - The Poppler library (used for PDF processing via `pdf2image`)

## Required Data Files

All data files must be located in the working directory:

- **`barcodes.csv`**  
  A CSV file listing valid barcode types, followed by a delimiter.  
  Example:  
	```CODE128,CODE39,I25,2```

The delimiter determines how much of the barcode string is used for folder naming.  
Example:  
Barcode `AS25012345` with delimiter `2` → filed in `AS/`  
Delimiter `4` → filed in `AS25/`

- **`department.txt`**  
A single line indicating the department or context.

- **`paths.txt`**  

```
Line 1 → path to target directory
Line 2 → path to review directory
Line 3 → path to working directory
```

- **`regex.txt`**  
Contains the regular expression used to identify valid barcodes. Test it carefully (e.g., [regex101](https://regex101.com)) to avoid false positives/negatives.

## JSON Configuration Cache

After the first run, the script creates a `.json` file storing the parsed configuration.  
**If any data files are modified**, delete the `.json` file to force regeneration using the updated files.

## Performance Tips

Choose a delimiter based on your expected document volume.  
Example: If your barcodes are 8-digit numeric codes, a delimiter of 4 gives you folders containing up to 10,000 documents each (0000–9999).

## Requirements

- Python 3.x
- `PIL` (Pillow)
- `pdf2image`
- Poppler (must be in the working directory in a folder called 'poppler' with 'poppler\Library\bin' as valid path)

## License

This script and its dependencies are licensed under the open source MIT-CMU License

## Author

David Shorten

