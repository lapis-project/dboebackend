from django.db import connection


def log_query_count(full_log=False):
    # Log query information
    queries = connection.queries
    print(f"\n{'=' * 80}")
    print(f"Total queries executed: {len(queries)}")
    print(f"{'=' * 80}")

    # Group queries by type
    query_types = {}
    for i, query in enumerate(queries, 1):
        sql = query["sql"]
        time = query["time"]

        # Extract table name
        if "FROM" in sql:
            table = sql.split("FROM")[1].split()[0].strip('"')
        elif "UPDATE" in sql:
            table = sql.split("UPDATE")[1].split()[0].strip('"')
        else:
            table = "unknown"

        query_types[table] = query_types.get(table, 0) + 1

        if full_log:
            if i <= 5 or i > len(queries) - 5:
                print(f"\nQuery {i} ({time}s) - Table: {table}")
                print(f"{sql[:200]}..." if len(sql) > 200 else sql)
                print(f"\n{'=' * 80}")
    print("Queries by table:")
    for table, count in sorted(query_types.items(), key=lambda x: x[1], reverse=True):
        print(f"  {table}: {count}")
    print(f"{'=' * 80}\n")
