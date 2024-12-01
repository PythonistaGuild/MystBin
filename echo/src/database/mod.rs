use rocket_db_pools::{sqlx, Database};

pub mod background_task;
pub mod pastes;
pub mod security;

#[derive(Database)]
#[database("postgres")]
pub struct PgDatabase(sqlx::PgPool);
