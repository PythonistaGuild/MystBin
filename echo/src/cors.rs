use rocket::{
    fairing::{Fairing, Info, Kind},
    http::Header,
    options, Request, Response,
};

use crate::config::Config;

// Ensure the server responds to all preflight requests
#[options("/<_..>")]
pub fn snatcher() {}

pub struct CorsHeaders;

#[rocket::async_trait]
impl Fairing for CorsHeaders {
    fn info(&self) -> Info {
        Info {
            name: "CORS Headers",
            kind: Kind::Response,
        }
    }

    async fn on_response<'r>(&self, request: &'r Request<'_>, response: &mut Response<'r>) {
        let origin = match request.headers().get_one("Origin") {
            Some(value) => value,
            None => return,
        };

        let config = request.rocket().state::<Config>().unwrap();

        if !config.allowed_hosts.iter().any(|x| x == origin) {
            return;
        }

        response.set_header(Header::new("Access-Control-Allow-Origin", origin));

        response.set_header(Header::new(
            "Access-Control-Allow-Methods",
            "DELETE, GET, PATCH, POST, PUT, QUERY",
        ));
        response.set_header(Header::new("Access-Control-Max-Age", "86400"));
        response.set_header(Header::new("Access-Control-Allow-Credentials", "true"));
    }
}
