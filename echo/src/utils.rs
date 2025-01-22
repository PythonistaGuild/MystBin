use rand::{distributions::Alphanumeric, Rng};

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

        let (prefix, suffix) = match value.split_once(" ") {
            Some(values) => values,
            None => return Outcome::Error((Status::Unauthorized, "Invalid Authorization header.")),
        };

        if prefix.to_lowercase() == "password" {
            Outcome::Success(PasswordHeader { value: suffix })
        } else {
            Outcome::Error((Status::Unauthorized, "Invalid Authorization header."))
        }
    }
}
