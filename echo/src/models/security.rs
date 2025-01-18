use serde::Serialize;
use sqlx::prelude::FromRow;

#[derive(FromRow, Serialize)]
pub struct SparsePasteInfo {
    id: String,
}
