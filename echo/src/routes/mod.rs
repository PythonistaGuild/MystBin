use rocket::{get, response::Redirect, uri};

pub mod docs;
pub mod health;
pub mod pastes;
pub mod security;

#[get("/")]
pub fn get_root() -> Redirect {
    Redirect::temporary(uri!("/docs"))
}
