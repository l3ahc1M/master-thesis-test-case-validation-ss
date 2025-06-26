import json
import os


def extract_tables_from_openapi(openapi_spec):
    """
    Extract table and column metadata from an OpenAPI specification.
    Filters for schemas used in GET methods and ensures only tables with
    more than one meaningful column are included.
    """
    print("Extracting tables from OpenAPI specification...")

    # Extract schema definitions and API paths
    components = openapi_spec.get("components", {})
    schemas = components.get("schemas", {})
    paths = openapi_spec.get("paths", {})

    get_schema_refs = set()  # Will store references to schemas used in GET responses

    # Collect schema references from GET responses
    for path, methods in paths.items():
        for method, details in methods.items():
            if method.lower() != "get":
                continue  # Ignore non-GET methods

            print(f"Analyzing GET method at path: {path}")
            responses = details.get("responses", {})
            for response in responses.values():
                content = response.get("content", {})
                for media_type in content.values():
                    schema = media_type.get("schema", {})
                    if "$ref" in schema:
                        # Reference to a named schema
                        ref_name = schema["$ref"].split("/")[-1]
                        print(f"   Found schema reference: {ref_name}")
                        get_schema_refs.add(ref_name)
                    elif "items" in schema and "$ref" in schema["items"]:
                        # Reference inside an array
                        ref_name = schema["items"]["$ref"].split("/")[-1]
                        print(f"   Found items schema reference: {ref_name}")
                        get_schema_refs.add(ref_name)

    print(f"Found GET schema references: {get_schema_refs}")

    tables = []

    # Loop over all available schemas
    for schema_name, schema in schemas.items():
        print(f"Processing schema: {schema_name}")

        # Skip schemas not used in GET methods
        if schema_name not in get_schema_refs:
            print(" - Skipped (not used in a GET endpoint)")
            continue

        # Skip if schema isn't an object or lacks properties
        if schema.get("type") != "object" or not schema.get("properties"):
            print(" - Skipped (not an object or has no properties)")
            continue

        columns = []  # Will store column metadata

        # Process each property as a potential column
        for prop_name, prop in schema.get("properties", {}).items():
            if not isinstance(prop, dict) or not prop:
                print(f"   - Skipped column '{prop_name}' (invalid or empty definition)")
                continue

            # Prefer title, fall back to description, append example if available
            description = prop.get("title", "") or prop.get("description", "")
            example = prop.get("example")
            if example is not None:
                description += f" Example: {example}"

            column = {
                "name": prop_name,
                "description": description,
                "format": prop.get("format", prop.get("type", "string"))
            }
            columns.append(column)
            print(f"   - Column added: {prop_name}")

        # Only include tables with more than one descriptive column
        non_empty_columns = [col for col in columns if col["description"] or col["format"]]
        if len(non_empty_columns) <= 1:
            print(f" - Skipped (only {len(non_empty_columns)} non-empty column(s))")
            continue

        table = {
            "name": schema_name.split(".")[-1],
            "description": schema.get("description", "").strip(),
            "columns": non_empty_columns
        }
        tables.append(table)
        print(f" - Table '{table['name']}' added with {len(non_empty_columns)} columns")

    print("Table extraction complete.")
    return {"tables": tables}


# Root folder containing all API subdirectories
root_dir = os.path.join(os.getcwd(), "system_documentation")
print(f"Searching for API files under: {root_dir}")

combined_tables = []  # Aggregate result of all tables across subfolders

# Iterate through all subdirectories
for subfolder in os.listdir(root_dir):
    subfolder_path = os.path.join(root_dir, subfolder)
    if not os.path.isdir(subfolder_path):
        continue  # Skip files

    print(f"Searching in subfolder: {subfolder_path}")

    for file in os.listdir(subfolder_path):
        if file.startswith("API_") and file.endswith(".json"):
            api_path = os.path.join(subfolder_path, file)
            print(f"Processing API file: {api_path}")

            with open(api_path, "r") as f:
                openapi_spec = json.load(f)

            db_structure = extract_tables_from_openapi(openapi_spec)

            # Save individual subfolder result
            output_file = os.path.join(subfolder_path, f"DB_{subfolder}.json")
            with open(output_file, "w") as f:
                json.dump(db_structure, f, indent=4)
            print(f"Saved extracted structure to: {output_file}")

            combined_tables.extend(db_structure["tables"])

# Save combined result to root directory
combined_output_path = os.path.join(root_dir, "combined_db.json")
with open(combined_output_path, "w") as f:
    json.dump({"tables": combined_tables}, f, indent=4)
print(f"Saved combined structure to: {combined_output_path}")
