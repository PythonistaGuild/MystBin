import os
import asyncpg
import asyncio

postgres_user = os.getenv("pg_user")
postgres_auth = os.getenv("pg_auth")

async def main():
    old: asyncpg.Connection = await asyncpg.connect(f"postgres://{postgres_user}:{postgres_auth}@127.0.0.1:5432/mystbin_old") # type: ignore
    new: asyncpg.Connection = await asyncpg.connect(f"postgres://{postgres_user}:{postgres_auth}@127.0.0.1:5432/mystbin_prod") # type: ignore

    current_idx = 0
    while True:
        print(f"Exporting @ index {current_idx}")
        async with old.transaction():
            async with new.transaction():
                bundle = await old.fetch("SELECT * FROM pastes ORDER BY id LIMIT 200 OFFSET $1", current_idx)
                if not bundle:
                    print("Export complete")
                    break

                print("fetched, inserting")
                    
                #await old.execute(f"DELETE FROM pastes WHERE {' OR '.join([f'id = ${x}' for x in range(1, 201)])}", *[x['id'] for x in bundle])

                await new.executemany("INSERT INTO pastes (id, views, origin_ip) VALUES ($1, $2, '0.0.0.0')", [(x['paste_id'], x['views']) for x in bundle])
                print("inserted pastes, inserting files")
                await new.executemany(
                    "INSERT INTO files (parent_id, content, filename, loc) VALUES ($1, $2, 'migrated.txt', $3)",
                    [(x['id'], x['data'], x["data"].count("\n")) for x in bundle]
                )
                print("imported files")
                current_idx += 200


asyncio.run(main())