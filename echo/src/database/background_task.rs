use std::time::Duration;

use rocket::{
    fairing::{self, Fairing, Info, Kind},
    Build, Rocket,
};
use rocket_db_pools::{
    sqlx::{self},
    Database,
};
use tokio::time;

use super::PgDatabase;

pub struct BackgroundTask;

#[rocket::async_trait]
impl Fairing for BackgroundTask {
    fn info(&self) -> Info {
        Info {
            name: "Database Cleanup Task",
            kind: Kind::Ignite,
        }
    }

    async fn on_ignite(&self, rocket: Rocket<Build>) -> fairing::Result {
        let mut interval = time::interval(Duration::from_secs(3600));
        let db = PgDatabase::fetch(&rocket).expect("database").0.clone();

        tokio::spawn(async move {
            loop {
                match db.acquire().await {
                    Ok(mut conn) => {
                        let result = sqlx::query(
                            "
                            DELETE FROM pastes
                            WHERE views >= max_views OR expires_at <= NOW()
                            ",
                        )
                        .execute(&mut *conn)
                        .await;

                        if let Err(error) = result {
                            eprintln!("Failed to delete expired pastes! {}", error);
                        }
                    }
                    Err(error) => {
                        eprint!("Failed to acquire database connection! {}", error);
                    }
                }

                interval.tick().await;
            }
        });

        Ok(rocket)
    }
}
