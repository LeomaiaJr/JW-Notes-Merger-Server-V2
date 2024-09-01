import sqlite3
import os
import shutil
import zipfile


def get_next_id(cursor, table_name, id_column):
    cursor.execute(f"SELECT MAX({id_column}) FROM {table_name}")
    max_id = cursor.fetchone()[0]
    return max_id + 1 if max_id is not None else 1


def get_unique_constraints(cursor, table_name):
    cursor.execute(f"PRAGMA index_list('{table_name}')")
    indices = cursor.fetchall()
    unique_constraints = []
    for idx in indices:
        if idx[2] == 1:  # This index is a unique constraint
            cursor.execute(f"PRAGMA index_info('{idx[1]}')")
            columns = [info[2] for info in cursor.fetchall()]
            unique_constraints.append(columns)
    return unique_constraints


def find_existing_row(cursor, table_name, unique_constraint, row_data, columns):
    where_clause = " AND ".join([f"{col} = ?" for col in unique_constraint])
    query = f"SELECT * FROM {table_name} WHERE {where_clause}"
    values = [row_data[columns.index(col)] for col in unique_constraint]
    cursor.execute(query, values)
    return cursor.fetchone()


def merge_simple_table(
    source_cursor, target_cursor, table_name, id_column, id_mappings
):
    # Get column names
    source_cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [column[1] for column in source_cursor.fetchall()]

    # Create insert query template
    insert_columns = ",".join(columns)
    placeholders = ",".join(["?" for _ in columns])
    insert_query = (
        f"INSERT INTO {table_name} ({insert_columns}) VALUES ({placeholders})"
    )

    # Get the starting ID for new entries
    next_id = get_next_id(target_cursor, table_name, id_column)
    current_id = next_id

    # Fetch all rows from the source table
    source_cursor.execute(f"SELECT * FROM {table_name}")
    rows = source_cursor.fetchall()

    for row in rows:
        # Create a new row with the updated ID
        new_row = list(row)
        new_row[0] = current_id

        try:
            target_cursor.execute(insert_query, new_row)

            id_mappings[table_name][row[0]] = current_id

            current_id += 1

        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                error_cleaned = e.args[0].replace("UNIQUE constraint failed: ", "")
                error_cleaned = error_cleaned.replace(f"{table_name}.", "")
                unique_constraints = error_cleaned.split(", ")

                existing_row = find_existing_row(
                    target_cursor, table_name, unique_constraints, new_row, columns
                )
                if existing_row:
                    id_mappings[table_name][row[0]] = existing_row[0]
                else:
                    print(f"Could not find existing row for {table_name}")

            else:
                raise

    return current_id - next_id


def merge_input_field(source_cursor, target_cursor, id_mappings):
    source_cursor.execute("SELECT * FROM InputField")
    rows = source_cursor.fetchall()

    # Prepare the insert query
    insert_query = """
  INSERT INTO InputField (LocationId, TextTag, Value)
  VALUES (?, ?, ?)
  """

    # Counter for successful inserts
    inserted_count = 0

    for row in rows:
        old_location_id, text_tag, value = row

        # Get the new LocationId from id_mappings
        new_location_id = id_mappings["Location"].get(old_location_id)

        if new_location_id is None:
            print(
                f"Warning: No mapping found for LocationId {old_location_id} in InputField"
            )
            continue

        try:
            target_cursor.execute(insert_query, (new_location_id, text_tag, value))
            inserted_count += 1

        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                continue
            else:
                raise

    return inserted_count


def merge_complex_table_group_one(
    source_cursor, target_cursor, table_name, id_column, id_mappings, dependencies
):
    source_cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [column[1] for column in source_cursor.fetchall()]

    # Create insert query template
    insert_columns = ",".join(columns)
    placeholders = ",".join(["?" for _ in columns])
    insert_query = (
        f"INSERT INTO {table_name} ({insert_columns}) VALUES ({placeholders})"
    )

    # Get the starting ID for new entries
    next_id = get_next_id(target_cursor, table_name, id_column)
    current_id = next_id

    # Get unique constraints
    unique_constraints = get_unique_constraints(target_cursor, table_name)

    # Fetch all rows from the source table
    source_cursor.execute(f"SELECT * FROM {table_name}")
    rows = source_cursor.fetchall()

    operations = 0

    for row in rows:
        # Create a new row with the updated ID and mapped foreign keys
        new_row = list(row)
        new_row[0] = current_id

        # Update foreign keys based on dependencies
        for dep_column, dep_table in dependencies.items():
            col_index = columns.index(dep_column)
            old_fk = new_row[col_index]
            new_fk = id_mappings[dep_table].get(old_fk)
            if new_fk is not None:
                new_row[col_index] = new_fk
            else:
                print(
                    f"Warning: No mapping found for {dep_column} {old_fk} in {table_name}"
                )
                break
        else:
            try:
                target_cursor.execute(insert_query, new_row)
                id_mappings[table_name][row[0]] = current_id
                current_id += 1
                operations += 1

            except sqlite3.IntegrityError as e:
                if "UNIQUE constraint failed" in str(e):
                    continue
                else:
                    raise

    return operations


