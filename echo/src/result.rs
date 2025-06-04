use std::result;

use rocket::{http::Status, serde::json::Json, Responder};
use serde::Serialize;

#[derive(Serialize)]
pub struct Error<E> {
    message: E,
}

#[derive(Responder)]
pub struct HTTPError<E> {
    inner: (Status, Json<Error<E>>),
}

impl<E> HTTPError<E> {
    pub fn new(code: u16, message: E) -> HTTPError<E> {
        let status = Status::from_code(code).expect("http status");

        HTTPError {
            inner: (status, Json(Error { message })),
        }
    }
}

pub type Result<T, E = &'static str> = result::Result<T, HTTPError<E>>;
