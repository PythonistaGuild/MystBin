use crate::{
    models::pastes::{Annotation, CreatePaste, File, Paste},
    result::{HTTPError, Result},
    utils::generate_id,
};
use rocket_db_pools::{
    sqlx::{self, Row},
    Connection,
};
use sqlx::{postgres::PgRow, Acquire};

use super::PgDatabase;

impl Paste {
    pub async fn fetch<'r>(
        conn: &mut Connection<PgDatabase>,
        id: String,
        password: Option<&'r str>,
    ) -> Result<Paste> {
        let query = format!(
            "
            UPDATE
                pastes
            SET
                views = views + 1
            WHERE
                id = $1 AND
                CASE WHEN max_views IS NULL THEN true ELSE views <= max_views END AND
                CASE WHEN expires_at IS NULL THEN true ELSE expires_at > CURRENT_TIMESTAMP END AND
                {}
            RETURNING
                created_at, expires_at, views, max_views
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
                let files = File::fetch(conn, &id).await?;
                Ok(Paste::from_row(row, id, files, None))
            }
            Err(_) => return Err(HTTPError::new(404, "Unknown paste or invalid password.")),
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

        for file in data.files() {
            let result = sqlx::query(
                "
                INSERT INTO files (paste_id, name, content)
                VALUES ($1, $2, $3)
                RETURNING id, name, content, lines, characters
                ",
            )
            .bind(paste.id())
            .bind(file.name().or(Some("unknown")))
            .bind(file.content())
            .fetch_one(&mut *tx)
            .await;

            match result {
                Ok(row) => {
                    let _id: i64 = row.get("id");
                    let annotations = Vec::new(); // TODO: Create and insert annotations

                    paste.add_file(File::from_row(row, annotations));
                }
                Err(_) => return Err(HTTPError::new(500, "Failed to create paste.")),
            }
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
            SELECT id, name, content, lines, characters
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

    fn from_row(row: PgRow, annotations: Vec<Annotation>) -> Self {
        let name = row.get("name");
        let content = row.get("content");

        let lines = row.get("lines");
        let characters = row.get("characters");

        File::new(name, content, lines, characters, annotations)
    }
}

impl Annotation {
    async fn fetch(conn: &mut Connection<PgDatabase>, file_id: &i64) -> Result<Vec<Self>> {
        let result = sqlx::query_as::<_, Annotation>(
            "
            SELECT head, tail, content
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
}