def merge_databases(source_db_path, target_db_path):
    source_conn = sqlite3.connect(source_db_path)
    target_conn = sqlite3.connect(target_db_path)

    source_cursor = source_conn.cursor()
    target_cursor = target_conn.cursor()

    op_count = 0

    id_mappings = {
        "IndependentMedia": {},
        "Location": {},
        "Tag": {},
        "PlaylistItem": {},
        "PlaylistItemIndependentMediaMap": {},
        "PlaylistItemLocationMap": {},
        "PlaylistItemMarker": {},
        "PlaylistItemMarkerBibleVerseMap": {},
        "PlaylistItemMarkerParagraphMap": {},
        "UserMark": {},
        "Bookmark": {},
        "BlockRange": {},
        "Note": {},
        "TagMap": {},
    }

    simple_tables = [
        ("IndependentMedia", "IndependentMediaId"),
        ("Location", "LocationId"),
        ("Tag", "TagId"),
    ]

    complex_tables_group_one = [
        {
            "name": "Bookmark",
            "id_column": "BookmarkId",
            "dependencies": {
                "LocationId": "Location",
                "PublicationLocationId": "Location",
            },
        },
        {
            "name": "PlaylistItem",
            "id_column": "PlaylistItemId",
            "dependencies": {
                "Accuracy": "PlaylistItemAccuracy",
                "ThumbnailFilePath": "IndependentMedia",
            },
        },
        {
            "name": "UserMark",
            "id_column": "UserMarkId",
            "dependencies": {"LocationId": "Location"},
        },
    ]

    for table, id_column in simple_tables:
        print(f"Simple Merging table: {table}")
        op_count += merge_simple_table(
            source_cursor, target_cursor, table, id_column, id_mappings
        )

    print("Merging table: InputField")
    op_count += merge_input_field(source_cursor, target_cursor, id_mappings)

    for table in complex_tables_group_one:
        print(f"Merging table: {table['name']}")
        operations = merge_complex_table_group_one(
            source_cursor,
            target_cursor,
            table["name"],
            table["id_column"],
            id_mappings,
            table["dependencies"],
        )
        op_count += operations

    print(id_mappings)

    # Commit changes and close connections
    target_conn.commit()
    source_conn.close()
    target_conn.close()

    print("Database merge completed successfully.")


def get_file_size(file_path):
    return os.path.getsize(file_path)


def move_files(source_folder, target_folder, exclude_files):
    for item in os.listdir(source_folder):
        if item not in exclude_files:
            source_path = os.path.join(source_folder, item)
            target_path = os.path.join(target_folder, item)
            shutil.move(source_path, target_path)
            print(f"Moved: {item}")


def zip_folder(folder_path, output_filename):
    with zipfile.ZipFile(output_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname)
    print(f"Created zip file: {output_filename}")


if __name__ == "__main__":
    db_path1 = "../assets/backup1/userData.db"
    db_path2 = "../assets/backup2/userData.db"

    if not os.path.exists(db_path1) or not os.path.exists(db_path2):
        print("Error: One or both database files do not exist.")
    else:
        # Determine the larger database and assign it as the target
        size1 = get_file_size(db_path1)
        size2 = get_file_size(db_path2)

        if size1 >= size2:
            source_db_path = db_path2
            target_db_path = db_path1
            source_folder = os.path.dirname(db_path2)
            target_folder = os.path.dirname(db_path1)
        else:
            source_db_path = db_path1
            target_db_path = db_path2
            source_folder = os.path.dirname(db_path1)
            target_folder = os.path.dirname(db_path2)

        print(f"Source DB: {source_db_path}")
        print(f"Target DB: {target_db_path}")

        # Merge databases
        merge_databases(source_db_path, target_db_path)
        print("Database merge completed successfully.")

        # Move files from source to target folder
        exclude_files = ["manifest.json", "userData.db", "default_thumbnail.png"]
        move_files(source_folder, target_folder, exclude_files)

        # Create zip file of the target folder
        parent_folder = os.path.dirname(target_folder)
        zip_filename = os.path.join(parent_folder, "merged.jwlibrary")
        # zip_folder(target_folder, zip_filename)

        print("All operations completed successfully.")
