use once_cell::sync::Lazy;
use rand::{distributions::Alphanumeric, Rng};

use regex::Regex;
use rocket::{
    http::Status,
    request::{FromRequest, Outcome, Request},
};

pub fn generate_id(size: usize) -> String {
    let random = rand::thread_rng();
    String::from_utf8(random.sample_iter(Alphanumeric).take(size).collect()).expect("id generator")
}

pub struct PasswordHeader<'r> {
    value: &'r str,
}

impl<'r> PasswordHeader<'r> {
    pub fn get(self) -> &'r str {
        self.value
    }
}

#[rocket::async_trait]
impl<'r> FromRequest<'r> for PasswordHeader<'r> {
    type Error = &'static str;

    async fn from_request(request: &'r Request<'_>) -> Outcome<Self, Self::Error> {
        let result = request.headers().get_one("Authorization");

        let value = match result {
            Some(value) => value,
            None => return Outcome::Error((Status::Unauthorized, "Missing Authorization header.")),
        };

        static PATTERN: Lazy<Regex> = Lazy::new(|| Regex::new(r"(?i:password): .+").unwrap());

        if !PATTERN.is_match(value) {
            return Outcome::Error((Status::Unauthorized, "Invalid Authorization header."));
        }

        Outcome::Success(PasswordHeader {
            value: value.split_once(" ").unwrap().1,
        })
    }
}
