use rocket::{delete, get, serde::json::Json};
use rocket_db_pools::Connection;

use crate::{database::PgDatabase, models::security::SparsePasteInfo, result::Result};

#[get("/security/<token>")]
pub async fn get_security(
    conn: Connection<PgDatabase>,
    token: &str,
) -> Result<Json<SparsePasteInfo>> {
    Ok(Json(SparsePasteInfo::get(conn, token).await?))
}

#[delete("/security/<token>")]
pub async fn delete_security(
    conn: Connection<PgDatabase>,
    token: &str,
) -> Result<Json<SparsePasteInfo>> {
    Ok(Json(SparsePasteInfo::delete(conn, token).await?))
}
