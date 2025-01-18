use rocket_db_pools::{
    sqlx::{self},
    Connection,
};

use crate::{
    models::security::SparsePasteInfo,
    result::{HTTPError, Result},
};

use super::PgDatabase;

impl SparsePasteInfo {
    pub async fn get(mut conn: Connection<PgDatabase>, token: &str) -> Result<Self> {
        let result =
            sqlx::query_as::<_, SparsePasteInfo>("SELECT id FROM pastes WHERE safety = $1")
                .bind(token)
                .fetch_one(&mut **conn)
                .await;

        match result {
            Ok(result) => Ok(result),
            Err(_) => Err(HTTPError::new(404, "Invalid safety token provided.")),
        }
    }

    pub async fn delete(mut conn: Connection<PgDatabase>, token: &str) -> Result<Self> {
        let result = sqlx::query_as::<_, SparsePasteInfo>(
            "DELETE FROM pastes WHERE safety = $1 RETURNING id",
        )
        .bind(token)
        .fetch_one(&mut **conn)
        .await;

        match result {
            Ok(result) => Ok(result),
            Err(_) => Err(HTTPError::new(404, "Invalid safety token provided.")),
        }
    }
}
