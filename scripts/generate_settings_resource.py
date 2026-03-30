import re  # Regular expression module for pattern matching in text
import json  # JSON module for serializing parsed settings to JSON format
import os  # OS module for filesystem path operations and directory creation


def parse_settings(markdown_path):
    """Parse WinSet registry settings documentation from a markdown file into structured data.

    This function reads a markdown file that documents Windows registry tweak categories
    and individual settings, then parses the hierarchical structure (categories > settings
    > key-value properties) into a list of nested dictionaries. Each category contains a
    list of settings, and each setting has properties extracted from markdown table rows.

    Args:
        markdown_path: Absolute or relative path to the markdown file (e.g. "docs/registry_keys.md")
                       that follows the expected format: ## Category headers, ### Setting headers,
                       and | **Property** | `Value` | table rows.

    Returns:
        A list of category dicts, each with "name" (str) and "settings" (list of setting dicts).
        Each setting dict has a "name" key plus dynamic keys parsed from table rows (e.g. "type",
        "default", "values", "description", "registry_key", "notes").
    """
    # Open the markdown documentation file and read all lines into memory
    with open(markdown_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Accumulator list that collects all parsed category dictionaries.
    # Each entry is a dict with "name" (category display name) and "settings" (list of setting dicts).
    categories = []

    # Reference to the category dict currently being populated.
    # None when no category header has been encountered yet; updated each time
    # a new "## Category N: ..." heading is found.
    current_category = None

    # Reference to the setting dict currently being populated.
    # None when no setting header has been encountered yet; updated each time
    # a new "### Setting Name" heading is found. Properties from subsequent
    # table rows are merged into this dict.
    current_setting = None

    # Precompiled regex to match category heading lines like "## Category 1: General Settings".
    # Captures the category name (group 1) after "Category N: ".
    category_re = re.compile(r"^## .*Category \d+: (.*)")

    # Precompiled regex to match setting heading lines like "### Dark Mode".
    # Captures the full setting name (group 1) after "### ".
    setting_re = re.compile(r"^### (.*)")

    # Precompiled regex to match markdown table rows containing bold property names and values,
    # e.g. "| **Type** | `REG_DWORD` |". Captures the property name (group 1, without ** markers)
    # and the value (group 2, with optional backtick wrapping).
    table_row_re = re.compile(r"^\| \*\*(.*)\*\* \| `?(.*?)`? \|")

    # Iterate over every line in the markdown file to build the parsed structure
    for line in lines:
        # Attempt to match a category heading (e.g. "## Category 2: Appearance")
        cat_match = category_re.match(line)
        if cat_match:
            # Create a new category dict with the extracted name and an empty settings list
            current_category = {
                "name": cat_match.group(
                    1
                ).strip(),  # Extracted category name, trimmed of whitespace
                "settings": [],  # Will be populated with setting dicts as they are parsed
            }
            # Append the new category to the top-level results list
            categories.append(current_category)
            continue  # Skip to next line; nothing else to process on a category header

        # Attempt to match a setting heading (e.g. "### Show File Extensions")
        set_match = setting_re.match(line)
        if set_match:
            # Create a new setting dict initialized with its display name
            current_setting = {"name": set_match.group(1).strip()}
            # Attach the setting to the current category if one exists (defensive check)
            if current_category:
                current_category["settings"].append(current_setting)
            continue  # Skip to next line; nothing else to process on a setting header

        # If we are inside a setting block, look for property table rows
        if current_setting:
            # Attempt to match a table row containing a bold property and its value
            row_match = table_row_re.match(line)
            if row_match:
                # Extract the property name (e.g. "Type", "Default", "Registry Key"),
                # strip whitespace, and lowercase it to serve as a normalized dict key
                key = row_match.group(1).strip().lower()
                # Extract the property value, strip whitespace, and remove backtick characters
                # that markdown uses to format inline code
                val = row_match.group(2).strip().replace("`", "")
                # Store the property as a key-value pair on the current setting dict
                current_setting[key] = val

    # Return the fully assembled list of categories with their nested settings
    return categories


# Entry point: runs when this script is executed directly (not imported as a module)
if __name__ == "__main__":
    # Determine the project root directory by going two levels up from this script's location
    # (scripts/ -> project root). This makes the script location-independent.
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Construct the path to the source markdown file containing registry key documentation
    markdown_path = os.path.join(base_dir, "docs", "registry_keys.md")

    # Construct the output directory path where the generated JSON resource will be written.
    # The src/resources/ directory holds runtime data consumed by the WinSet application.
    output_dir = os.path.join(base_dir, "src", "resources")

    # Ensure the output directory exists; create it (and parents) if missing
    os.makedirs(output_dir, exist_ok=True)

    # Full path to the output JSON file that the WinSet app will load at runtime
    output_path = os.path.join(output_dir, "settings.json")

    # Parse the markdown documentation into structured category/setting data
    results = parse_settings(markdown_path)

    # Serialize the parsed results to the JSON output file with 2-space indentation
    # for human readability and diff-friendliness in version control
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    # Print a summary: output file path and total number of settings across all categories
    print(
        f"Generated {output_path} with {sum(len(c['settings']) for c in results)} settings."
    )
