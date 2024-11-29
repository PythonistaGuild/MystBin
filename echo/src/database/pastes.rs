use crate::{
    models::pastes::{Annotation, CreateFile, CreatePaste, File, Paste},
    result::{HTTPError, Result},
    scanners::scan_file,
    utils::generate_id,
};
use rocket_db_pools::{
    sqlx::{self, Row},
    Connection,
};
use sqlx::{postgres::PgRow, Acquire, Postgres, Transaction};

use super::PgDatabase;

impl Paste {
    pub async fn fetch<'r>(
        conn: &mut Connection<PgDatabase>,
        id: String,
        password: Option<&'r str>,
    ) -> Result<Paste> {
        let query = format!(
            "
            WITH _ AS (
                UPDATE
                    pastes
                SET
                    views = views + 1
                WHERE
                    id = $1 AND {}
            )
            SELECT
                created_at,
                expires_at,
                views + 1 AS views, -- account for in-progress update above
                max_views,
                CASE WHEN password IS NULL THEN true ELSE
                    CASE WHEN $2 IS NULL THEN false ELSE password = CRYPT($2, password) END
                END AS authenticated
            FROM
                pastes
            WHERE
                id = $1 AND
                CASE WHEN max_views IS NULL THEN true ELSE views <= max_views END AND
                CASE WHEN expires_at IS NULL THEN true ELSE expires_at > CURRENT_TIMESTAMP END
            ",
            match password {
                None => "password IS NULL",
                Some(_) => "password = CRYPT($2, password)",
            },
        );

        let result = sqlx::query(&query)
            .bind(&id)
            .bind(password)
            .fetch_one(&mut ***conn)
            .await;

        match result {
            Ok(row) => {
                let authenticated = row.get("authenticated");

                if authenticated {
                    let files = File::fetch(conn, &id).await?;
                    Ok(Paste::from_row(row, id, files, None))
                } else {
                    Err(HTTPError::new(401, "Provided password is not valid."))
                }
            }
            Err(_) => {
                return Err(HTTPError::new(
                    404,
                    "Requested paste does not exist, has too many views, or has expired.",
                ))
            }
        }
    }

    pub async fn create<'r>(
        conn: &mut Connection<PgDatabase>,
        data: CreatePaste<'r>,
    ) -> Result<Paste> {
        let mut tx = match (&mut **conn).begin().await {
            Ok(tx) => tx,
            Err(_) => return Err(HTTPError::new(500, "Failed to create paste.")),
        };

        let mut paste = loop {
            let id = generate_id(20);
            let safety = generate_id(64);

            let result = sqlx::query(
                "
                INSERT INTO pastes (id, expires_at, max_views, password, safety)
                VALUES ($1, $2, $3, (SELECT CRYPT($4, gen_salt('bf')) WHERE $4 IS NOT NULL), $5)
                RETURNING created_at, expires_at, views, max_views
                ",
            )
            .bind(&id)
            .bind(data.expires_at())
            .bind(data.max_views())
            .bind(data.password())
            .bind(&safety)
            .fetch_one(&mut *tx)
            .await;

            match result {
                Ok(row) => {
                    let files = Vec::with_capacity(data.files().len());
                    break Paste::from_row(row, id, files, Some(safety));
                }
                Err(error) => {
                    let inner = error.as_database_error();

                    // However unlikely it is, the id or safety was a duplicate.
                    if inner.is_some() && inner.unwrap().is_unique_violation() {
                        continue;
                    }

                    return Err(HTTPError::new(500, "Failed to create paste."));
                }
            }
        };

        let invalidate_secrets = data.password().is_none();

        for file in data.files() {
            let file = File::create(&mut tx, paste.id(), file, invalidate_secrets).await?;
            paste.add_file(file);
        }

        match tx.commit().await {
            Ok(_) => Ok(paste),
            Err(_) => Err(HTTPError::new(500, "Failed to create paste.")),
        }
    }

    fn from_row(row: PgRow, id: String, files: Vec<File>, safety: Option<String>) -> Self {
        let created_at = row.get("created_at");
        let expires_at = row.get("expires_at");

        let views = row.get("views");
        let max_views = row.get("max_views");

        Paste::new(id, created_at, expires_at, views, max_views, files, safety)
    }
}

