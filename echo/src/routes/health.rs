use rocket::get;
use rocket_db_pools::{
    sqlx::{self, Row},
    Connection,
};

use crate::{
    database::PgDatabase,
    result::{HTTPError, Result},
};

#[get("/health")]
pub async fn health(mut db: Connection<PgDatabase>) -> Result<String> {
    let result = sqlx::query("SELECT 'ok'").fetch_one(&mut **db).await;

    match result {
        Ok(row) => Ok(row.get(0)),
        Err(_) => Err(HTTPError::new(503, "Database connection unhealthy.")),
    }
}
