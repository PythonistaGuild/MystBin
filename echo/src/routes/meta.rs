use rocket::{
    get,
    response::{
        content::{RawHtml, RawJson},
        Redirect,
    },
    serde::json::Json,
    uri,
};
use rocket_db_pools::{
    sqlx::{self, Row},
    Connection,
};
use scalar_doc::{Documentation, Theme};

use crate::{
    database::PgDatabase,
    result::{HTTPError, Result},
};

#[get("/")]
pub fn get_root() -> Redirect {
    Redirect::temporary(uri!("/docs"))
}

#[get("/docs")]
pub fn get_docs() -> RawHtml<String> {
    let docs = Documentation::new("MystBin API Documentation", "/docs/spec.json")
        .theme(Theme::Alternate)
        .build()
        .unwrap();

    RawHtml(docs)
}

#[get("/docs/spec.json")]
pub fn get_spec() -> RawJson<&'static str> {
    RawJson(include_str!("../../openapi.json"))
}

#[get("/health")]
pub async fn get_health(mut db: Connection<PgDatabase>) -> Result<String> {
    let result = sqlx::query("SELECT 'ok'").fetch_one(&mut **db).await;

    match result {
        Ok(row) => Ok(row.get(0)),
        Err(_) => Err(HTTPError::new(503, "Database connection unhealthy.")),
    }
}