impl File {
    async fn fetch(conn: &mut Connection<PgDatabase>, paste_id: &str) -> Result<Vec<Self>> {
        let result = sqlx::query(
            "
            SELECT id, name, content, language, lines, characters
            FROM files
            WHERE paste_id = $1
            ORDER BY id ASC
            ",
        )
        .bind(paste_id)
        .fetch_all(&mut ***conn)
        .await;

        let rows = match result {
            Ok(rows) => rows,
            Err(_) => return Err(HTTPError::new(500, "Unable to fetch paste files.")),
        };

        let mut files = Vec::with_capacity(rows.len());

        for row in rows {
            let id = row.get("id");
            let annotations = Annotation::fetch(conn, &id).await?;

            files.push(File::from_row(row, annotations));
        }

        Ok(files)
    }

    async fn create<'r>(
        tx: &mut Transaction<'_, Postgres>,
        paste_id: &str,
        file: &'r CreateFile<'r>,
        invalidate_secrets: bool,
    ) -> Result<Self> {
        let result = sqlx::query(
            "
            INSERT INTO files (paste_id, name, content, language)
            VALUES ($1, $2, $3, $4)
            RETURNING id, name, content, language, lines, characters
            ",
        )
        .bind(paste_id)
        .bind(file.name().or(Some("unknown")))
        .bind(file.content())
        .bind(file.language())
        .fetch_one(&mut **tx)
        .await;

        match result {
            Ok(row) => {
                let id: i64 = row.get("id");
                let annotations =
                    Annotation::create(tx, id, file.content(), invalidate_secrets).await?;

                return Ok(File::from_row(row, annotations));
            }
            Err(_) => return Err(HTTPError::new(500, "Failed to create paste.")),
        }
    }

    fn from_row(row: PgRow, annotations: Vec<Annotation>) -> Self {
        let name = row.get("name");
        let content = row.get("content");
        let language = row.get("language");

        let lines = row.get("lines");
        let characters = row.get("characters");

        File::new(name, content, language, lines, characters, annotations)
    }
}

impl Annotation {
    async fn fetch(conn: &mut Connection<PgDatabase>, file_id: &i64) -> Result<Vec<Self>> {
        let result = sqlx::query_as::<_, Annotation>(
            "
            SELECT head_line, head_char, head_char, tail_line, tail_char, content
            FROM annotations
            WHERE file_id = $1
            ORDER BY id ASC
            ",
        )
        .bind(file_id)
        .fetch_all(&mut ***conn)
        .await;

        match result {
            Ok(annotations) => Ok(annotations),
            Err(_) => return Err(HTTPError::new(500, "Unable to fetch file annotations.")),
        }
    }

    async fn create(
        tx: &mut Transaction<'_, Postgres>,
        file_id: i64,
        content: &str,
        invalidate_secrets: bool,
    ) -> Result<Vec<Self>> {
        let scans = scan_file(content, invalidate_secrets).await;
        let mut annotations = Vec::with_capacity(scans.len());

        for scan in scans {
            let mut content = format!("Mystb.in found a secret for {}.", scan.service);

            if invalidate_secrets {
                content += " This secret has been invalidated.";
            }

            let result = sqlx::query(
                "
                INSERT INTO annotations (file_id, head_line, head_char, tail_line, tail_char, content)
                VALUES ($1, $2, $3, $4, $5, $6)
                ",
            )
            .bind(file_id)
            .bind(scan.head.line())
            .bind(scan.head.char())
            .bind(scan.tail.line())
            .bind(scan.tail.char())
            .bind(&content)
            .execute(&mut **tx)
            .await;

            match result {
                Ok(_) => annotations.push(Annotation::new(scan.head, scan.tail, content)),
                Err(_) => return Err(HTTPError::new(500, "Failed to create paste.")),
            };
        }

        Ok(annotations)
    }
}
