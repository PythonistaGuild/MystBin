use crate::{
    database::PgDatabase,
    models::pastes::{CreatePaste, Paste},
    result::Result,
    utils::PasswordHeader,
};
use rocket::{get, post, serde::json::Json};
use rocket_db_pools::Connection;
use rocket_validation::Validated;

#[get("/pastes/<id>")]
pub async fn get_paste<'r>(
    mut conn: Connection<PgDatabase>,
    id: String,
    password: Option<PasswordHeader<'r>>,
) -> Result<Json<Paste>> {
    let password = match password {
        Some(value) => Some(value.get()),
        None => None,
    };

    Ok(Json(Paste::fetch(&mut conn, id, password).await?))
}

#[post("/pastes", data = "<data>", rank = 2)]
pub async fn create_paste_simple<'r>(
    mut conn: Connection<PgDatabase>,
    data: String,
) -> Result<Json<Paste>> {
    let paste = CreatePaste::from_content(data)?;
    Ok(Json(Paste::create(&mut conn, paste).await?))
}

#[post("/pastes", format = "application/json", data = "<data>")]
pub async fn create_paste_structured<'r>(
    mut conn: Connection<PgDatabase>,
    data: Validated<Json<CreatePaste<'r>>>,
) -> Result<Json<Paste>> {
    Ok(Json(Paste::create(&mut conn, data.0 .0).await?))
}
