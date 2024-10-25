use std::env;

use config::Config;
use cors::CorsHeaders;
use database::{background_task::BackgroundTask, PgDatabase};
use figment::providers::{Format, Json};
use rocket::{catchers, fairing::AdHoc, figment, routes};
use rocket_db_pools::Database;
use routes::{health, pastes, security};

pub mod config;
pub mod cors;
pub mod database;
pub mod models;
pub mod result;
pub mod routes;
pub mod utils;

#[rocket::launch]
fn rocket() -> _ {
    let routes = routes![
        cors::snatcher,
        health::health,
        pastes::get_paste,
        pastes::create_paste_simple,
        pastes::create_paste_structured,
        security::get_security,
        security::delete_security,
    ];

    let version = env!("CARGO_PKG_VERSION");
    let user_agent = format!("Echo/{} (+https://mystb.in)", version);

    let client = reqwest::Client::builder()
        .https_only(true)
        .user_agent(user_agent)
        .build()
        .unwrap();

    let path = env::var("ECHO_CONFIG").expect("ECHO_CONFIG not set");
    let provider = rocket::Config::figment().merge(Json::file(path));

    rocket::custom(provider)
        .manage(client)
        .mount("/", routes)
        .attach(PgDatabase::init())
        .attach(CorsHeaders)
        .attach(BackgroundTask)
        .attach(AdHoc::config::<Config>())
        .register("/", catchers![rocket_validation::validation_catcher])
}
